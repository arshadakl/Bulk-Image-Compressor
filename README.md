# 🖼️ Image Compression by Target File Size

A **production-ready Python script** that compresses images to a specific target file size with **minimal visible quality loss**.

## ✨ Features

- 🎯 **Target file size compression** - Specify exact KB/MB output size
- 🔍 **Binary search optimization** - Finds highest quality that meets target
- 📐 **No resizing** - Maintains original image dimensions
- 🎨 **Multi-format support** - JPEG, PNG, WebP
- 🚀 **Batch processing** - Process entire folders automatically
- 📊 **Detailed reports** - See compression stats for each image
- 🛡️ **Error handling** - Gracefully handles corrupted files
- 💎 **Smart format handling** - PNG optimization, transparency preservation

## 📋 Requirements

```bash
pip install Pillow
```

That's it! No other dependencies needed.

## 🚀 Quick Start

### Basic Usage

```bash
# Compress all images in current folder to 200KB
python compress_images.py

# Compress images in specific folder
python compress_images.py "path/to/your/images"

# Compress to 500KB
python compress_images.py "path/to/images" 500

# Compress to 1MB (1024KB)
python compress_images.py "path/to/images" 1024
```

### Edit Configuration

Open `compress_images.py` and modify these settings:

```python
# Target file size in KB
TARGET_SIZE_KB = 200

# Input directory
INPUT_DIR = "."  # Current directory

# Quality bounds (adjust if needed)
MIN_QUALITY = 30
MAX_QUALITY = 95
```

## 📂 Output Structure

```
your-folder/
├── image1.jpg
├── image2.png
└── compressed/          # ← Created automatically
    ├── image1.jpg       # Compressed versions
    └── image2.png
```

**Original files are never modified.**

## 🔧 How It Works

### Compression Algorithm

1. **Check original size**
   - If already ≤ target → copy to `compressed/` folder
   
2. **Binary search for optimal quality**
   - Start with quality range 30-95
   - Test middle quality value
   - If file too large → reduce quality
   - If file small enough → try higher quality
   - Repeat until optimal quality found

3. **Format-specific handling**
   - **JPEG**: Quality-based compression, RGBA→RGB conversion
   - **PNG**: Optimize flag + compression level 9 + optional palette quantization
   - **WebP**: Lossy compression with method=6

4. **Save result**
   - Writes best compressed version to `compressed/` subfolder
   - Maintains original filename

### Quality vs. File Size

The script finds the **highest possible quality** that stays within your target file size. This means:
- Better results than hardcoded quality values
- Optimal trade-off between size and visual fidelity
- Different images may use different quality levels

## 📊 Sample Output

```
================================================================================
🖼️  IMAGE COMPRESSION - TARGET FILE SIZE
================================================================================

🎯 Target file size: 200.00 KB
📁 Input folder: D:\Photos
📂 Output folder: D:\Photos\compressed
🖼️  Found 5 image(s) to process
================================================================================

[1/5] Processing: sunset.jpg
    ✅ 2.45 MB → 198.23 KB
    Quality: 72, Reduction: 91.9%

[2/5] Processing: portrait.png
    ✅ 1.89 MB → 199.87 KB
    Quality: 85, Reduction: 89.7%

[3/5] Processing: logo.png
    ✅ 45.67 KB → 45.67 KB
    Already under target

================================================================================
📊 COMPRESSION REPORT
================================================================================
✅ Successfully compressed: 5/5

📈 Total original size: 8.32 MB
📉 Total compressed size: 987.45 KB
💾 Total space saved: 7.36 MB (88.5%)

✨ Compressed images saved to: D:\Photos\compressed
================================================================================
```

## 🎛️ Advanced Usage

### Supported Formats

- `.jpg` / `.jpeg` - JPEG images
- `.png` - PNG images (with transparency)
- `.webp` - WebP images

### PNG Handling

PNGs are handled specially because they don't have a simple "quality" parameter:

1. Try optimized PNG with `compress_level=9`
2. If too large, try quantizing to 256 colors (palette mode)
3. If still too large, convert to WebP format
4. Binary search on WebP quality

### Transparency

- RGBA images are handled correctly
- JPEG conversion uses white background for transparent areas
- PNG/WebP preserve transparency

### Edge Cases

✅ **Small images** - If already under target, just optimized and copied  
✅ **Large PNGs** - Automatically tries palette conversion or WebP fallback  
✅ **Corrupted images** - Skipped with error message, doesn't stop batch  
✅ **Non-image files** - Ignored automatically  

## ⚙️ Configuration Options

### Target Size Tolerance

```python
SIZE_TOLERANCE_BYTES = 1024  # Stop if within 1KB of target
```

Allows slight overshooting to avoid excessive iterations.

### Quality Bounds

```python
MIN_QUALITY = 30  # Don't go below this
MAX_QUALITY = 95  # Don't go above this
```

Adjust if you want stricter quality requirements.

## 🛡️ Safety Features

- ✅ Never modifies original files
- ✅ Creates separate `compressed/` folder
- ✅ Graceful error handling
- ✅ Detailed logging
- ✅ Validates input paths
- ✅ Handles file permission issues

## 📝 Use Cases

### 1. Website Optimization
Compress product images to exactly 200KB for fast loading:
```bash
python compress_images.py "./product-photos" 200
```

### 2. Email Attachments
Reduce images to 500KB for email-friendly sizes:
```bash
python compress_images.py "./vacation-photos" 500
```

### 3. Mobile App Assets
Optimize assets to 150KB for mobile apps:
```bash
python compress_images.py "./app-assets" 150
```

### 4. Social Media
Prepare images at 1MB for social platforms:
```bash
python compress_images.py "./social-content" 1024
```

## 🐛 Troubleshooting

### "No image files found"
- Check that folder contains `.jpg`, `.jpeg`, `.png`, or `.webp` files
- Verify folder path is correct

### "Could not compress below target"
- Target size may be too aggressive
- Try increasing target size
- Very detailed images may not compress well

### Import Error: "No module named 'PIL'"
```bash
pip install Pillow
```

## 🧪 Testing

Test with a single image first:
```bash
# Create test folder with one image
mkdir test-images
# Copy one image to test-images/
python compress_images.py test-images 200
```

## 📄 License

This script is provided as-is for production use. Modify as needed.

## 🤝 Contributing

Feel free to enhance with:
- Additional format support (TIFF, BMP, etc.)
- Multiprocessing for faster batch processing
- GUI interface
- Progress bars

## 🔬 Technical Details

### Binary Search Complexity
- Time: O(log Q) where Q is quality range (typically ~6 iterations)
- Each iteration requires one image encoding operation
- Much faster than linear search

### Memory Usage
- Uses `BytesIO` for in-memory operations
- No temporary files written during search
- Original image loaded once

### Determinism
- Same input always produces same output
- Reproducible results for testing/CI

---

**Built for production asset pipelines. Safe, fast, precise.**
