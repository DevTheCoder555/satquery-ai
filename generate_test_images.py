#!/usr/bin/env python3
"""
Generate realistic satellite test images for SatQuery AI
Creates synthetic but realistic-looking satellite imagery
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import os


def create_realistic_satellite_image(width=512, height=512, seed=42):
    """Create a realistic synthetic satellite image"""
    np.random.seed(seed)

    # Create base image with noise
    img_array = np.random.randint(50, 150, (height, width, 3), dtype=np.uint8)

    # Add different land cover types
    img = Image.fromarray(img_array)
    draw = ImageDraw.Draw(img)

    # Add water bodies (blue)
    for _ in range(3):
        x1, y1 = np.random.randint(0, width - 100), np.random.randint(0, height - 100)
        x2, y2 = x1 + np.random.randint(50, 150), y1 + np.random.randint(50, 150)
        draw.ellipse([x1, y1, x2, y2], fill=(30, 80, 180))

    # Add vegetation (green)
    for _ in range(5):
        x1, y1 = np.random.randint(0, width - 80), np.random.randint(0, height - 80)
        x2, y2 = x1 + np.random.randint(40, 120), y1 + np.random.randint(40, 120)
        draw.ellipse([x1, y1, x2, y2], fill=(40, 120, 50))

    # Add urban areas (gray/brown)
    for _ in range(4):
        x1, y1 = np.random.randint(0, width - 60), np.random.randint(0, height - 60)
        x2, y2 = x1 + np.random.randint(30, 100), y1 + np.random.randint(30, 100)
        draw.rectangle([x1, y1, x2, y2], fill=(140, 130, 120))

    # Add roads (light gray lines)
    for _ in range(3):
        x1, y1 = np.random.randint(0, width), np.random.randint(0, height)
        x2, y2 = np.random.randint(0, width), np.random.randint(0, height)
        draw.line([x1, y1, x2, y2], fill=(200, 200, 200), width=3)

    # Apply blur to make it more realistic
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

    # Add some noise
    img_array = np.array(img)
    noise = np.random.randint(-10, 10, img_array.shape, dtype=np.int16)
    img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(img_array)


def create_change_detection_pair(seed1=42, seed2=43):
    """Create a pair of images showing changes over time"""
    # First image (before)
    img1 = create_realistic_satellite_image(seed=seed1)

    # Second image (after) - with some changes
    img2_array = np.array(img1)

    # Simulate urban expansion
    draw = ImageDraw.Draw(Image.fromarray(img2_array))
    for _ in range(3):
        x1, y1 = np.random.randint(100, 400), np.random.randint(100, 400)
        x2, y2 = x1 + np.random.randint(30, 80), y1 + np.random.randint(30, 80)
        draw.rectangle([x1, y1, x2, y2], fill=(150, 140, 130))

    img2 = Image.fromarray(img2_array)
    img2 = img2.filter(ImageFilter.GaussianBlur(radius=1.5))

    return img1, img2


def create_optical_sar_pair(seed=42):
    """Create optical and SAR image pair"""
    # Optical image (RGB)
    optical = create_realistic_satellite_image(seed=seed)

    # SAR image (grayscale with different characteristics)
    optical_array = np.array(optical)

    # SAR characteristics: water is dark, urban is bright, vegetation is medium
    sar_array = np.zeros(
        (optical_array.shape[0], optical_array.shape[1]), dtype=np.uint8
    )

    # Water areas (dark in SAR)
    water_mask = (optical_array[:, :, 2] > 150) & (optical_array[:, :, 0] < 80)
    sar_array[water_mask] = np.random.randint(20, 50, water_mask.sum())

    # Urban areas (bright in SAR)
    urban_mask = (
        (optical_array[:, :, 0] > 120)
        & (optical_array[:, :, 1] > 110)
        & (optical_array[:, :, 2] > 100)
    )
    sar_array[urban_mask] = np.random.randint(180, 230, urban_mask.sum())

    # Vegetation (medium in SAR)
    veg_mask = (optical_array[:, :, 1] > 100) & (optical_array[:, :, 0] < 80)
    sar_array[veg_mask] = np.random.randint(100, 150, veg_mask.sum())

    # Fill remaining with medium values
    other_mask = ~(water_mask | urban_mask | veg_mask)
    sar_array[other_mask] = np.random.randint(80, 120, other_mask.sum())

    # Add speckle noise (characteristic of SAR)
    speckle = np.random.randint(-15, 15, sar_array.shape, dtype=np.int16)
    sar_array = np.clip(sar_array.astype(np.int16) + speckle, 0, 255).astype(np.uint8)

    # Convert to RGB for consistency
    sar_rgb = np.stack([sar_array, sar_array, sar_array], axis=2)
    sar = Image.fromarray(sar_rgb)

    return optical, sar


def main():
    """Generate all test images"""
    output_dir = "test_images"
    os.makedirs(output_dir, exist_ok=True)

    print("Generating realistic satellite test images...")

    # Single images for VQA and grounding
    print("1. Creating single satellite images...")
    for i in range(1, 6):
        img = create_realistic_satellite_image(seed=i * 10)
        img.save(f"{output_dir}/satellite_{i}.png")
        print(f"   ✓ satellite_{i}.png")

    # Change detection pair
    print("2. Creating change detection pair...")
    img1, img2 = create_change_detection_pair()
    img1.save(f"{output_dir}/change_before.png")
    img2.save(f"{output_dir}/change_after.png")
    print("   ✓ change_before.png")
    print("   ✓ change_after.png")

    # Optical-SAR pair
    print("3. Creating optical-SAR pair...")
    optical, sar = create_optical_sar_pair()
    optical.save(f"{output_dir}/optical.png")
    sar.save(f"{output_dir}/sar.png")
    print("   ✓ optical.png")
    print("   ✓ sar.png")

    print(f"\n✅ Generated 10 test images in {output_dir}/")
    print("\nTest scenarios:")
    print("  • VQA: Use any satellite_*.png")
    print(
        "  • Grounding: Use any satellite_*.png with 'Highlight water/vegetation/urban'"
    )
    print("  • Change Detection: Use change_before.png + change_after.png")
    print("  • Optical-SAR Fusion: Use optical.png + sar.png")


if __name__ == "__main__":
    main()
