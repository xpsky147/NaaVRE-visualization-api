import os
import uuid
import json
from datetime import datetime
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StreamlitService:
    def __init__(self):
        # Data storage directory (use environment variable or default)
        self.data_dir = os.environ.get("STREAMLIT_DATA_DIR", "/data/api/streamlit_visualizations")
        os.makedirs(self.data_dir, exist_ok=True)

    async def create_visualization(
        self,
        title: str,
        chart_type: str,
        data: Dict[str, Any],
        layout: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Streamlit visualization and return access URL."""
        viz_id = str(uuid.uuid4())
        visualization_data = {
            "id": viz_id,
            "created_at": datetime.now().isoformat(),
            "title": title,
            "chart_type": chart_type,
            "data": data,
            "layout": layout or {},
            "options": options or {}
        }
        viz_dir = os.path.join(self.data_dir, viz_id)
        os.makedirs(viz_dir, exist_ok=True)

        try:
            data_path = os.path.join(viz_dir, "data.json")
            with open(data_path, "w") as f:
                json.dump(visualization_data, f)
            logger.info(f"Streamlit visualization data stored: {viz_id}")

            # Get Streamlit base URL from environment variable
            streamlit_url = os.environ.get("STREAMLIT_URL", "https://viz-test-visualization-api")
            visualization_url = f"{streamlit_url}/?id={viz_id}"

            return {
                "visualization_id": viz_id,
                "status": "ready",
                "visualization_url": visualization_url,
                "message": "Streamlit visualization created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating Streamlit visualization: {str(e)}")
            return {
                "visualization_id": viz_id,
                "status": "error",
                "error_message": str(e),
                "message": "Failed to create Streamlit visualization"
            }

    async def get_visualization_data(self, viz_id: str) -> Dict[str, Any]:
        """Get Streamlit visualization data."""
        data_path = os.path.join(self.data_dir, viz_id, "data.json")
        if not os.path.exists(data_path):
            logger.error(f"Streamlit visualization data not found: {viz_id}")
            raise FileNotFoundError(f"Streamlit visualization data not found: {viz_id}")

        try:
            with open(data_path, "r") as f:
                visualization_data = json.load(f)
            logger.info(f"Retrieved Streamlit visualization data: {viz_id}")
            return visualization_data
        except Exception as e:
            logger.error(f"Error retrieving Streamlit visualization data: {str(e)}")
            raise RuntimeError(f"Error retrieving Streamlit visualization data: {str(e)}")

    async def create_scientific_visualization(
        self,
        title: str,
        chart_type: str,
        data: Dict[str, Any],
        layout: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a scientific visualization and return access URL."""
        viz_id = str(uuid.uuid4())
        visualization_data = {
            "id": viz_id,
            "created_at": datetime.now().isoformat(),
            "title": title,
            "chart_type": chart_type,
            "data": data,
            "layout": layout or {},
            "options": options or {},
            "metadata": metadata or {}
        }
        viz_dir = os.path.join(self.data_dir, viz_id)
        os.makedirs(viz_dir, exist_ok=True)

        try:
            data_path = os.path.join(viz_dir, "data.json")
            with open(data_path, "w") as f:
                json.dump(visualization_data, f)
            logger.info(f"Scientific visualization data stored: {viz_id}")

            streamlit_url = os.environ.get("STREAMLIT_URL", "https://viz-test-visualization-api")
            visualization_url = f"{streamlit_url}/?id={viz_id}"

            return {
                "visualization_id": viz_id,
                "status": "ready",
                "visualization_url": visualization_url,
                "message": "Scientific visualization created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating scientific visualization: {str(e)}")
            return {
                "visualization_id": viz_id,
                "status": "error",
                "error_message": str(e),
                "message": "Failed to create scientific visualization"
            }

    async def create_dashboard_visualization(
        self,
        title: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a dashboard visualization and return access URL."""
        viz_id = str(uuid.uuid4())
        visualization_data = {
            "id": viz_id,
            "created_at": datetime.now().isoformat(),
            "title": title,
            "chart_type": "dashboard",
            "data": data,
            "options": options or {},
            "metadata": metadata or {}
        }
        viz_dir = os.path.join(self.data_dir, viz_id)
        os.makedirs(viz_dir, exist_ok=True)

        try:
            data_path = os.path.join(viz_dir, "data.json")
            with open(data_path, "w") as f:
                json.dump(visualization_data, f)
            logger.info(f"Dashboard visualization data stored: {viz_id}")

            streamlit_url = os.environ.get("STREAMLIT_URL", "https://viz-test-visualization-api")
            visualization_url = f"{streamlit_url}/?id={viz_id}"

            return {
                "visualization_id": viz_id,
                "status": "ready",
                "visualization_url": visualization_url,
                "message": "Dashboard visualization created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating dashboard visualization: {str(e)}")
            return {
                "visualization_id": viz_id,
                "status": "error",
                "error_message": str(e),
                "message": "Failed to create dashboard visualization"
            }

# Create service instance
streamlit_service = StreamlitService()