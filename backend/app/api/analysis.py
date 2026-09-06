from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List
import base64
import io

from app.agent.controller import SatQueryAgent
from app.evaluation.metrics import evaluation_metrics

router = APIRouter()


class AnalysisRequest(BaseModel):
    query: str
    image_paths: list[str]
    sensor_types: Optional[list[str]] = None
    chat_history: Optional[list[dict]] = None


class AnalysisResponse(BaseModel):
    success: bool
    task_type: str
    answer: str
    confidence: float
    evidence_images: list[dict]
    execution_trace: list[dict]
    model_used: Optional[str] = None
    response_time: Optional[float] = None
    chat_history: Optional[list[dict]] = None


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """Main analysis endpoint - routes to appropriate tool based on query"""

    # Validate inputs
    if not request.image_paths:
        raise HTTPException(status_code=400, detail="No images provided")

    for img_path in request.image_paths:
        if not Path(img_path).exists():
            raise HTTPException(status_code=404, detail=f"Image not found: {img_path}")

    # Initialize agent
    agent = SatQueryAgent()

    try:
        # Run analysis
        result = await agent.process_query(
            query=request.query,
            image_paths=request.image_paths,
            sensor_types=request.sensor_types,
            chat_history=request.chat_history,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/tasks")
async def get_supported_tasks():
    """Return list of supported analysis tasks"""
    return {
        "tasks": [
            {
                "id": "vqa",
                "name": "Visual Question Answering",
                "description": "Answer questions about a single satellite image",
                "example": "What is visible in this image?",
                "model": "Gemini Vision VQA",
            },
            {
                "id": "grounding",
                "name": "Text-Guided Grounding",
                "description": "Locate and highlight specific objects/regions",
                "example": "Highlight the water body",
                "model": "Text-Guided Grounding Model",
            },
            {
                "id": "change_detection",
                "name": "Bi-Temporal Change Detection",
                "description": "Analyze changes between two images from different dates",
                "example": "What changed between these two images?",
                "model": "Bi-Temporal Change Detection Model",
            },
            {
                "id": "optical_sar",
                "name": "Optical + SAR Fusion",
                "description": "Combined analysis of optical and SAR imagery",
                "example": "Use both images to identify built-up regions",
                "model": "Optical-SAR Fusion Model",
            },
        ]
    }


@router.get("/evaluation")
async def get_evaluation_metrics():
    """Return model evaluation metrics"""
    return evaluation_metrics.get_metrics()


@router.get("/evaluation/{task_type}")
async def get_task_evaluation(task_type: str):
    """Return evaluation metrics for a specific task"""
    metrics = evaluation_metrics.get_task_metrics(task_type)
    if not metrics:
        raise HTTPException(
            status_code=404, detail=f"Task type '{task_type}' not found"
        )
    return metrics
