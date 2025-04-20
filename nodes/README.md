# Node Library for Scientific Workflow Platform

This folder contains all the computational and service nodes used as building blocks in the platform's scientific workflows. Each node is implemented as a standalone script or container that performs a specific function, such as running simulations, registering visualizations, or exposing interactive services.

## Node Overview

| Node Name           | Description                                                    |
|---------------------|----------------------------------------------------------------|
| compute.py          | Simulates scientific experiments (e.g., heat transfer, signal analysis, fluid flow) and outputs results in JSON format. |
| main.py             | Integrates computation results and registers them with the Visualization API for interactive visualization. |
| create_viz.py       | Used in web/external tool workflows (e.g., Jupyter, RShiny, Streamlit) to dynamically register a running service with the Visualization API and expose it via Ingress. |
| cleaner.py          | Deregisters and cleans up visualization resources after workflow completion or failure. |

## Usage

- Each node is designed to be executed within a container as part of an Argo Workflow step.
- Input and output paths are passed as command-line arguments or environment variables.
- The nodes are stateless and exchange data via mounted volumes or API calls.

## Example

```bash
# Run a simulation node directly (for test)
python compute.py --type heat-transfer --params '{"grid_size":50,"time_steps":100}' --output ./results.json

# Register and visualize results
python main.py --input ./results.json --output ./visualization-url.txt --type scientific
```

## File List
compute.py – Scientific experiment simulation (JSON output)

main.py – Visualization registration and integration node

create_viz.py – Visualization API registration for running services (e.g. Jupyter/Streamlit)

cleaner.py – Visualization resource cleanup node

## Notes
Each node should be run in a compatible Python environment with the required dependencies installed (see requirements.txt if applicable).
For more details on parameters and output, refer to each script's docstrings or inline comments.