from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .services.k8s_service import create_k8s_resources, delete_k8s_resources
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualizationRequest(BaseModel):
    name: str

class VisualizationResponse(BaseModel):
    visualization_url: str


@app.post("/visualization_ingress_service", response_model=VisualizationResponse)
async def create_visualization(request: VisualizationRequest):
    try:
        logger.info(f"Received request to create visualization for {request.name}")
        url = create_k8s_resources(request.name)
        return VisualizationResponse(visualization_url=url)
    except ValueError as e:
        logger.error(f"Bad Request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/visualization_ingress_service")
async def delete_visualization(id: str):
    try:
        logger.info(f"Received request to delete visualization for {id}")
        delete_k8s_resources(id)
        return {"detail": "Resource deleted successfully"}
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))