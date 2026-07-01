#!/usr/bin/env python3
"""
Image Compression Script - Target File Size or Percentage with Minimal Quality Loss
====================================================================================

Batch compresses images to a target size (KB) or by a percentage of original size.
Always saves best-effort result even if target cannot be fully met.

Usage:
    python compress_images.py <folder> [--target-kb KB] [--percentage PCT]

Examples:
    python compress_images.py ./photos --target-kb 200
    python compress_images.py ./photos --percentage 50
    python compress_images.py ./photos --percentage 75
"""

import os
import sys
import argparse
from pathlib import Path
from io import BytesIO
from typing import Tuple, Optional
from PIL import Image
import traceback


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_TARGET_KB = 200
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
MIN_QUALITY = 10
MAX_QUALITY = 95
SIZE_TOLERANCE_BYTES = 1024


# ============================================================================
# CORE COMPRESSION LOGIC
# ============================================================================

def get_image_size_bytes(img: Image.Image, format_type: str, quality: int, optimize: bool = True) -> Tuple[bytes, int]:
    buffer = BytesIO()

    if format_type == 'JPEG':
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(buffer, format='JPEG', quality=quality, optimize=optimize)

    elif format_type == 'PNG':
        img.save(buffer, format='PNG', optimize=optimize, compress_level=9)

    elif format_type == 'WebP':
        img.save(buffer, format='WebP', quality=quality, method=6)

    buffer.seek(0)
    data = buffer.getvalue()
    return data, len(data)


def find_optimal_quality(img: Image.Image, target_bytes: int, format_type: str) -> Tuple[bytes, int, int]:
    """
    Binary search for highest quality that fits target_bytes.
    Always returns a result — falls back to MIN_QUALITY if target unreachable.
    """

    if format_type == 'PNG':
        data, size = get_image_size_bytes(img, 'PNG', quality=95, optimize=True)
        if size <= target_bytes:
            return data, 95, size

        if img.mode in ('RGBA', 'RGB'):
            try:
                quantized = img.quantize(colors=256, method=2)
                data, size = get_image_size_bytes(quantized, 'PNG', quality=95, optimize=True)
                if size <= target_bytes:
                    return data, 95, size
            except Exception:
                pass

        # Fall through to WebP binary search
        format_type = 'WebP'

    low = MIN_QUALITY
    high = MAX_QUALITY
    best_data = None
    best_quality = MIN_QUALITY
    best_size = 0

    # Always compute MIN_QUALITY result as fallback
    fallback_data, fallback_size = get_image_size_bytes(img, format_type, MIN_QUALITY, optimize=True)

    while low <= high:
        mid = (low + high) // 2
        try:
            data, size = get_image_size_bytes(img, format_type, quality=mid, optimize=True)

            if size <= target_bytes:
                best_data = data
                best_quality = mid
                best_size = size
                low = mid + 1
                if target_bytes - size <= SIZE_TOLERANCE_BYTES:
                    break
            else:
                high = mid - 1

        except Exception as e:
            print(f"    Warning: Error at quality {mid}: {e}")
            high = mid - 1

    # Return best found, or fallback to MIN_QUALITY (best effort)
    if best_data is not None:
        return best_data, best_quality, best_size
    return fallback_data, MIN_QUALITY, fallback_size


