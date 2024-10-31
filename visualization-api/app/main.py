from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from .services.k8s_service import K8sResourceManager
import asyncio

app = FastAPI()
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)

class VisualizationRequest(BaseModel):
    name: str
    base_url: str

class VisualizationResponse(BaseModel):
    visualization_url: str

k8s_manager = K8sResourceManager()

@app.post("/visualizations", response_model=VisualizationResponse)
async def create_visualization(request: VisualizationRequest):
    try:
        logger.info(f"Received request to create visualization for workflow {request.name}")
        url = await k8s_manager.create_resources(request.name, request.base_url)  # 加上 await
        return VisualizationResponse(visualization_url=url)
    except ValueError as e:
        logger.error(f"Bad Request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/visualizations")
async def delete_visualization(name: str, base_url: str):
    try:
        logger.info(f"Received request to delete visualization for workflow {name}")
        await k8s_manager.delete_resources(name, base_url)
        return {"detail": "Resource deleted successfully"}
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))