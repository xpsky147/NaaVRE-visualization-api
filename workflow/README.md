# Workflow Templates for Scientific Visualization Platform

This folder contains reusable Argo Workflow and WorkflowTemplate YAML files that describe complete scientific analysis and visualization pipelines. These workflows orchestrate multiple nodes to accomplish simulation, post-processing, and interactive visualization.

## Workflow Overview

| Workflow YAML                        | Description                                                                |
|--------------------------------------|----------------------------------------------------------------------------|
| scientific-visualization-workflow.yaml | Simulates a scientific experiment (e.g., heat transfer) and automatically visualizes the results using the Visualization API. |
| jupyter.yaml                         | Launches a Jupyter Notebook server, registers it via the Visualization API, and exposes it over Ingress for user access.    |
| rshiny-create-clean.yaml             | Similar to Jupyter, but launches an RShiny app and manages its lifecycle, including registration and cleanup. |

## Parameter Guide

Workflows in this folder typically use the following key parameters:

- **experiment-type**  
  Specifies the type of scientific experiment to run in the compute node (`compute.py`).  
  Common values include:
  - `heat-transfer` &nbsp;&nbsp;*// 1D/2D heat diffusion simulation*
  - `signal-analysis` &nbsp;&nbsp;*// Signal and frequency analysis*
  - `fluid-flow` &nbsp;&nbsp;*// Simple 2D fluid dynamics simulation*
  - *(You can extend with more types as supported by compute.py)*

- **experiment-params**  
  JSON-formatted string with parameters specific to the chosen experiment type.  

Example for `heat-transfer`:
```json
  {
    "grid_size": 50,
    "time_steps": 100,
    "diffusion_rate": 0.5
  }
```

Example for signal-analysis:
 ```json
  {
  "length": 100,
  "frequency": 1.0,
  "noise_level": 0.1
  }
```

(Refer to compute.py for supported parameter names for each experiment type.)

- **visualization-type**  
Controls how the results are visualized by the visualization integrator node (data-viz, i.e., main.py).
  - scientific   // For advanced scientific charts, e.g. line, scatter, boxplot
  - dashboard   // For a multi-panel dashboard view
  - basic   // For a simple single chart (line or scatter)

Example
``` yaml
# Example snippet for reference
- name: run-scientific-computation
  container:
    image: xpsky/scientific-computation:latest
    command: ["python", "/app/compute.py"]
    args: [
      "--type=heat-transfer",
      "--params={\"grid_size\":50,\"time_steps\":100}",
      "--output=/workdir/results.json"
    ]
- name: run-visualization
  container:
    image: xpsky/data-viz:latest
    command: ["python", "/app/main.py"]
    args: [
      "--input=/workdir/results.json",
      "--output=/workdir/visualization-url.txt",
      "--type=scientific"
    ]
```

## Usage
Each YAML describes a complete workflow and can be submitted with argo submit -n <namespace> <workflow.yaml>.

Parameters such as experiment type or visualization type can be customized as needed.

Results and visualization URLs are persisted in the shared volume.

## File List
scientific-visualization-workflow.yaml – Complete simulation and visualization pipeline

jupyter.yaml – Workflow to expose Jupyter Notebook as a service

rshiny-create-clean.yaml – Workflow for RShiny app exposure and lifecycle management
(Add others as necessary)

## Notes
These YAMLs require a working Argo Workflows installation and the referenced container images deployed to your Kubernetes cluster.
For more details on each step, see the inline comments in each YAML.