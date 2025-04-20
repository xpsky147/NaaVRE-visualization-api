from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import logging
from .services.k8s_service import K8sResourceManager
from .services.streamlit_service import streamlit_service

from .models.k8s_models import VisualizationRequest, VisualizationResponse
from .models.visualization_models import StreamlitVisualizationRequest, StreamlitVisualizationResponse
from .models.visualization_models import ScientificVisualizationRequest, DashboardVisualizationRequest

from fastapi.responses import FileResponse
import json
import asyncio

from datetime import datetime

app = FastAPI()
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)

k8s_manager = K8sResourceManager()

@app.post("/visualizations", response_model=VisualizationResponse)
async def create_visualization(request: VisualizationRequest):
    """
    Deploy a visualization service.
    This endpoint deploys a visualization application in Kubernetes and returns the access URL.
    Suitable for interactive and complex visualization scenarios.
    """
    try:
        logger.info(f"Received request to create visualization for workflow {request.name}")
        url = await k8s_manager.create_resources(
            request.name, 
            request.label, 
            request.base_url, 
            request.needs_base_path, 
            request.target_port,
            request.viz_type
        )
        return VisualizationResponse(visualization_url=url)
    except ValueError as e:
        logger.error(f"Bad Request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/visualizations")
async def delete_visualization(name: str, label: str):
    try:
        logger.info(f"Received request to delete visualization for workflow {name}")
        await k8s_manager.delete_resources(name, label)
        return {"detail": "Resource deleted successfully"}
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/visualizations/streamlit", response_model=StreamlitVisualizationResponse)
async def create_streamlit_visualization(request: StreamlitVisualizationRequest):
    """
    Create a Streamlit visualization.
    This endpoint passes data to the deployed Streamlit application and returns the access URL.
    Suitable for interactive visualization scenarios.
    """
    try:
        logger.info(f"Received request to create Streamlit visualization: {request.title}")
        result = await streamlit_service.create_visualization(
            title=request.title,
            chart_type=request.chart_type,
            data=request.data,
            layout=request.layout,
            options=request.options
        )
        return StreamlitVisualizationResponse(**result)
    except Exception as e:
        logger.error(f"Error creating Streamlit visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visualization/data/{viz_id}")
async def get_streamlit_visualization_data(viz_id: str):
    """
    Get Streamlit visualization data for use by the Streamlit application.
    """
    try:
        visualization_data = await streamlit_service.get_visualization_data(viz_id)
        return visualization_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Visualization data not found")
    except Exception as e:
        logger.error(f"Error retrieving visualization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/visualizations/scientific", response_model=StreamlitVisualizationResponse)
async def create_scientific_visualization(request: ScientificVisualizationRequest):
    """
    Create a scientific visualization.
    Supports scientific charts such as boxplot, violin plot, heatmap, correlation matrix, etc.
    """
    try:
        logger.info(f"Received request to create scientific visualization: {request.title}")
        result = await streamlit_service.create_scientific_visualization(
            title=request.title,
            chart_type=request.chart_type,
            data=request.data,
            layout=request.layout,
            options=request.options,
            metadata=request.metadata
        )
        return StreamlitVisualizationResponse(**result)
    except Exception as e:
        logger.error(f"Error creating scientific visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/visualizations/dashboard", response_model=StreamlitVisualizationResponse)
async def create_dashboard_visualization(request: DashboardVisualizationRequest):
    """
    Create a dashboard visualization.
    Allows combining multiple visualizations in a single view.
    """
    try:
        logger.info(f"Received request to create dashboard visualization: {request.title}")
        result = await streamlit_service.create_dashboard_visualization(
            title=request.title,
            data=request.data,
            options=request.options,
            metadata=request.metadata
        )
        return StreamlitVisualizationResponse(**result)
    except Exception as e:
        logger.error(f"Error creating dashboard visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))