from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import base64
import io
import uuid


class GroundingModel:
    """
    Text-guided grounding model for satellite imagery.
    Locates and highlights specific objects/regions based on text queries.
    """

    def __init__(self):
        self.model_name = "Text-Guided Grounding"

    async def analyze(self, image_path: str, target: str) -> dict:
        """Locate and highlight target object in image"""

        # Load image
        image = Image.open(image_path).convert("RGB")
        image_array = np.array(image)

        # Detect target region
        mask, bbox = self._detect_target_region(image_array, target)

        # Generate visualization
        highlighted_image = self._create_highlighted_image(image, mask, bbox, target)

        # Generate answer
        answer = self._generate_answer(target, bbox, image_array.shape)

        # Calculate confidence
        confidence = self._calculate_confidence(mask, target)

        # Save evidence image
        evidence_path = self._save_evidence_image(highlighted_image)

        return {
            "answer": answer,
            "confidence": confidence,
            "evidence_images": [
                {
                    "type": "grounding_result",
                    "description": f"Highlighted location of {target}",
                    "url": f"/uploads/{evidence_path}",
                }
            ],
        }

    def _detect_target_region(self, image_array: np.ndarray, target: str) -> tuple:
        """Detect target region using color-based segmentation"""

        target_lower = target.lower()

        # Create mask based on target type
        if "water" in target_lower or "river" in target_lower or "lake" in target_lower:
            mask = self._segment_water(image_array)
        elif (
            "vegetation" in target_lower
            or "forest" in target_lower
            or "green" in target_lower
            or "tree" in target_lower
        ):
            mask = self._segment_vegetation(image_array)
        elif (
            "building" in target_lower
            or "built" in target_lower
            or "urban" in target_lower
        ):
            mask = self._segment_built_up(image_array)
        elif "road" in target_lower or "highway" in target_lower:
            mask = self._segment_roads(image_array)
        elif "soil" in target_lower or "bare" in target_lower:
            mask = self._segment_bare_soil(image_array)
        else:
            # Default: segment most prominent feature
            mask = self._segment_most_prominent(image_array)

        # Find bounding box
        bbox = self._mask_to_bbox(mask)

        return mask, bbox

    def _segment_water(self, image_array: np.ndarray) -> np.ndarray:
        """Segment water bodies"""
        if len(image_array.shape) != 3:
            return np.zeros(image_array.shape[:2], dtype=bool)

        b = image_array[:, :, 2].astype(float)
        r = image_array[:, :, 0].astype(float)
        g = image_array[:, :, 1].astype(float)

        # Water: high blue, low red and green
        water_mask = (b > r * 1.1) & (b > g * 1.1) & (b > 50)

        return water_mask

    def _segment_vegetation(self, image_array: np.ndarray) -> np.ndarray:
        """Segment vegetation"""
        if len(image_array.shape) != 3:
            return np.zeros(image_array.shape[:2], dtype=bool)

        g = image_array[:, :, 1].astype(float)
        r = image_array[:, :, 0].astype(float)
        b = image_array[:, :, 2].astype(float)

        # Vegetation: high green, NDVI-like
        veg_mask = (g > r) & (g > b) & (g > 50) & ((g - r) > 10)

        return veg_mask

    def _segment_built_up(self, image_array: np.ndarray) -> np.ndarray:
        """Segment built-up areas"""
        if len(image_array.shape) != 3:
            return np.zeros(image_array.shape[:2], dtype=bool)

        r = image_array[:, :, 0].astype(float)
        g = image_array[:, :, 1].astype(float)
        b = image_array[:, :, 2].astype(float)

        # Built-up: gray/brown tones
        built_mask = (np.abs(r - g) < 30) & (np.abs(g - b) < 30) & (r > 80) & (r < 200)

        return built_mask

    def _segment_roads(self, image_array: np.ndarray) -> np.ndarray:
        """Segment roads (simplified)"""
        if len(image_array.shape) != 3:
            return np.zeros(image_array.shape[:2], dtype=bool)

        r = image_array[:, :, 0].astype(float)
        g = image_array[:, :, 1].astype(float)
        b = image_array[:, :, 2].astype(float)

        # Roads: bright gray/white linear features
        road_mask = (
            (r > 150)
            & (g > 150)
            & (b > 150)
            & (np.abs(r - g) < 20)
            & (np.abs(g - b) < 20)
        )

        return road_mask

    def _segment_bare_soil(self, image_array: np.ndarray) -> np.ndarray:
        """Segment bare soil"""
        if len(image_array.shape) != 3:
            return np.zeros(image_array.shape[:2], dtype=bool)

        r = image_array[:, :, 0].astype(float)
        g = image_array[:, :, 1].astype(float)
        b = image_array[:, :, 2].astype(float)

        # Bare soil: brown/tan
        soil_mask = (r > g) & (g > b) & (r > 100) & (r < 200) & ((r - b) > 30)

        return soil_mask

    def _segment_most_prominent(self, image_array: np.ndarray) -> np.ndarray:
        """Segment most prominent feature"""
        if len(image_array.shape) != 3:
            return np.zeros(image_array.shape[:2], dtype=bool)

        # Use variance to find prominent regions
        gray = np.mean(image_array, axis=2)
        mean_val = np.mean(gray)

        # High variance regions
        prominent = np.abs(gray - mean_val) > np.std(gray)

        return prominent

    def _mask_to_bbox(self, mask: np.ndarray) -> tuple:
        """Convert binary mask to bounding box"""
        if not np.any(mask):
            return (0, 0, mask.shape[1], mask.shape[0])

        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)

        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]

        return (int(xmin), int(ymin), int(xmax), int(ymax))

    def _create_highlighted_image(
        self, image: Image.Image, mask: np.ndarray, bbox: tuple, target: str
    ) -> Image.Image:
        """Create visualization with highlighted region"""

        # Create copy
        highlighted = image.copy()
        draw = ImageDraw.Draw(highlighted)

        # Draw bounding box
        xmin, ymin, xmax, ymax = bbox
        draw.rectangle([xmin, ymin, xmax, ymax], outline="red", width=3)

        # Add label
        label = target.upper()
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
            )
        except:
            font = ImageFont.load_default()

        # Draw label background
        text_bbox = draw.textbbox((xmin, ymin - 30), label, font=font)
        draw.rectangle(text_bbox, fill="red")
        draw.text((xmin, ymin - 30), label, fill="white", font=font)

        # Add semi-transparent overlay for masked region
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Create mask visualization
        mask_rgb = np.zeros((*mask.shape, 4), dtype=np.uint8)
        mask_rgb[mask, 0] = 255  # Red
        mask_rgb[mask, 3] = 100  # Semi-transparent

        mask_image = Image.fromarray(mask_rgb, "RGBA")
        highlighted = Image.alpha_composite(highlighted.convert("RGBA"), mask_image)

        return highlighted.convert("RGB")

    def _generate_answer(self, target: str, bbox: tuple, image_shape: tuple) -> str:
        """Generate natural language answer"""
        xmin, ymin, xmax, ymax = bbox
        img_height, img_width = image_shape[:2]

        # Calculate position description
        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2

        # Relative position
        if center_y < img_height / 3:
            vertical = "northern"
        elif center_y > 2 * img_height / 3:
            vertical = "southern"
        else:
            vertical = "central"

        if center_x < img_width / 3:
            horizontal = "western"
        elif center_x > 2 * img_width / 3:
            horizontal = "eastern"
        else:
            horizontal = "central"

        position = f"{vertical} {horizontal}" if vertical != horizontal else vertical

        # Calculate size
        width = xmax - xmin
        height = ymax - ymin
        area = width * height
        total_area = img_width * img_height
        coverage = (area / total_area) * 100

        return f"The {target} is located in the {position} region of the image. It covers approximately {coverage:.1f}% of the scene and spans from coordinates ({xmin}, {ymin}) to ({xmax}, {ymax})."

    def _calculate_confidence(self, mask: np.ndarray, target: str) -> float:
        """Calculate confidence score"""

        # Base confidence
        confidence = 0.80

        # Check if mask has reasonable coverage
        mask_coverage = np.sum(mask) / (mask.shape[0] * mask.shape[1])

        if 0.01 < mask_coverage < 0.5:
            confidence += 0.10
        elif mask_coverage < 0.01:
            confidence -= 0.20

        return min(max(confidence, 0.5), 0.95)

def _save_evidence_image(self, image: Image.Image) -> str:
    """Save evidence image and return filename"""
    filename = f"grounding_{uuid.uuid4().hex[:8]}.png"
    # Use absolute path from backend directory
    backend_dir = Path(__file__).parent.parent.parent
    uploads_dir = backend_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    filepath = uploads_dir / filename
    image.save(filepath)
    return filename