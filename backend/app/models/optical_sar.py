from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import base64
import io
import uuid


class OpticalSARModel:
    """
    Optical + SAR fusion model for satellite imagery.
    Combines information from optical and SAR sensors for enhanced analysis.
    """

    def __init__(self):
        self.model_name = "Optical-SAR Fusion"

    async def analyze(
        self, image_path1: str, image_path2: str, sensor_types: list[str], query: str
    ) -> dict:
        """Analyze optical and SAR images together"""

        # Load images
        image1 = Image.open(image_path1).convert("RGB")
        image2 = Image.open(image_path2).convert("RGB")

        # Resize to same dimensions if needed
        if image1.size != image2.size:
            image2 = image2.resize(image1.size, Image.Resampling.LANCZOS)

        array1 = np.array(image1)
        array2 = np.array(image2)

        # Determine which is optical and which is SAR
        optical_idx = 0
        sar_idx = 1

        if sensor_types and len(sensor_types) >= 2:
            if sensor_types[0].lower() == "sar":
                optical_idx = 1
                sar_idx = 0

        optical_array = array1 if optical_idx == 0 else array2
        sar_array = array2 if sar_idx == 1 else array1

        # Perform fusion analysis
        fusion_result = self._perform_fusion(optical_array, sar_array, query)

        # Generate visualization
        fusion_map = self._create_fusion_visualization(image1, image2, fusion_result)

        # Generate answer
        answer = self._generate_answer(query, fusion_result)

        # Calculate confidence
        confidence = self._calculate_confidence(fusion_result)

        # Save evidence image
        fusion_map_path = self._save_evidence_image(fusion_map, "fusion")

        return {
            "answer": answer,
            "confidence": confidence,
            "evidence_images": [
                {
                    "type": "fusion_result",
                    "description": "Optical-SAR fusion analysis result",
                    "url": f"/uploads/{fusion_map_path}",
                }
            ],
        }

    def _perform_fusion(self, optical: np.ndarray, sar: np.ndarray, query: str) -> dict:
        """Perform optical-SAR fusion analysis"""

        query_lower = query.lower()

        # Extract features from optical image
        optical_features = self._extract_optical_features(optical)

        # Extract features from SAR image
        sar_features = self._extract_sar_features(sar)

        # Fuse features
        fused_features = self._fuse_features(optical_features, sar_features)

        # Perform task-specific analysis
        if "built" in query_lower or "urban" in query_lower:
            result = self._detect_built_up_fused(fused_features)
        elif "water" in query_lower:
            result = self._detect_water_fused(fused_features)
        elif "vegetation" in query_lower or "forest" in query_lower:
            result = self._detect_vegetation_fused(fused_features)
        else:
            # General land cover classification
            result = self._classify_land_cover_fused(fused_features)

        return result

    def _extract_optical_features(self, optical: np.ndarray) -> dict:
        """Extract features from optical image"""

        if len(optical.shape) != 3:
            return {"brightness": optical.astype(float)}

        r = optical[:, :, 0].astype(float)
        g = optical[:, :, 1].astype(float)
        b = optical[:, :, 2].astype(float)

        features = {
            "red": r,
            "green": g,
            "blue": b,
            "brightness": (r + g + b) / 3,
            "ndvi_like": (g - r) / (g + r + 1e-8),  # Vegetation indicator
            "water_index": (b - g) / (b + g + 1e-8),  # Water indicator
            "built_up_index": (r - g) / (r + g + 1e-8),  # Built-up indicator
        }

        return features

    def _extract_sar_features(self, sar: np.ndarray) -> dict:
        """Extract features from SAR image"""

        if len(sar.shape) == 3:
            # Convert to grayscale if needed
            sar_gray = np.mean(sar, axis=2)
        else:
            sar_gray = sar.astype(float)

        # Normalize
        sar_normalized = (sar_gray - sar_gray.min()) / (
            sar_gray.max() - sar_gray.min() + 1e-8
        )

        features = {
            "backscatter": sar_normalized,
            "texture": self._calculate_texture(sar_normalized),
            "edges": self._detect_edges(sar_normalized),
        }

        return features

    def _calculate_texture(self, image: np.ndarray) -> np.ndarray:
        """Calculate texture feature using local variance"""
        # Local variance as texture measure using numpy
        kernel_size = 5
        pad = kernel_size // 2

        # Pad image
        padded = np.pad(image, pad, mode="edge")

        # Calculate local mean using sliding window
        mean = np.zeros_like(image, dtype=float)
        mean_sq = np.zeros_like(image, dtype=float)

        for i in range(kernel_size):
            for j in range(kernel_size):
                mean += padded[i : i + image.shape[0], j : j + image.shape[1]]
                mean_sq += padded[i : i + image.shape[0], j : j + image.shape[1]] ** 2

        mean /= kernel_size * kernel_size
        mean_sq /= kernel_size * kernel_size
        variance = mean_sq - mean**2

        return variance

    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Detect edges using Sobel operator with numpy"""
        # Sobel kernels
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=float)

        # Pad image
        padded = np.pad(image, 1, mode="edge")

        # Convolve with Sobel kernels
        edges_x = np.zeros_like(image, dtype=float)
        edges_y = np.zeros_like(image, dtype=float)

        for i in range(3):
            for j in range(3):
                edges_x += (
                    sobel_x[i, j]
                    * padded[i : i + image.shape[0], j : j + image.shape[1]]
                )
                edges_y += (
                    sobel_y[i, j]
                    * padded[i : i + image.shape[0], j : j + image.shape[1]]
                )

        edges = np.hypot(edges_x, edges_y)

        return edges

    def _fuse_features(self, optical: dict, sar: dict) -> dict:
        """Fuse optical and SAR features"""

        fused = {}

        # Combine brightness
        if "brightness" in optical and "backscatter" in sar:
            fused["combined_brightness"] = (
                optical["brightness"] / (optical["brightness"].max() + 1e-8)
                + sar["backscatter"]
            ) / 2

        # Combine vegetation indicators
        if "ndvi_like" in optical and "texture" in sar:
            fused["vegetation_score"] = (
                optical["ndvi_like"]
                + (1 - sar["texture"] / (sar["texture"].max() + 1e-8))
            ) / 2

        # Combine water indicators
        if "water_index" in optical and "backscatter" in sar:
            # Water appears dark in both optical and SAR
            fused["water_score"] = (
                optical["water_index"] + (1 - sar["backscatter"])
            ) / 2

        # Combine built-up indicators
        if "built_up_index" in optical and "edges" in sar:
            fused["built_up_score"] = (
                optical["built_up_index"] + sar["edges"] / (sar["edges"].max() + 1e-8)
            ) / 2

        # Add raw features
        fused.update(optical)
        fused.update(sar)

        return fused

    def _detect_built_up_fused(self, features: dict) -> dict:
        """Detect built-up areas using fused features"""

        if "built_up_score" in features:
            score = features["built_up_score"]
            threshold = np.mean(score) + 0.5 * np.std(score)
            mask = score > threshold

            coverage = np.sum(mask) / (mask.shape[0] * mask.shape[1]) * 100

            return {
                "class": "built_up",
                "mask": mask,
                "coverage": float(coverage),
                "confidence": 0.85 if coverage > 10 else 0.75,
            }

        return {"class": "built_up", "mask": None, "coverage": 0, "confidence": 0.6}

    def _detect_water_fused(self, features: dict) -> dict:
        """Detect water using fused features"""

        if "water_score" in features:
            score = features["water_score"]
            threshold = np.mean(score) + 0.5 * np.std(score)
            mask = score > threshold

            coverage = np.sum(mask) / (mask.shape[0] * mask.shape[1]) * 100

            return {
                "class": "water",
                "mask": mask,
                "coverage": float(coverage),
                "confidence": 0.85 if coverage > 5 else 0.75,
            }

        return {"class": "water", "mask": None, "coverage": 0, "confidence": 0.6}

    def _detect_vegetation_fused(self, features: dict) -> dict:
        """Detect vegetation using fused features"""

        if "vegetation_score" in features:
            score = features["vegetation_score"]
            threshold = np.mean(score) + 0.5 * np.std(score)
            mask = score > threshold

            coverage = np.sum(mask) / (mask.shape[0] * mask.shape[1]) * 100

            return {
                "class": "vegetation",
                "mask": mask,
                "coverage": float(coverage),
                "confidence": 0.85 if coverage > 20 else 0.75,
            }

        return {"class": "vegetation", "mask": None, "coverage": 0, "confidence": 0.6}

    def _classify_land_cover_fused(self, features: dict) -> dict:
        """General land cover classification using fused features"""

        # Combine all scores
        masks = {}

        if "built_up_score" in features:
            score = features["built_up_score"]
            threshold = np.mean(score) + 0.5 * np.std(score)
            masks["built_up"] = score > threshold

        if "water_score" in features:
            score = features["water_score"]
            threshold = np.mean(score) + 0.5 * np.std(score)
            masks["water"] = score > threshold

        if "vegetation_score" in features:
            score = features["vegetation_score"]
            threshold = np.mean(score) + 0.5 * np.std(score)
            masks["vegetation"] = score > threshold

        # Create combined mask
        combined_mask = np.zeros_like(list(masks.values())[0]) if masks else None

        if combined_mask is not None:
            for class_name, mask in masks.items():
                combined_mask = np.logical_or(combined_mask, mask)

        return {
            "class": "land_cover",
            "mask": combined_mask,
            "masks": masks,
            "coverage": float(
                np.sum(combined_mask)
                / (combined_mask.shape[0] * combined_mask.shape[1])
                * 100
            )
            if combined_mask is not None
            else 0,
            "confidence": 0.80,
        }

    def _create_fusion_visualization(
        self, image1: Image.Image, image2: Image.Image, result: dict
    ) -> Image.Image:
        """Create visualization of fusion result"""

        width, height = image1.size

        # Create new image with 3 panels
        result_img = Image.new("RGB", (width * 3 + 20, height + 40), "white")

        # Add original images
        result_img.paste(image1, (0, 40))
        result_img.paste(image2, (width + 10, 40))

        # Create fusion result overlay
        if result.get("mask") is not None:
            mask = result["mask"]

            # Create colored overlay
            overlay = image1.copy().convert("RGBA")
            overlay_array = np.array(overlay)

            # Color based on class
            class_name = result.get("class", "land_cover")
            if class_name == "water":
                overlay_array[mask, 0] = 0  # Blue
                overlay_array[mask, 1] = 0
                overlay_array[mask, 2] = 255
            elif class_name == "vegetation":
                overlay_array[mask, 0] = 0  # Green
                overlay_array[mask, 1] = 255
                overlay_array[mask, 2] = 0
            else:  # built_up or land_cover
                overlay_array[mask, 0] = 255  # Red
                overlay_array[mask, 1] = 0
                overlay_array[mask, 2] = 0

            overlay_array[mask, 3] = 150  # Semi-transparent

            fusion_img = Image.fromarray(overlay_array, "RGBA").convert("RGB")
            result_img.paste(fusion_img, (width * 2 + 20, 40))

        # Add labels
        draw = ImageDraw.Draw(result_img)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
            )
        except:
            font = ImageFont.load_default()

        draw.text((width // 2 - 30, 10), "Optical", fill="black", font=font)
        draw.text((width + 10 + width // 2 - 20, 10), "SAR", fill="black", font=font)
        draw.text(
            (width * 2 + 20 + width // 2 - 40, 10),
            "Fusion Result",
            fill="black",
            font=font,
        )

        return result_img

    def _generate_answer(self, query: str, result: dict) -> str:
        """Generate natural language answer"""

        query_lower = query.lower()
        class_name = result.get("class", "land_cover")
        coverage = result.get("coverage", 0)

        if "built" in query_lower or "urban" in query_lower:
            return f"Optical-SAR fusion analysis identified built-up areas covering {coverage:.1f}% of the scene. The combination of optical spectral information and SAR structural information provides enhanced detection of urban features. SAR backscatter patterns complement optical reflectance for improved built-up area identification."

        elif "water" in query_lower:
            return f"Optical-SAR fusion analysis detected water bodies covering {coverage:.1f}% of the scene. Water appears dark in both optical and SAR imagery, allowing robust detection through multi-sensor fusion. The combined analysis improves water body delineation compared to single-sensor approaches."

        elif "vegetation" in query_lower or "forest" in query_lower:
            return f"Optical-SAR fusion analysis identified vegetation covering {coverage:.1f}% of the scene. Optical data provides spectral vegetation information while SAR contributes structural information about vegetation height and density. The fusion enhances vegetation mapping accuracy."

        else:
            return f"Optical-SAR fusion analysis classified {coverage:.1f}% of the scene into distinct land cover classes. The multi-modal approach combines optical spectral information with SAR structural and textural features for comprehensive land cover mapping. This fusion strategy leverages the complementary strengths of both sensor types."

    def _calculate_confidence(self, result: dict) -> float:
        """Calculate confidence score"""

        base_confidence = result.get("confidence", 0.75)

        # Adjust based on coverage
        coverage = result.get("coverage", 0)
        if 5 < coverage < 50:
            base_confidence += 0.05

        return min(max(base_confidence, 0.5), 0.95)

def _save_evidence_image(self, image: Image.Image, prefix: str) -> str:
    """Save evidence image and return filename"""
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    # Use absolute path from backend directory
    backend_dir = Path(__file__).parent.parent.parent
    uploads_dir = backend_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    filepath = uploads_dir / filename
    image.save(filepath)
    return filename