def compress_image(input_path: Path, output_path: Path, target_bytes: int) -> Tuple[bool, bool, int, int, str]:
    """
    Compress single image. Always saves output — best effort if target unreachable.

    Returns:
        (success, hit_target, original_size, compressed_size, message)
    """
    try:
        img = Image.open(input_path)
        original_size = input_path.stat().st_size

        if original_size <= target_bytes:
            img.save(output_path, optimize=True)
            return True, True, original_size, output_path.stat().st_size, "Already under target"

        original_format = img.format
        if original_format in ('JPEG', 'JPG'):
            format_type = 'JPEG'
        elif original_format == 'PNG':
            format_type = 'PNG'
        elif original_format == 'WEBP':
            format_type = 'WebP'
        else:
            format_type = 'JPEG'

        compressed_data, final_quality, final_size = find_optimal_quality(img, target_bytes, format_type)

        with open(output_path, 'wb') as f:
            f.write(compressed_data)

        hit_target = final_size <= target_bytes
        reduction_pct = ((original_size - final_size) / original_size) * 100
        message = f"Quality: {final_quality}, Reduction: {reduction_pct:.1f}%"

        return True, hit_target, original_size, final_size, message

    except Exception as e:
        return False, False, 0, 0, f"Error: {str(e)}"


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def process_folder(input_dir: str, target_kb: Optional[int], percentage: Optional[float]):
    """
    Process all images. Supports fixed target KB or per-image percentage reduction.

    Args:
        target_kb: Fixed target size in KB (all images same target)
        percentage: Compress TO this % of original size (e.g. 50 = half the original)
    """
    input_path = Path(input_dir).resolve()

    if not input_path.exists():
        print(f"❌ Error: Directory '{input_dir}' does not exist")
        return

    if not input_path.is_dir():
        print(f"❌ Error: '{input_dir}' is not a directory")
        return

    output_path = input_path / "compressed"
    output_path.mkdir(exist_ok=True)

    image_files = []
    for ext in SUPPORTED_FORMATS:
        image_files.extend(input_path.glob(f"*{ext}"))
        image_files.extend(input_path.glob(f"*{ext.upper()}"))

    image_files = sorted(set(image_files))

    if not image_files:
        print(f"⚠️  No image files found in '{input_dir}'")
        print(f"   Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return

    if percentage is not None:
        mode_desc = f"percentage mode ({percentage:.0f}% of original size per image)"
    else:
        mode_desc = f"fixed target {format_size(target_kb * 1024)} per image"

    print(f"🎯 Mode: {mode_desc}")
    print(f"📁 Input:  {input_path}")
    print(f"📂 Output: {output_path}")
    print(f"🖼️  Found {len(image_files)} image(s) to process")
    print("=" * 80)

    total_original = 0
    total_compressed = 0
    success_count = 0
    best_effort_count = 0
    failed_count = 0

    for idx, img_file in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}] Processing: {img_file.name}")

        output_file = output_path / img_file.name

        # Compute per-image target if percentage mode
        if percentage is not None:
            try:
                original_size = img_file.stat().st_size
                target_bytes = max(1024, int(original_size * percentage / 100))
            except Exception:
                target_bytes = 1024
        else:
            target_bytes = target_kb * 1024

        try:
            success, hit_target, orig_size, comp_size, message = compress_image(
                img_file, output_file, target_bytes
            )

            if success:
                total_original += orig_size
                total_compressed += comp_size

                if hit_target:
                    success_count += 1
                    print(f"    ✅ {format_size(orig_size)} → {format_size(comp_size)}")
                else:
                    best_effort_count += 1
                    target_label = format_size(target_bytes)
                    print(f"    ⚠️  {format_size(orig_size)} → {format_size(comp_size)}  (best effort, target was {target_label})")

                print(f"    {message}")
            else:
                failed_count += 1
                print(f"    ❌ {message}")

        except Exception as e:
            failed_count += 1
            print(f"    ❌ Unexpected error: {e}")
            traceback.print_exc()

    # Summary
    total = len(image_files)
    print("\n" + "=" * 80)
    print("📊 COMPRESSION REPORT")
    print("=" * 80)
    print(f"✅ Hit target:   {success_count}/{total}")
    if best_effort_count:
        print(f"⚠️  Best effort:  {best_effort_count}/{total}  (compressed as much as possible)")
    if failed_count:
        print(f"❌ Failed:       {failed_count}/{total}")

    processed = success_count + best_effort_count
    if processed > 0 and total_original > 0:
        total_reduction = total_original - total_compressed
        reduction_pct = (total_reduction / total_original) * 100

        print(f"\n📈 Total original:    {format_size(total_original)}")
        print(f"📉 Total compressed:  {format_size(total_compressed)}")
        print(f"💾 Total saved:       {format_size(total_reduction)} ({reduction_pct:.1f}%)")

    print(f"\n✨ Output folder: {output_path}")
    print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Bulk image compressor — fixed target size or percentage-based.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compress_images.py ./photos --target-kb 200
  python compress_images.py ./photos --percentage 50
  python compress_images.py ./photos -p 35
  python compress_images.py ./photos -p 75 --target-kb 300  # ERROR: pick one
        """
    )
    parser.add_argument("input_dir", nargs="?", default=".",
                        help="Folder containing images (default: current directory)")
    parser.add_argument("--target-kb", "-t", type=int, default=None,
                        help="Target file size in KB (e.g. 200)")
    parser.add_argument("--percentage", "-p", type=float, default=None,
                        help="Compress TO this %% of original size (e.g. 50 = half size)")

    args = parser.parse_args()

    if args.target_kb is not None and args.percentage is not None:
        parser.error("Use --target-kb OR --percentage, not both.")

    if args.percentage is not None:
        if not (1 <= args.percentage <= 99):
            parser.error("--percentage must be between 1 and 99.")
        target_kb = None
        percentage = args.percentage
    else:
        target_kb = args.target_kb if args.target_kb is not None else DEFAULT_TARGET_KB
        percentage = None

    print("=" * 80)
    print("🖼️  BULK IMAGE COMPRESSOR")
    print("=" * 80)
    print()

    process_folder(args.input_dir, target_kb, percentage)


if __name__ == "__main__":
    main()
