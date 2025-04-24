#!/usr/bin/env python3
import os, time, subprocess, statistics
import httpx

# --------------------------------------------
# Configuration
# --------------------------------------------
API = os.getenv("API_URL", "http://localhost:8000")
NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
REPEAT = 5  # Number of repetitions per scenario

# Prefixes must match those defined in your K8sResourceManager
SVC_PREFIX = "viz-svc-"
ING_PREFIX = "viz-ing-"

# --------------------------------------------
# Visualization deployment scenarios
# --------------------------------------------
SCENARIOS = {
    "jupyter": {
        "post_payload": {
            "name": "perf-jupyter-c",
            "label": "perf-jupyter-c",
            "base_url": "perf-jupyter-c",
            "needs_base_path": True,
            "target_port": 8888,
            "viz_type": "jupyter"
        },
        "label": "perf-jupyter-c"
    },
    "rshiny": {
        "post_payload": {
            "name": "perf-rshiny-c",
            "label": "perf-rshiny-c",
            "base_url": "perf-rshiny-c",
            "needs_base_path": False,
            "target_port": 3838,
            "viz_type": "rshiny"
        },
        "label": "perf-rshiny-c"
    }
}

# --------------------------------------------
# Wait until both svc and ingress are present
# --------------------------------------------
def wait_for_presence(label, timeout=60):
    svc = SVC_PREFIX + label
    ing = ING_PREFIX + label
    end = time.time() + timeout
    while time.time() < end:
        svc_ok = subprocess.run(
            ["kubectl", "get", "svc", svc, "-n", NAMESPACE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        ing_ok = subprocess.run(
            ["kubectl", "get", "ing", ing, "-n", NAMESPACE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        if svc_ok and ing_ok:
            return True
        time.sleep(1)
    return False

# --------------------------------------------
# Wait until both svc and ingress are deleted
# --------------------------------------------
def wait_for_absence(label, timeout=120):
    svc = SVC_PREFIX + label
    ing = ING_PREFIX + label
    end = time.time() + timeout
    while time.time() < end:
        svc_exists = subprocess.run(
            ["kubectl", "get", "svc", svc, "-n", NAMESPACE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        ing_exists = subprocess.run(
            ["kubectl", "get", "ing", ing, "-n", NAMESPACE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        if not svc_exists and not ing_exists:
            return True
        time.sleep(1)
    return False

# --------------------------------------------
# Measure how long it takes to clean up resources after deletion
# --------------------------------------------
def measure_cleanup(label, name, payload):
    # 1. Create visualization resource via POST
    r = httpx.post(f"{API}/visualizations", json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"POST failed: {r.status_code} {r.text}")

    # 2. Wait for resources to appear
    if not wait_for_presence(label):
        raise RuntimeError("Resources did not appear in time")

    # 3. Start timing
    t1 = time.time()

    # 4. Delete the visualization
    d = httpx.delete(f"{API}/visualizations",
                     params={"name": name, "label": label},
                     timeout=60)
    if d.status_code >= 400:
        raise RuntimeError(f"DELETE failed: {d.status_code} {d.text}")

    # 5. Wait for resources to be fully removed
    if not wait_for_absence(label):
        raise RuntimeError("Resources were not cleaned up in time")

    t2 = time.time()
    return (t2 - t1) * 1000  # Return time in milliseconds

# --------------------------------------------
# Main experiment runner
# --------------------------------------------
def main():
    print(f"Experiment C: Resource Cleanup Latency x {REPEAT}\n")
    for scen, cfg in SCENARIOS.items():
        print(f"-- Scenario: {scen} --")
        results = []
        for i in range(REPEAT):
            try:
                ms = measure_cleanup(
                    label=cfg["label"],
                    name=cfg["post_payload"]["name"],
                    payload=cfg["post_payload"]
                )
                print(f" [{i + 1}] cleanup latency: {ms:.1f} ms")
                results.append(ms)
            except Exception as e:
                print(f" [{i + 1}] ERROR: {e}")
            time.sleep(5)

        if results:
            avg = statistics.mean(results)
            p95 = statistics.quantiles(results, n=100)[94]
            print(f" → Avg {avg:.1f} ms | P95 {p95:.1f} ms | min {min(results):.1f} ms | max {max(results):.1f} ms\n")
        else:
            print(" → All failed, no valid data\n")

if __name__ == "__main__":
    main()