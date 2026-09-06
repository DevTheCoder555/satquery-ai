from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import base64
import io
import uuid


class ChangeDetectionModel:
    """
    Bi-temporal change detection model for satellite imagery.
    Analyzes changes between two images from different time periods.
    """

    def __init__(self):
        self.model_name = "Bi-Temporal Change Detection"

    async def analyze(self, image_path1: str, image_path2: str, query: str) -> dict:
        """Analyze changes between two images"""

        # Load images
        image1 = Image.open(image_path1).convert("RGB")
        image2 = Image.open(image_path2).convert("RGB")

        # Resize to same dimensions if needed
        if image1.size != image2.size:
            image2 = image2.resize(image1.size, Image.Resampling.LANCZOS)

        array1 = np.array(image1)
        array2 = np.array(image2)

        # Detect changes
        change_mask, change_stats = self._detect_changes(array1, array2)

        # Generate change map visualization
        change_map = self._create_change_map(image1, image2, change_mask)

        # Generate answer based on query and changes
        answer = self._generate_answer(query, change_stats, array1.shape)

        # Calculate confidence
        confidence = self._calculate_confidence(change_mask, array1, array2)

        # Save evidence images
        change_map_path = self._save_evidence_image(change_map, "change_map")

        return {
            "answer": answer,
            "confidence": confidence,
            "evidence_images": [
                {
                    "type": "change_map",
                    "description": "Visual change detection map (red = changed areas)",
                    "url": f"/uploads/{change_map_path}",
                }
            ],
        }

    def _detect_changes(self, array1: np.ndarray, array2: np.ndarray) -> tuple:
        """Detect changes between two images"""

        # Convert to float for calculations
        img1 = array1.astype(float)
        img2 = array2.astype(float)

        # Calculate difference
        if len(img1.shape) == 3:
            # Color image - use multiple methods
            diff = np.sqrt(np.sum((img1 - img2) ** 2, axis=2))
        else:
            # Grayscale
            diff = np.abs(img1 - img2)

        # Normalize difference
        diff_normalized = (diff - diff.min()) / (diff.max() - diff.min() + 1e-8)

        # Apply threshold to create binary change mask
        threshold = np.mean(diff_normalized) + 1.5 * np.std(diff_normalized)
        change_mask = diff_normalized > threshold

        # Calculate change statistics
        change_stats = self._calculate_change_statistics(img1, img2, change_mask)

        return change_mask, change_stats

    def _calculate_change_statistics(
        self, img1: np.ndarray, img2: np.ndarray, change_mask: np.ndarray
    ) -> dict:
        """Calculate statistics about detected changes"""

        total_pixels = change_mask.shape[0] * change_mask.shape[1]
        changed_pixels = np.sum(change_mask)
        change_percentage = (changed_pixels / total_pixels) * 100

        # Analyze type of changes
        if len(img1.shape) == 3:
            # Check for increase/decrease in different land covers
            green1 = img1[:, :, 1].mean()
            green2 = img2[:, :, 1].mean()

            blue1 = img1[:, :, 2].mean()
            blue2 = img2[:, :, 2].mean()

            brightness1 = img1.mean()
            brightness2 = img2.mean()

            stats = {
                "change_percentage": float(change_percentage),
                "changed_pixels": int(changed_pixels),
                "total_pixels": int(total_pixels),
                "vegetation_change": float(green2 - green1),
                "water_change": float(blue2 - blue1),
                "brightness_change": float(brightness2 - brightness1),
                "increased_vegetation": green2 > green1 * 1.1,
                "decreased_vegetation": green2 < green1 * 0.9,
                "increased_water": blue2 > blue1 * 1.1,
                "decreased_water": blue2 < blue1 * 0.9,
                "increased_brightness": brightness2 > brightness1 * 1.1,
                "decreased_brightness": brightness2 < brightness1 * 0.9,
            }
        else:
            stats = {
                "change_percentage": float(change_percentage),
                "changed_pixels": int(changed_pixels),
                "total_pixels": int(total_pixels),
                "brightness_change": float(img2.mean() - img1.mean()),
            }

        return stats

    def _create_change_map(
        self, image1: Image.Image, image2: Image.Image, change_mask: np.ndarray
    ) -> Image.Image:
        """Create visual change map"""

        # Create side-by-side comparison with change overlay
        width, height = image1.size

        # Create new image with 3 panels
        result = Image.new("RGB", (width * 3 + 20, height + 40), "white")

        # Add images
        result.paste(image1, (0, 40))
        result.paste(image2, (width + 10, 40))

        # Create change overlay
        change_overlay = image1.copy().convert("RGBA")
        overlay_array = np.array(change_overlay)

        # Mark changed areas in red
        overlay_array[change_mask, 0] = 255  # Red
        overlay_array[change_mask, 1] = 0  # Green
        overlay_array[change_mask, 2] = 0  # Blue
        overlay_array[change_mask, 3] = 150  # Semi-transparent

        change_img = Image.fromarray(overlay_array, "RGBA")
        result.paste(change_img.convert("RGB"), (width * 2 + 20, 40))

        # Add labels
        draw = ImageDraw.Draw(result)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
            )
        except:
            font = ImageFont.load_default()

        draw.text((width // 2 - 30, 10), "Image 1", fill="black", font=font)
        draw.text(
            (width + 10 + width // 2 - 30, 10), "Image 2", fill="black", font=font
        )
        draw.text(
            (width * 2 + 20 + width // 2 - 40, 10),
            "Change Map",
            fill="black",
            font=font,
        )

        return result

    def _generate_answer(self, query: str, stats: dict, image_shape: tuple) -> str:
        """Generate natural language answer about changes"""

        query_lower = query.lower()
        change_pct = stats["change_percentage"]

        # Determine magnitude
        if change_pct < 5:
            magnitude = "minimal"
        elif change_pct < 15:
            magnitude = "moderate"
        elif change_pct < 30:
            magnitude = "significant"
        else:
            magnitude = "substantial"

        # Build answer based on query type
        if "what" in query_lower and "change" in query_lower:
            answer = f"Analysis reveals {magnitude} changes between the two images. "
            answer += f"Approximately {change_pct:.1f}% of the area shows detectable changes. "

            if stats.get("increased_vegetation"):
                answer += "Vegetation coverage has increased. "
            elif stats.get("decreased_vegetation"):
                answer += "Vegetation coverage has decreased. "

            if stats.get("increased_water"):
                answer += "Water body coverage has expanded. "
            elif stats.get("decreased_water"):
                answer += "Water body coverage has reduced. "

            if stats.get("increased_brightness"):
                answer += "Overall brightness has increased, suggesting new built-up development. "
            elif stats.get("decreased_brightness"):
                answer += "Overall brightness has decreased. "

            return answer

        elif (
            "built" in query_lower
            or "urban" in query_lower
            or "increase" in query_lower
        ):
            if stats.get("increased_brightness") and change_pct > 10:
                return f"Yes, built-up area has increased. The analysis shows {magnitude} changes with {change_pct:.1f}% of the area affected. Brightness values have increased, indicating new construction and urban development."
            else:
                return f"Built-up area changes are {magnitude}. Approximately {change_pct:.1f}% of the area shows changes, but brightness analysis does not strongly indicate significant urban expansion."

        elif (
            "vegetation" in query_lower
            or "forest" in query_lower
            or "green" in query_lower
        ):
            if stats.get("increased_vegetation"):
                return f"Vegetation has increased between the two dates. The analysis shows {magnitude} changes with {change_pct:.1f}% of the area affected. Green cover has expanded, suggesting afforestation or agricultural growth."
            elif stats.get("decreased_vegetation"):
                return f"Vegetation has decreased between the two dates. The analysis shows {magnitude} changes with {change_pct:.1f}% of the area affected. Green cover has reduced, suggesting deforestation or land conversion."
            else:
                return f"Vegetation changes are {magnitude} with {change_pct:.1f}% of the area showing detectable changes. No significant trend in vegetation increase or decrease was detected."

        elif "water" in query_lower:
            if stats.get("increased_water"):
                return f"Water coverage has increased. The analysis shows {magnitude} changes with {change_pct:.1f}% of the area affected. Water bodies appear to have expanded."
            elif stats.get("decreased_water"):
                return f"Water coverage has decreased. The analysis shows {magnitude} changes with {change_pct:.1f}% of the area affected. Water bodies appear to have shrunk."
            else:
                return f"Water body changes are {magnitude} with {change_pct:.1f}% of the area showing detectable changes. No significant trend in water coverage was detected."

        else:
            # Generic response
            answer = f"Bi-temporal analysis reveals {magnitude} changes between the two images. "
            answer += f"Approximately {change_pct:.1f}% of the total area ({stats['changed_pixels']:,} pixels) shows detectable changes. "

            if change_pct > 20:
                answer += "The changes are substantial and affect a large portion of the scene. "
            elif change_pct > 10:
                answer += (
                    "The changes are clearly visible and affect a significant area. "
                )
            else:
                answer += "The changes are relatively minor and localized. "

            return answer

    def _calculate_confidence(
        self, change_mask: np.ndarray, array1: np.ndarray, array2: np.ndarray
    ) -> float:
        """Calculate confidence score"""

        # Base confidence
        confidence = 0.75

        # Image similarity affects confidence
        if len(array1.shape) == 3:
            correlation = np.corrcoef(array1.flatten(), array2.flatten())[0, 1]
            if correlation > 0.9:
                confidence += 0.10  # High correlation
            elif correlation < 0.5:
                confidence -= 0.15  # Low correlation

        # Change amount affects confidence
        change_pct = np.sum(change_mask) / (change_mask.shape[0] * change_mask.shape[1])
        if 0.05 < change_pct < 0.4:
            confidence += 0.05  # Reasonable change amount

        return min(max(confidence, 0.5), 0.95)

    def _save_evidence_image(self, image: Image.Image, prefix: str) -> str:
        """Save evidence image and return filename"""
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = Path("uploads") / filename
        image.save(filepath)
        return filename
