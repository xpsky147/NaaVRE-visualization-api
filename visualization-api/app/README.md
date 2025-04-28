# Visualization API

A FastAPI-based microservice for deploying and managing scientific and dashboard visualizations on Kubernetes.

## What is this service for?

- **Expose your visualization or data analysis tools as a web service on Kubernetes** (Jupyter, RShiny, etc).
- **Generate interactive visualizations from data directly via API**, and share them via generated URLs.

## Requirements

- Python 3.12
- Docker (for container builds)
- Kubernetes cluster (for deployment)
- Helm (for deployment via Helm charts)
- Tilt (for local development, optional)

### Python dependencies

All dependencies are pinned in `requirements.txt`:

```text
fastapi==0.111.1
PyJWT[crypto]==2.8.0
requests==2.32.3
uvicorn==0.29.0
pydantic==2.7.1
kubernetes==29.0.0
```

## Local Development and Deployment (with Tilt)

This API is designed to be deployed as part of the NaaVRE platform using [Tilt](https://tilt.dev/).

## API Endpoints
- POST /visualizations — Deploy a visualization service
- DELETE /visualizations — Delete a visualization service
- POST /visualizations/streamlit — Create Streamlit visualization
- POST /visualizations/scientific — Create scientific visualization
- POST /visualizations/dashboard — Create dashboard visualization
- GET /api/visualization/data/{viz_id} — Get visualization data
- GET /healthz — Health check

## Quick Start (Local Development)

1. Clone repo and enter directory.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set required environment variables, e.g.:
```bash
export INGRESS_DOMAIN=localhost
export STREAMLIT_URL=http://localhost:8501
```
4. Launch server:
```bash
uvicorn visualization-api.main:app --host 0.0.0.0 --port 80
```

5. Visit http://localhost:8000/docs for interactive API docs.


## Data Storage
All visualization data is stored under STREAMLIT_DATA_DIR (default /data/api/streamlit_visualizations).
Each visualization has a unique UUID directory and a data.json file.

## Extending the API
Add new endpoints or visualization logic in visualization-api/ and services/.
Data models are in models/.

## Common Issues
Environment variable not set: Make sure INGRESS_DOMAIN and STREAMLIT_URL are set.

Kubernetes resource errors: Check your K8s cluster access and RBAC.

Data lost after restart: Use a PersistentVolume for STREAMLIT_DATA_DIR in production.

## Environment Variables
- K8S_NAMESPACE (default: default)
- INGRESS_DOMAIN (required)
- STREAMLIT_URL (default: http://viz.naavre.example.com)

## Integration with NaaVRE
This service is a component in the NaaVRE platform. For full workflow orchestration, see NaaVRE documentation.