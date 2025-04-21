# Node Library for Scientific Workflow Platform

This folder contains all the computational and service nodes used as building blocks in the platform's scientific workflows. Each node is implemented as a standalone script or container that performs a specific function, such as running simulations, registering visualizations, or exposing interactive services.

## Node Overview

| Node Name             | Description                                                    |
|-----------------------|----------------------------------------------------------------|
| scientific-computation| Simulates scientific experiments (e.g., heat transfer, signal analysis, fluid flow) and outputs results in JSON format. |
| data-viz              | Integrates computation results and registers them with the Visualization API for interactive visualization. |
| create                | Used in web/external tool workflows (e.g., Jupyter, RShiny, Streamlit) to dynamically register a running service with the Visualization API and expose it via Ingress. |
| clean                 | Deregisters and cleans up visualization resources after workflow completion or failure. |
| streamlit             | Streamlit app for rendering experiment results. |


## Usage

- Each node is designed to be executed within a container as part of an Argo Workflow step.
- Input and output paths are passed as command-line arguments or environment variables.
- The nodes are stateless and exchange data via mounted volumes or API calls.

### Deploy Streamlit
```bash
kubectl apply -f streamlit-deployment-simple.yaml
```

## File List
compute.py – Scientific experiment simulation (JSON output)

main.py – Visualization registration and integration node

create_viz.py – Visualization API registration for running services (e.g. Jupyter/Streamlit)

cleaner.py – Visualization resource cleanup node

viz_app.py - Main Streamlit app for rendering experiment results

## Notes
Each node should be run in a compatible Python environment with the required dependencies installed (see requirements.txt if applicable).
For more details on parameters and output, refer to each script's docstrings or inline comments.

The app expects result data in JSON format, usually mounted at /workdir/results.json or fetched from an API.
Adjust API endpoints or paths in viz_app.py as needed for your workflow.

---

