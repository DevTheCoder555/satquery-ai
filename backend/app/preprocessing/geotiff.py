"""
GeoTIFF preprocessing module for handling geospatial satellite imagery
"""

from pathlib import Path
from PIL import Image
import numpy as np
import io

# Try to import rasterio, but don't fail if not available
try:
    import rasterio
    from rasterio.enums import Resampling

    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    print("Warning: rasterio not installed. GeoTIFF support limited.")


class GeoTIFFProcessor:
    """Process GeoTIFF files with geospatial metadata"""

    def __init__(self):
        self.model_name = "GeoTIFF Processor"

    def load_geotiff(self, file_path: str) -> dict:
        """
        Load GeoTIFF file and extract metadata

        Returns:
            dict with keys:
                - image: PIL Image (RGB)
                - array: numpy array (original bands)
                - metadata: dict with geospatial info
                - band_count: number of bands
                - crs: coordinate reference system
                - bounds: geographic bounds
                - resolution: pixel resolution
        """
        if not RASTERIO_AVAILABLE:
            # Fallback to PIL
            return self._load_with_pil(file_path)

        try:
            with rasterio.open(file_path) as src:
                # Read all bands
                array = src.read()

                # Get metadata
                metadata = {
                    "width": src.width,
                    "height": src.height,
                    "band_count": src.count,
                    "dtype": str(src.dtypes[0]),
                    "crs": str(src.crs) if src.crs else None,
                    "bounds": {
                        "left": src.bounds.left,
                        "bottom": src.bounds.bottom,
                        "right": src.bounds.right,
                        "top": src.bounds.top,
                    }
                    if src.bounds
                    else None,
                    "resolution": {"x": src.res[0], "y": src.res[1]}
                    if src.res
                    else None,
                    "transform": str(src.transform) if src.transform else None,
                    "nodata": src.nodata,
                    "driver": src.driver,
                }

                # Convert to RGB for display
                rgb_image = self._convert_to_rgb(array, src.count)

                return {
                    "image": rgb_image,
                    "array": array,
                    "metadata": metadata,
                    "band_count": src.count,
                    "crs": metadata["crs"],
                    "bounds": metadata["bounds"],
                    "resolution": metadata["resolution"],
                }

        except Exception as e:
            print(f"Error loading GeoTIFF with rasterio: {e}")
            return self._load_with_pil(file_path)

    def _convert_to_rgb(self, array: np.ndarray, band_count: int) -> Image.Image:
        """Convert multi-band array to RGB PIL Image"""

        if band_count == 1:
            # Single band (grayscale or SAR)
            band = array[0]
            # Normalize to 0-255
            band_min, band_max = band.min(), band.max()
            if band_max > band_min:
                normalized = ((band - band_min) / (band_max - band_min) * 255).astype(
                    np.uint8
                )
            else:
                normalized = np.zeros_like(band, dtype=np.uint8)
            return Image.fromarray(normalized, mode="L").convert("RGB")

        elif band_count == 2:
            # Two bands - use first band as grayscale
            band = array[0]
            band_min, band_max = band.min(), band.max()
            if band_max > band_min:
                normalized = ((band - band_min) / (band_max - band_min) * 255).astype(
                    np.uint8
                )
            else:
                normalized = np.zeros_like(band, dtype=np.uint8)
            return Image.fromarray(normalized, mode="L").convert("RGB")

        elif band_count >= 3:
            # Three or more bands - use first 3 as RGB
            # Assume bands are in order: R, G, B (or similar)
            rgb = np.stack([array[0], array[1], array[2]], axis=-1)

            # Normalize each band
            for i in range(3):
                band = rgb[:, :, i]
                band_min, band_max = band.min(), band.max()
                if band_max > band_min:
                    rgb[:, :, i] = (
                        (band - band_min) / (band_max - band_min) * 255
                    ).astype(np.uint8)
                else:
                    rgb[:, :, i] = 0

            return Image.fromarray(rgb.astype(np.uint8), mode="RGB")

        else:
            # Fallback
            return Image.new("RGB", (100, 100), color="gray")

    def _load_with_pil(self, file_path: str) -> dict:
        """Fallback: Load with PIL only"""
        try:
            image = Image.open(file_path)

            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            array = np.array(image)

            metadata = {
                "width": image.width,
                "height": image.height,
                "band_count": 3,
                "dtype": str(array.dtype),
                "crs": None,
                "bounds": None,
                "resolution": None,
                "transform": None,
                "nodata": None,
                "driver": "PIL",
            }

            return {
                "image": image,
                "array": array,
                "metadata": metadata,
                "band_count": 3,
                "crs": None,
                "bounds": None,
                "resolution": None,
            }

        except Exception as e:
            print(f"Error loading image with PIL: {e}")
            raise

    def get_band_statistics(self, array: np.ndarray) -> dict:
        """Calculate statistics for each band"""
        stats = {}

        if len(array.shape) == 2:
            # Single band
            stats["band_1"] = {
                "min": float(array.min()),
                "max": float(array.max()),
                "mean": float(array.mean()),
                "std": float(array.std()),
            }
        else:
            # Multiple bands
            for i in range(array.shape[0]):
                band = array[i]
                stats[f"band_{i + 1}"] = {
                    "min": float(band.min()),
                    "max": float(band.max()),
                    "mean": float(band.mean()),
                    "std": float(band.std()),
                }

        return stats

    def extract_ndvi(
        self, array: np.ndarray, red_band: int = 0, nir_band: int = 3
    ) -> np.ndarray:
        """
        Calculate NDVI (Normalized Difference Vegetation Index)
        Requires at least 4 bands (Red, Green, Blue, NIR)

        NDVI = (NIR - Red) / (NIR + Red)
        """
        if array.shape[0] < 4:
            raise ValueError(
                "NDVI calculation requires at least 4 bands (Red, Green, Blue, NIR)"
            )

        red = array[red_band].astype(float)
        nir = array[nir_band].astype(float)

        # Avoid division by zero
        denominator = nir + red
        denominator[denominator == 0] = 1e-10

        ndvi = (nir - red) / denominator

        return ndvi

    def extract_ndwi(
        self, array: np.ndarray, green_band: int = 1, nir_band: int = 3
    ) -> np.ndarray:
        """
        Calculate NDWI (Normalized Difference Water Index)
        Requires at least 4 bands

        NDWI = (Green - NIR) / (Green + NIR)
        """
        if array.shape[0] < 4:
            raise ValueError("NDWI calculation requires at least 4 bands")

        green = array[green_band].astype(float)
        nir = array[nir_band].astype(float)

        # Avoid division by zero
        denominator = green + nir
        denominator[denominator == 0] = 1e-10

        ndwi = (green - nir) / denominator

        return ndwi


# Global instance
geotiff_processor = GeoTIFFProcessor()
