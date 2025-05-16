#!/usr/bin/env python3
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
import random

def simulate_experiment(experiment_type, params):
    """Simulate a scientific experiment by type and parameters."""
    print(f"Running experiment: {experiment_type}")
    params = json.loads(params) if isinstance(params, str) else params

    if experiment_type == "heat-transfer":
        return simulate_heat_transfer(params)
    elif experiment_type == "signal-analysis":
        return simulate_signal_analysis(params)
    elif experiment_type == "fluid-flow":
        return simulate_fluid_flow(params)
    else:
        return simulate_default_experiment(params)

def simulate_heat_transfer(params):
    """Simulate a heat transfer experiment (simple exponential decay)."""
    grid_size = params.get("grid_size", 50)
    time_steps = params.get("time_steps", 100)
    diffusion_rate = params.get("diffusion_rate", 0.5)

    # Generate temperature time series (average temperature decay)
    time_series = []
    for t in range(0, time_steps+1, 5):
        avg_temp = 100 * np.exp(-t * diffusion_rate / time_steps)
        avg_temp += random.uniform(-2, 2)
        time_series.append({"time": t, "value": avg_temp})

    # Generate scattered grid data points
    data_points = []
    for i in range(10):
        for j in range(10):
            temp = 100 * np.exp(-(i+j)/18) + random.uniform(-5, 5)
            data_points.append({
                "x": i,
                "y": j,
                "temperature": temp
            })

    return {
        "metadata": {
            "experiment_type": "Heat Transfer Experiment",
            "timestamp": datetime.now().isoformat(),
            "parameters": params
        },
        "results": {
            "summary": {
                "initial_temperature": time_series[0]["value"],
                "final_temperature": time_series[-1]["value"],
                "cooling_rate": diffusion_rate
            },
            "time_series": time_series,
            "data_points": data_points
        },
        "visualization_hints": {
            "recommended_charts": ["line"],
            "x_axis": "Time (s)",
            "y_axis": "Temperature (°C)"
        }
    }

def simulate_signal_analysis(params):
    """Simulate a signal analysis experiment (sine wave with noise)."""
    frequency = params.get("frequency", 10)  # Hz
    duration = params.get("duration", 2)     # seconds
    noise_level = params.get("noise_level", 0.2)

    sampling_rate = 1000  # Hz
    t = np.linspace(0, duration, int(sampling_rate * duration))
    signal = np.sin(2 * np.pi * frequency * t)
    signal += np.random.normal(0, noise_level, signal.shape)

    from scipy import fftpack
    sig_fft = fftpack.fft(signal)
    power = np.abs(sig_fft)**2
    sample_freq = fftpack.fftfreq(signal.size, d=1/sampling_rate)

    mask = sample_freq > 0
    freqs = sample_freq[mask]
    power = power[mask]

    time_series = [{"time": float(t[i]), "value": float(signal[i])}
                  for i in range(0, len(t), 10)]  # Downsample for less data
    frequency_data = [{"frequency": float(freqs[i]), "power": float(power[i])}
                     for i in range(min(100, len(freqs)))]

    return {
        "metadata": {
            "experiment_type": "Signal Analysis Experiment",
            "timestamp": datetime.now().isoformat(),
            "parameters": params
        },
        "results": {
            "summary": {
                "input_frequency": frequency,
                "duration": duration,
                "noise_level": noise_level,
                "detected_frequency": float(freqs[np.argmax(power)])
            },
            "time_series": time_series,
            "frequency_data": frequency_data
        },
        "visualization_hints": {
            "recommended_charts": ["line", "bar"],
            "x_axis": "Time (s)",
            "y_axis": "Amplitude"
        }
    }

def simulate_fluid_flow(params):
    """Simulate a fluid flow experiment (simple 2D velocity field)."""
    reynolds = params.get("reynolds", 1000)
    grid_points = params.get("grid_points", 20)

    x = np.linspace(0, 1, grid_points)
    y = np.linspace(0, 1, grid_points)
    X, Y = np.meshgrid(x, y)

    # Parabolic profile with random noise
    u = 4 * Y * (1 - Y) + np.random.normal(0, 0.05, (grid_points, grid_points))
    v = np.random.normal(0, 0.02, (grid_points, grid_points))

    velocity_data = []
    for i in range(grid_points):
        for j in range(grid_points):
            velocity_data.append({
                "x": float(X[i, j]),
                "y": float(Y[i, j]),
                "u": float(u[i, j]),
                "v": float(v[i, j]),
                "speed": float(np.sqrt(u[i, j]**2 + v[i, j]**2))
            })

    return {
        "metadata": {
            "experiment_type": "Fluid Flow Experiment",
            "timestamp": datetime.now().isoformat(),
            "parameters": params
        },
        "results": {
            "summary": {
                "reynolds_number": reynolds,
                "max_velocity": float(np.max(np.sqrt(u**2 + v**2))),
                "avg_velocity": float(np.mean(np.sqrt(u**2 + v**2)))
            },
            "velocity_data": velocity_data
        },
        "visualization_hints": {
            "recommended_charts": ["scatter", "line"],
            "x_axis": "X Position",
            "y_axis": "Y Position"
        }
    }

def simulate_default_experiment(params):
    """Default experiment simulation: generates random data points."""
    data_points = []
    for i in range(100):
        data_points.append({
            "x": i,
            "y": 50 + 25 * np.sin(i/10) + random.uniform(-10, 10)
        })

    return {
        "metadata": {
            "experiment_type": "Generic Experiment",
            "timestamp": datetime.now().isoformat(),
            "parameters": params
        },
        "results": {
            "data_points": data_points
        },
        "visualization_hints": {
            "recommended_charts": ["line", "scatter"],
            "x_axis": "X Value",
            "y_axis": "Y Value"
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Scientific experiment simulator")
    parser.add_argument("--type", required=False, help="Experiment type")
    parser.add_argument("--params", required=False, help="Parameters as JSON string")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--input", required=False, help="Input CSV file")

    args = parser.parse_args()

    try:
        if args.input:  # 如果指定了 input，走 CSV 分析分支
            df = pd.read_csv(args.input)
            # 自动识别类别列
            species_col = None
            for col in df.columns:
                if col.lower() in ["species", "class", "target"]:
                    species_col = col
                    break
            if not species_col:
                raise ValueError("CSV文件中未找到 species/class/target 列")
            # 计算各类别的各特征均值
            mean_values = df.groupby(species_col).mean(numeric_only=True)
            feature_means_points = []
            for feature in mean_values.columns:
                for species in mean_values.index:
                    feature_means_points.append({
                        "feature": feature,
                        "species": species,
                        "mean": mean_values.loc[species, feature]
                    })
            # 构建输出结果，推荐 bar 分组柱状图
            result = {
                "metadata": {
                    "experiment_type": "Iris Data Analysis",
                    "parameters": {}
                },
                "results": {
                    "feature_means_points": feature_means_points
                },
                "visualization_hints": {
                    "recommended_charts": ["bar"],
                    "x_axis": "feature",
                    "y_axis": "mean",
                    "color": "species"
                }
            }
        else:  # 没有input，保持原有仿真
            result = simulate_experiment(args.type, args.params)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Computation finished, result saved to: {args.output}")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())