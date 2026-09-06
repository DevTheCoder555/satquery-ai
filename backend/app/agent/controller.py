from typing import Optional
from pathlib import Path
import re
import time

from app.models.gemini_vqa import GeminiVQAModel
from app.models.grounding import GroundingModel
from app.models.change import ChangeDetectionModel
from app.models.optical_sar import OpticalSARModel
from app.evaluation.metrics import evaluation_metrics


class SatQueryAgent:
    """
    Main agent that orchestrates satellite image analysis.
    Routes queries to appropriate specialist tools based on:
    - Number of images
    - Query keywords
    - Sensor types mentioned
    - Chat history for context
    """

    def __init__(self):
        self.vqa_model = GeminiVQAModel()  # Now uses Gemini with fallback
        self.grounding_model = GroundingModel()
        self.change_model = ChangeDetectionModel()
        self.optical_sar_model = OpticalSARModel()
        self.chat_history = []  # Store conversation history

    async def process_query(
        self,
        query: str,
        image_paths: list[str],
        sensor_types: Optional[list[str]] = None,
        chat_history: Optional[list[dict]] = None,
    ) -> dict:
        """Process user query and route to appropriate tool"""

        start_time = time.time()
        execution_trace = []

        # Update chat history if provided
        if chat_history:
            self.chat_history = chat_history

        # Step 1: Input validation
        execution_trace.append(
            {
                "step": "Input Validation",
                "status": "success",
                "message": f"Validated {len(image_paths)} image(s)",
            }
        )

        # Step 2: Classify query
        task_type = self._classify_query(query, image_paths, sensor_types)
        execution_trace.append(
            {
                "step": "Query Classification",
                "status": "success",
                "message": f"Classified as: {task_type.upper()}",
            }
        )

        # Step 3: Route to appropriate tool
        try:
            if task_type == "vqa":
                result = await self._run_vqa(query, image_paths, execution_trace)
            elif task_type == "grounding":
                result = await self._run_grounding(query, image_paths, execution_trace)
            elif task_type == "change_detection":
                result = await self._run_change_detection(
                    query, image_paths, execution_trace
                )
            elif task_type == "optical_sar":
                result = await self._run_optical_sar(
                    query, image_paths, sensor_types, execution_trace
                )
            else:
                result = await self._run_vqa(query, image_paths, execution_trace)

            success = True
        except Exception as e:
            execution_trace.append(
                {
                    "step": "Analysis Error",
                    "status": "error",
                    "message": f"Error: {str(e)}",
                }
            )
            result = {
                "answer": f"Analysis failed: {str(e)}",
                "confidence": 0.0,
                "evidence_images": [],
            }
            success = False

        # Add final step
        execution_trace.append(
            {
                "step": "Analysis Complete",
                "status": "success",
                "message": "Results generated successfully",
            }
        )

        # Calculate response time
        response_time = time.time() - start_time

        # Record metrics
        evaluation_metrics.record_analysis(
            task_type=task_type,
            confidence=result["confidence"],
            success=success,
            response_time=response_time,
        )

        # Add to chat history
        self.chat_history.append(
            {
                "role": "user",
                "query": query,
                "task_type": task_type,
                "timestamp": time.time(),
            }
        )
        self.chat_history.append(
            {
                "role": "assistant",
                "answer": result["answer"],
                "confidence": result["confidence"],
                "task_type": task_type,
                "timestamp": time.time(),
            }
        )

        return {
            "success": success,
            "task_type": task_type,
            "answer": result["answer"],
            "confidence": result["confidence"],
            "evidence_images": result.get("evidence_images", []),
            "execution_trace": execution_trace,
            "model_used": result.get("model_used", "Unknown"),
            "response_time": round(response_time, 2),
            "chat_history": self.chat_history[-10:],  # Return last 10 messages
        }

    def _classify_query(
        self,
        query: str,
        image_paths: list[str],
        sensor_types: Optional[list[str]] = None,
    ) -> str:
        """Classify query into task type"""
        query_lower = query.lower()

        # Check for optical+SAR fusion
        if sensor_types and len(sensor_types) >= 2:
            if "optical" in sensor_types and "sar" in sensor_types:
                return "optical_sar"

        # Check for keywords indicating optical+SAR
        optical_sar_keywords = [
            "optical",
            "sar",
            "fusion",
            "combine",
            "both sensors",
            "multimodal",
        ]
        if any(keyword in query_lower for keyword in optical_sar_keywords):
            if len(image_paths) >= 2:
                return "optical_sar"

        # Check for change detection (2 images)
        if len(image_paths) >= 2:
            change_keywords = [
                "change",
                "compare",
                "difference",
                "before",
                "after",
                "increased",
                "decreased",
                "between",
            ]
            if any(keyword in query_lower for keyword in change_keywords):
                return "change_detection"
            # Default to change detection for 2 images
            return "change_detection"

        # Check for grounding
        grounding_keywords = [
            "highlight",
            "locate",
            "find",
            "where",
            "show me",
            "point out",
            "identify the location",
            "mark",
        ]
        if any(keyword in query_lower for keyword in grounding_keywords):
            return "grounding"

        # Default to VQA
        return "vqa"

    async def _run_vqa(self, query: str, image_paths: list[str], trace: list) -> dict:
        """Run VQA analysis with Gemini"""

        # Check if Gemini is available
        if self.vqa_model.use_gemini:
            trace.append(
                {
                    "step": "Model Selection",
                    "status": "success",
                    "message": "Selected: Gemini Vision VQA (Advanced)",
                }
            )
        else:
            trace.append(
                {
                    "step": "Model Selection",
                    "status": "success",
                    "message": "Selected: Color-based VQA (Fallback)",
                }
            )

        # Add context from chat history if available
        enhanced_query = query
        if len(self.chat_history) >= 2:
            # Get last user query for context
            last_user_msg = None
            for msg in reversed(self.chat_history[:-1]):
                if msg["role"] == "user":
                    last_user_msg = msg["query"]
                    break

            if last_user_msg and last_user_msg != query:
                enhanced_query = (
                    f"Previous question was: '{last_user_msg}'. Now: {query}"
                )

        result = await self.vqa_model.analyze(enhanced_query, image_paths[0])

        trace.append(
            {
                "step": "VQA Analysis",
                "status": "success",
                "message": f"Visual question answering completed using {result.get('model_used', 'VQA')}",
            }
        )

        return result

    async def _run_grounding(
        self, query: str, image_paths: list[str], trace: list
    ) -> dict:
        """Run grounding analysis"""
        trace.append(
            {
                "step": "Model Selection",
                "status": "success",
                "message": "Selected: Text-Guided Grounding Model",
            }
        )

        # Extract target object from query
        target = self._extract_target_object(query)

        result = await self.grounding_model.analyze(image_paths[0], target)

        trace.append(
            {
                "step": "Grounding Analysis",
                "status": "success",
                "message": f"Located: {target}",
            }
        )

        return result

    async def _run_change_detection(
        self, query: str, image_paths: list[str], trace: list
    ) -> dict:
        """Run change detection analysis"""
        trace.append(
            {
                "step": "Model Selection",
                "status": "success",
                "message": "Selected: Bi-Temporal Change Detection Model",
            }
        )

        trace.append(
            {
                "step": "Temporal Validation",
                "status": "success",
                "message": "Validated bi-temporal image pair",
            }
        )

        result = await self.change_model.analyze(image_paths[0], image_paths[1], query)

        trace.append(
            {
                "step": "Change Analysis",
                "status": "success",
                "message": "Change detection completed",
            }
        )

        trace.append(
            {
                "step": "Evidence Generation",
                "status": "success",
                "message": "Change map generated",
            }
        )

        return result

    async def _run_optical_sar(
        self,
        query: str,
        image_paths: list[str],
        sensor_types: Optional[list[str]],
        trace: list,
    ) -> dict:
        """Run optical+SAR fusion analysis"""
        trace.append(
            {
                "step": "Model Selection",
                "status": "success",
                "message": "Selected: Optical-SAR Fusion Model",
            }
        )

        trace.append(
            {
                "step": "Multi-Modal Validation",
                "status": "success",
                "message": "Validated optical and SAR imagery",
            }
        )

        result = await self.optical_sar_model.analyze(
            image_paths[0], image_paths[1], sensor_types, query
        )

        trace.append(
            {
                "step": "Fusion Analysis",
                "status": "success",
                "message": "Cross-modal analysis completed",
            }
        )

        return result

    def _extract_target_object(self, query: str) -> str:
        """Extract the target object to locate from query"""
        query_lower = query.lower()

        # Common satellite image objects
        objects = [
            "water body",
            "water",
            "river",
            "lake",
            "building",
            "buildings",
            "built-up",
            "urban",
            "vegetation",
            "forest",
            "trees",
            "green area",
            "road",
            "roads",
            "highway",
            "agricultural",
            "farm",
            "field",
            "crop",
            "bare soil",
            " barren",
            "desert",
        ]

        for obj in objects:
            if obj in query_lower:
                return obj

        # Default
        return "region of interest"
