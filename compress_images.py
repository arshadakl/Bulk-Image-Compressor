#!/usr/bin/env python3
"""
Image Compression Script - Target File Size with Minimal Quality Loss
======================================================================

This script compresses images to a specified target file size while maintaining
original dimensions and minimizing visible quality degradation.

Features:
- Batch processes all images in a folder
- Uses binary search to find optimal quality setting
- Preserves original dimensions (no resizing)
- Handles JPEG, PNG, and WebP formats
- Creates 'compressed' subfolder for output
- Provides detailed compression report

Author: Generated for Production Use
Date: January 2026
"""

import os
import sys
from pathlib import Path
from io import BytesIO
from typing import Tuple, Optional
from PIL import Image
import traceback


# ============================================================================
# CONFIGURATION SECTION
# ============================================================================

# Target file size in KB (easily adjustable)
TARGET_SIZE_KB = 200

# Input directory (can be changed to any folder path)
INPUT_DIR = "."  # Current directory by default

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}

# Quality search bounds
MIN_QUALITY = 30
MAX_QUALITY = 95

# Binary search tolerance (in bytes)
SIZE_TOLERANCE_BYTES = 1024  # 1 KB tolerance


# ============================================================================
# CORE COMPRESSION LOGIC
# ============================================================================

def get_image_size_bytes(img: Image.Image, format_type: str, quality: int, optimize: bool = True) -> Tuple[bytes, int]:
    """
    Save image to BytesIO buffer and return the data and size.
    
    Args:
        img: PIL Image object
        format_type: Target format ('JPEG', 'PNG', 'WebP')
        quality: Quality setting (1-100)
        optimize: Enable optimization
        
    Returns:
        Tuple of (image_bytes, size_in_bytes)
    """
    buffer = BytesIO()
    
    # Save with format-specific parameters
    if format_type == 'JPEG':
        # Convert RGBA to RGB for JPEG
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
        img.save(buffer, format='JPEG', quality=quality, optimize=optimize)
        
    elif format_type == 'PNG':
        # PNG optimization
        img.save(buffer, format='PNG', optimize=optimize, compress_level=9)
        
    elif format_type == 'WebP':
        # WebP supports both lossy and lossless
        img.save(buffer, format='WebP', quality=quality, method=6)
    
    buffer.seek(0)
    data = buffer.getvalue()
    return data, len(data)


def find_optimal_quality(img: Image.Image, target_bytes: int, format_type: str) -> Tuple[Optional[bytes], int, int]:
    """
    Use binary search to find the highest quality that meets target file size.
    
    Args:
        img: PIL Image object
        target_bytes: Target file size in bytes
        format_type: Target format ('JPEG', 'PNG', 'WebP')
        
    Returns:
        Tuple of (compressed_image_bytes, final_quality, final_size)
        Returns (None, 0, 0) if target cannot be achieved
    """
    
    # Special handling for PNG (quality doesn't apply the same way)
    if format_type == 'PNG':
        # Try optimized PNG first
        data, size = get_image_size_bytes(img, 'PNG', quality=95, optimize=True)
        
        if size <= target_bytes:
            return data, 95, size
        
        # If PNG is too large, try converting to WebP or palette mode
        # Try palette conversion for PNG with many colors
        if img.mode == 'RGBA' or img.mode == 'RGB':
            try:
                # Try quantizing to reduce colors
                quantized = img.quantize(colors=256, method=2)
                data, size = get_image_size_bytes(quantized, 'PNG', quality=95, optimize=True)
                if size <= target_bytes:
                    return data, 95, size
            except:
                pass
        
        # Last resort: convert to WebP
        data, size = get_image_size_bytes(img, 'WebP', quality=MAX_QUALITY, optimize=True)
        if size <= target_bytes:
            return data, MAX_QUALITY, size
        
        # Fall through to binary search for WebP
        format_type = 'WebP'
    
    # Binary search for optimal quality (JPEG and WebP)
    low = MIN_QUALITY
    high = MAX_QUALITY
    best_data = None
    best_quality = 0
    best_size = 0
    
    while low <= high:
        mid = (low + high) // 2
        
        try:
            data, size = get_image_size_bytes(img, format_type, quality=mid, optimize=True)
            
            # Check if this quality meets our target
            if size <= target_bytes:
                # This quality works, try higher quality
                best_data = data
                best_quality = mid
                best_size = size
                low = mid + 1
                
                # If we're within tolerance of target, we can stop
                if target_bytes - size <= SIZE_TOLERANCE_BYTES:
                    break
            else:
                # File too large, reduce quality
                high = mid - 1
                
        except Exception as e:
            print(f"    Warning: Error at quality {mid}: {e}")
            high = mid - 1
    
    return best_data, best_quality, best_size


