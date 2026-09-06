"""
Gemini VQA Model - Uses Google Gemini API for advanced visual question answering
Falls back to color-based VQA if API is unavailable
"""

from pathlib import Path
from PIL import Image
import numpy as np
import base64
import io
import os

# Try to import google.generativeai, but don't fail if not available
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Using fallback VQA model.")


class GeminiVQAModel:
    """
    Advanced VQA model using Google Gemini API.
    Falls back to color-based analysis if API is unavailable.
    """

    def __init__(self):
        self.model_name = "Gemini Vision VQA"
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.use_gemini = GEMINI_AVAILABLE and self.api_key is not None

        if self.use_gemini:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
                print("✓ Gemini VQA model initialized")
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini: {e}")
                self.use_gemini = False
        else:
            print("Using fallback color-based VQA model")

    async def analyze(self, query: str, image_path: str) -> dict:
        """Analyze satellite image and answer query"""

        if self.use_gemini:
            return await self._analyze_with_gemini(query, image_path)
        else:
            return await self._analyze_with_color(query, image_path)

    async def _analyze_with_gemini(self, query: str, image_path: str) -> dict:
        """Use Gemini API for analysis"""
        try:
            # Load and encode image
            image = Image.open(image_path)

            # Create prompt for satellite image analysis
            prompt = f"""You are a remote sensing expert analyzing a satellite image. 
            Answer the following question about this satellite imagery:
            
            Question: {query}
            
            Provide a detailed, technical answer focusing on:
            - Land cover types visible (water, vegetation, urban, bare soil, etc.)
            - Spatial patterns and distributions
            - Any notable features or changes
            - Approximate coverage percentages if relevant
            
            Be specific and use remote sensing terminology where appropriate."""

            # Generate response
            response = self.model.generate_content([prompt, image])
            answer = response.text

            # Calculate confidence based on response quality
            confidence = self._calculate_gemini_confidence(answer)

            return {
                "answer": answer,
                "confidence": confidence,
                "evidence_images": [],
                "model_used": "Gemini Vision",
            }

        except Exception as e:
            print(f"Gemini API error: {e}")
            # Fallback to color-based analysis
            return await self._analyze_with_color(query, image_path)

    async def _analyze_with_color(self, query: str, image_path: str) -> dict:
        """Fallback: Color-based analysis"""
        from app.models.vqa import VQAModel

        fallback_model = VQAModel()
        result = await fallback_model.analyze(query, image_path)
        result["model_used"] = "Color-based VQA (Fallback)"
        return result

    def _calculate_gemini_confidence(self, answer: str) -> float:
        """Calculate confidence based on response characteristics"""
        # Base confidence for Gemini responses
        confidence = 0.85

        # Increase confidence for detailed responses
        if len(answer) > 200:
            confidence += 0.05
        if len(answer) > 500:
            confidence += 0.03

        # Increase confidence if percentages are mentioned
        if "%" in answer:
            confidence += 0.02

        # Increase confidence if technical terms are used
        technical_terms = [
            "vegetation",
            "urban",
            "water body",
            "land cover",
            "spectral",
            "spatial",
            "resolution",
            "sensor",
        ]
        for term in technical_terms:
            if term.lower() in answer.lower():
                confidence += 0.01
                break

        return min(confidence, 0.95)
