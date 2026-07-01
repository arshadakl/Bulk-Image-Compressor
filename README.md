# 🖼️ Bulk Image Compressor

A Python script that batch-compresses images to a **fixed target size** or by a **percentage of the original size**, with minimal visible quality loss. Every image is always compressed — never skipped.

## ✨ Features

- 🎯 **Target size mode** — compress all images to a fixed KB limit
- 📉 **Percentage mode** — compress each image to X% of its original size (e.g. 50%, 35%, 75%)
- 🔍 **Binary search optimization** — finds highest quality that meets the target
- 💯 **Always compresses** — best-effort result saved even when target is unreachable
- 📐 **No resizing** — original dimensions preserved
- 🎨 **Multi-format** — JPEG, PNG, WebP
- 🚀 **Batch processing** — whole folder in one command
- 📊 **Detailed report** — per-image stats and totals
- 🛡️ **Error handling** — corrupted files skipped, batch continues

## 📋 Requirements

```bash
pip install Pillow
```

## 🚀 Usage

```
python compress_images.py <folder> [--target-kb KB] [--percentage PCT]
```

### Fixed target size (KB)

```bash
# Compress all images to 200KB (default)
python compress_images.py ./photos

# Compress to 500KB
python compress_images.py ./photos --target-kb 500

# Short flag
python compress_images.py ./photos -t 150
```

### Percentage mode

Compresses each image **to X% of its own original size**:

```bash
# Compress each image to 50% of its original size
python compress_images.py ./photos --percentage 50

# Compress to 35% of original
python compress_images.py ./photos --percentage 35

# Compress to 75% of original
python compress_images.py ./photos --percentage 75

# Short flag
python compress_images.py ./photos -p 50
```

> `--percentage 50` on a 4MB image → targets 2MB  
> `--percentage 50` on a 600KB image → targets 300KB

### Cannot use both flags together

```bash
python compress_images.py ./photos -p 50 --target-kb 200  # ❌ Error
```

## 📂 Output Structure

```
your-folder/
├── image1.jpg
├── image2.png
└── compressed/          ← Created automatically
    ├── image1.jpg       ← Compressed versions
    └── image2.png
```

Original files are never modified.

## 📊 Sample Output

```
================================================================================
🖼️  BULK IMAGE COMPRESSOR
================================================================================

🎯 Mode: percentage mode (50% of original size per image)
📁 Input:  D:\Photos
📂 Output: D:\Photos\compressed
🖼️  Found 4 image(s) to process
================================================================================

[1/4] Processing: sunset.jpg
    ✅ 2.45 MB → 1.22 MB
    Quality: 78, Reduction: 50.2%

[2/4] Processing: portrait.png
    ✅ 1.89 MB → 941.23 KB
    Quality: 82, Reduction: 51.3%

[3/4] Processing: logo.png
    ✅ 45.67 KB → 45.67 KB
    Already under target

[4/4] Processing: raw_scan.jpg
    ⚠️  8.10 MB → 3.21 MB  (best effort, target was 4.15 MB)
    Quality: 10, Reduction: 60.4%

================================================================================
📊 COMPRESSION REPORT
================================================================================
✅ Hit target:   3/4
⚠️  Best effort:  1/4  (compressed as much as possible)

📈 Total original:    12.50 MB
📉 Total compressed:  5.43 MB
💾 Total saved:       7.07 MB (56.6%)

✨ Output folder: D:\Photos\compressed
================================================================================
```

### Best effort (⚠️)

When an image cannot reach the target (e.g. very dense raw scans), the script saves the **most compressed version achievable** at minimum quality instead of skipping it. No image is left behind.

## 🔧 How It Works

1. **Check original size** — if already ≤ target, copy optimized to `compressed/`
2. **Binary search quality** — tests quality range 10–95, finds highest that fits target
3. **Best effort fallback** — if no quality hits target, saves the minimum-quality result
4. **Format-specific handling**
   - **JPEG** — quality-based compression, RGBA→RGB with white background
   - **PNG** — `compress_level=9` → palette quantization → WebP fallback
   - **WebP** — lossy with `method=6`

## 🎛️ Supported Formats

| Extension | Format |
|-----------|--------|
| `.jpg` / `.jpeg` | JPEG |
| `.png` | PNG (transparency preserved) |
| `.webp` | WebP |

## 📝 Use Cases

### Website optimization
```bash
python compress_images.py ./product-photos --target-kb 200
```

### Email attachments
```bash
python compress_images.py ./vacation-photos --percentage 50
```

### Mobile assets
```bash
python compress_images.py ./app-assets --target-kb 150
```

### Bulk archive reduction
```bash
python compress_images.py ./archive --percentage 35
```

## 🐛 Troubleshooting

### "No image files found"
Check folder contains `.jpg`, `.jpeg`, `.png`, or `.webp` files and path is correct.

### Image shows ⚠️ best effort
Target is too aggressive for that image's content. Either raise `--percentage` or `--target-kb`, or accept the best-effort output — it's still compressed as much as possible.

### Import error: `No module named 'PIL'`
```bash
pip install Pillow
```

## 🛡️ Safety

- Never modifies original files
- Creates separate `compressed/` folder
- Graceful error handling — one failure doesn't stop the batch
- Validates input paths before processing

---

**Compresses every image, every time.**
