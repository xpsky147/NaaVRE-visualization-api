#!/usr/bin/env python3
"""
Node A - Scientific Computation Visualization Integrator

Reads scientific computation results and submits them to the Visualization API.
Supports types: scientific, dashboard, basic.
"""
import os
import sys
import json
import argparse
import requests
from datetime import datetime

# Configuration
API_URL = os.environ.get("API_URL", "http://visualization-api")
MAX_RETRIES = 5
WAIT_SECONDS = 2

def load_results(input_file):
    """Load scientific computation results from file."""
    print(f"Loading computation results: {input_file}")
    with open(input_file, 'r') as f:
        return json.load(f)

def create_visualization(data, viz_type):
    """Create a visualization using the Visualization API."""
    print(f"Creating visualization of type {viz_type}...")

    # Select API endpoint and prepare data
    if viz_type == "scientific":
        endpoint = "/visualizations/scientific"
        request_data = prepare_scientific_visualization(data)
    elif viz_type == "dashboard":
        endpoint = "/visualizations/dashboard"
        request_data = prepare_dashboard_visualization(data)
    else:
        endpoint = "/visualizations/streamlit"
        request_data = prepare_basic_visualization(data)

    # Retry logic for API call
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{API_URL}{endpoint}",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Visualization created: {result.get('visualization_url')}")
                return result
            else:
                print(f"Attempt {attempt+1} failed: API returned {response.status_code}")
                print(f"Response: {response.text}")

        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")

        if attempt < MAX_RETRIES - 1:
            import time
            print(f"Waiting {WAIT_SECONDS} seconds before retry...")
            time.sleep(WAIT_SECONDS)

    raise Exception(f"Visualization creation failed after {MAX_RETRIES} attempts")

def prepare_scientific_visualization(data):
    """Prepare payload for scientific visualization."""
    metadata = data.get("metadata", {})
    results = data.get("results", {})
    viz_hints = data.get("visualization_hints", {})

    # Determine chart type, default to "line"
    chart_type = "line"
    if "recommended_charts" in viz_hints:
        chart_type = viz_hints["recommended_charts"][0]

    experiment_type = metadata.get("experiment_type", "Experiment")

    # Handle different experiment result formats
    if "Heat Transfer" in experiment_type:
        # Heat transfer experiment - time vs temperature line chart
        if "time_series" in results:
            chart_data = {
                "x": [point["time"] for point in results["time_series"]],
                "y": [point["value"] for point in results["time_series"]]
            }
        else:
            chart_data = {
                "data": results.get("data_points", [])
            }

    elif "Signal Analysis" in experiment_type:
        # Signal analysis experiment
        if chart_type == "line" and "time_series" in results:
            chart_data = {
                "x": [point["time"] for point in results["time_series"]],
                "y": [point["value"] for point in results["time_series"]]
            }
        elif "frequency_data" in results:
            chart_type = "bar"
            chart_data = {
                "x": [point["frequency"] for point in results["frequency_data"]],
                "y": [point["power"] for point in results["frequency_data"]]
            }
        else:
            chart_data = {
                "data": results.get("data_points", [])
            }

    elif "Fluid Flow" in experiment_type:
        # Fluid flow experiment - scatter plot for vector field
        if "velocity_data" in results:
            chart_type = "scatter"
            chart_data = {
                "data": results["velocity_data"]
            }
        else:
            chart_data = {
                "data": results.get("data_points", [])
            }

    else:
        # Generic data format
        if "data_points" in results:
            chart_data = {
                "x": [point.get("x", i) for i, point in enumerate(results["data_points"])],
                "y": [point.get("y", 0) for point in results["data_points"]]
            }
        else:
            chart_data = {
                "data": []
            }

    # Build request payload
    return {
        "title": f"{experiment_type} Analysis Result",
        "chart_type": chart_type,
        "data": chart_data,
        "layout": {
            "title": f"{experiment_type} Analysis Result",
            "xaxis_title": viz_hints.get("x_axis", "X Value"),
            "yaxis_title": viz_hints.get("y_axis", "Y Value")
        },
        "metadata": metadata
    }

