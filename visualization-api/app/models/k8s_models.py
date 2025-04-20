from pydantic import BaseModel
from typing import Optional

class VisualizationRequest(BaseModel):
    name: str
    label: str
    base_url: str = ""
    needs_base_path: bool = False
    target_port: int = 80
    viz_type: Optional[str] = "generic-web"

class VisualizationResponse(BaseModel):
    visualization_url: str