def compress_image(input_path: Path, output_path: Path, target_bytes: int) -> Tuple[bool, int, int, str]:
    """
    Compress a single image to target file size.
    
    Args:
        input_path: Path to input image
        output_path: Path to save compressed image
        target_bytes: Target file size in bytes
        
    Returns:
        Tuple of (success, original_size, compressed_size, message)
    """
    try:
        # Open image
        img = Image.open(input_path)
        original_size = input_path.stat().st_size
        
        # If already under target, just copy
        if original_size <= target_bytes:
            img.save(output_path, optimize=True)
            return True, original_size, output_path.stat().st_size, "Already under target"
        
        # Determine best format based on original
        original_format = img.format
        if original_format in ('JPEG', 'JPG'):
            format_type = 'JPEG'
        elif original_format == 'PNG':
            format_type = 'PNG'
        elif original_format == 'WEBP':
            format_type = 'WebP'
        else:
            # Default to JPEG for other formats
            format_type = 'JPEG'
        
        # Find optimal quality
        compressed_data, final_quality, final_size = find_optimal_quality(img, target_bytes, format_type)
        
        if compressed_data is None:
            return False, original_size, 0, f"Could not compress below {target_bytes} bytes"
        
        # Save compressed image
        with open(output_path, 'wb') as f:
            f.write(compressed_data)
        
        reduction_pct = ((original_size - final_size) / original_size) * 100
        message = f"Quality: {final_quality}, Reduction: {reduction_pct:.1f}%"
        
        return True, original_size, final_size, message
        
    except Exception as e:
        return False, 0, 0, f"Error: {str(e)}"


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def process_folder(input_dir: str, target_kb: int):
    """
    Process all images in the input directory.
    
    Args:
        input_dir: Path to folder containing images
        target_kb: Target file size in KB
    """
    input_path = Path(input_dir).resolve()
    
    if not input_path.exists():
        print(f"❌ Error: Input directory '{input_dir}' does not exist")
        return
    
    if not input_path.is_dir():
        print(f"❌ Error: '{input_dir}' is not a directory")
        return
    
    # Create compressed subfolder
    output_path = input_path / "compressed"
    output_path.mkdir(exist_ok=True)
    
    target_bytes = target_kb * 1024
    
    # Find all image files
    image_files = []
    for ext in SUPPORTED_FORMATS:
        image_files.extend(input_path.glob(f"*{ext}"))
        image_files.extend(input_path.glob(f"*{ext.upper()}"))
    
    if not image_files:
        print(f"⚠️  No image files found in '{input_dir}'")
        print(f"   Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return
    
    print(f"🎯 Target file size: {format_size(target_bytes)}")
    print(f"📁 Input folder: {input_path}")
    print(f"📂 Output folder: {output_path}")
    print(f"🖼️  Found {len(image_files)} image(s) to process")
    print("=" * 80)
    
    # Process each image
    total_original = 0
    total_compressed = 0
    success_count = 0
    failed_count = 0
    
    for idx, img_file in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}] Processing: {img_file.name}")
        
        output_file = output_path / img_file.name
        
        try:
            success, orig_size, comp_size, message = compress_image(
                img_file, output_file, target_bytes
            )
            
            if success:
                total_original += orig_size
                total_compressed += comp_size
                success_count += 1
                
                print(f"    ✅ {format_size(orig_size)} → {format_size(comp_size)}")
                print(f"    {message}")
            else:
                failed_count += 1
                print(f"    ❌ {message}")
                
        except Exception as e:
            failed_count += 1
            print(f"    ❌ Unexpected error: {e}")
            traceback.print_exc()
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 COMPRESSION REPORT")
    print("=" * 80)
    print(f"✅ Successfully compressed: {success_count}/{len(image_files)}")
    
    if failed_count > 0:
        print(f"❌ Failed: {failed_count}/{len(image_files)}")
    
    if success_count > 0:
        total_reduction = total_original - total_compressed
        reduction_pct = (total_reduction / total_original) * 100 if total_original > 0 else 0
        
        print(f"\n📈 Total original size: {format_size(total_original)}")
        print(f"📉 Total compressed size: {format_size(total_compressed)}")
        print(f"💾 Total space saved: {format_size(total_reduction)} ({reduction_pct:.1f}%)")
    
    print(f"\n✨ Compressed images saved to: {output_path}")
    print("=" * 80)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main function to run the compression script."""
    print("=" * 80)
    print("🖼️  IMAGE COMPRESSION - TARGET FILE SIZE")
    print("=" * 80)
    print()
    
    # Allow command-line override
    input_dir = INPUT_DIR
    target_kb = TARGET_SIZE_KB
    
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            target_kb = int(sys.argv[2])
        except ValueError:
            print(f"❌ Error: Invalid target size '{sys.argv[2]}'. Must be an integer (KB)")
            sys.exit(1)
    
    process_folder(input_dir, target_kb)


if __name__ == "__main__":
    main()