def prepare_dashboard_visualization(data):
    """Prepare payload for dashboard visualization (multiple charts)."""
    metadata = data.get("metadata", {})
    results = data.get("results", {})
    viz_hints = data.get("visualization_hints", {})
    experiment_type = metadata.get("experiment_type", "Experiment")
    charts = []

    # Time series chart if available
    if "time_series" in results:
        charts.append({
            "title": "Time Series Analysis",
            "type": "line",
            "data": {
                "x": [point["time"] for point in results["time_series"]],
                "y": [point["value"] for point in results["time_series"]]
            },
            "layout": {
                "title": "Time Trend",
                "xaxis_title": viz_hints.get("x_axis", "Time"),
                "yaxis_title": viz_hints.get("y_axis", "Value")
            }
        })

    # Data points scatter chart if available
    if "data_points" in results:
        charts.append({
            "title": "Data Points Distribution",
            "type": "scatter",
            "data": {
                "x": [point.get("x", i) for i, point in enumerate(results["data_points"])],
                "y": [point.get("y", point.get("temperature", 0)) for point in results["data_points"]]
            },
            "layout": {
                "title": "Distribution",
                "xaxis_title": "X Position",
                "yaxis_title": "Y Value"
            }
        })

    # Summary bar chart if available
    if "summary" in results:
        summary = results["summary"]
        summary_data = {
            "x": list(summary.keys()),
            "y": list(summary.values())
        }
        charts.append({
            "title": "Summary Statistics",
            "type": "bar",
            "data": summary_data,
            "layout": {
                "title": "Experiment Summary",
                "xaxis_title": "Metric",
                "yaxis_title": "Value"
            }
        })

    # Build dashboard layout
    return {
        "title": f"{experiment_type} Dashboard",
        "data": {
            "layout": {"rows": min(2, len(charts)), "cols": 2},
            "charts": charts
        },
        "metadata": metadata
    }

def prepare_basic_visualization(data):
    """Prepare payload for basic visualization (line or scatter)."""
    metadata = data.get("metadata", {})
    results = data.get("results", {})
    viz_hints = data.get("visualization_hints", {})
    experiment_type = metadata.get("experiment_type", "Experiment")

    if "time_series" in results:
        chart_type = "line"
        chart_data = {
            "x": [point["time"] for point in results["time_series"]],
            "y": [point["value"] for point in results["time_series"]]
        }
    elif "data_points" in results:
        chart_type = "scatter"
        chart_data = {
            "x": [point.get("x", i) for i, point in enumerate(results["data_points"])],
            "y": [point.get("y", 0) for point in results["data_points"]]
        }
    else:
        # Default fallback
        chart_type = "line"
        chart_data = {
            "x": [1, 2, 3, 4, 5],
            "y": [1, 2, 3, 2, 1]
        }

    return {
        "title": f"{experiment_type} Result",
        "chart_type": chart_type,
        "data": chart_data,
        "layout": {
            "title": f"{experiment_type} Result",
            "xaxis_title": viz_hints.get("x_axis", "X Value"),
            "yaxis_title": viz_hints.get("y_axis", "Y Value")
        }
    }

def save_result(output_file, result):
    """Save visualization URL to file, and save full result as JSON."""
    visualization_url = result.get("visualization_url", "")
    print(f"Saving visualization URL: {visualization_url}")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(visualization_url)

    # Save additional metadata as JSON
    result_json = {
        "visualization_url": visualization_url,
        "visualization_id": result.get("visualization_id", ""),
        "timestamp": datetime.now().isoformat(),
        "status": result.get("status", "")
    }
    json_file = f"{os.path.splitext(output_file)[0]}.json"
    with open(json_file, 'w') as f:
        json.dump(result_json, f, indent=2)

def main():
    """Main entry: parse arguments, load results, create visualization, save URL."""
    parser = argparse.ArgumentParser(description="Node A - Scientific Computation Visualization Integrator")
    parser.add_argument("--input", required=True, help="Input file (scientific computation result)")
    parser.add_argument("--output", required=True, help="Output file for visualization URL")
    parser.add_argument("--type", default="scientific",
                      choices=["basic", "scientific", "dashboard"],
                      help="Visualization type")

    args = parser.parse_args()

    try:
        data = load_results(args.input)
        result = create_visualization(data, args.type)
        save_result(args.output, result)
        print("Visualization creation completed successfully")
        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())