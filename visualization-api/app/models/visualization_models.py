from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class DataVisualizationRequest(BaseModel):
    name: str
    workflow_id: str
    visualization_type: str  # "line", "bar", "scatter", "heatmap"
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    config: Optional[Dict[str, Any]] = {}

class DataVisualizationResponse(BaseModel):
    visualization_id: str
    status: str
    visualization_url: Optional[str] = None
    error_message: Optional[str] = None
    message: Optional[str] = None

class StreamlitVisualizationRequest(BaseModel):
    title: str
    chart_type: str
    data: Dict[str, Any]
    layout: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None

class StreamlitVisualizationResponse(BaseModel):
    visualization_id: str
    status: str
    visualization_url: str
    message: str
    error_message: Optional[str] = None

class ScientificVisualizationRequest(BaseModel):
    title: str
    chart_type: str  # "boxplot", "violin", "heatmap", "correlation"
    data: Dict[str, Any]
    layout: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class DashboardVisualizationRequest(BaseModel):
    title: str
    data: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    