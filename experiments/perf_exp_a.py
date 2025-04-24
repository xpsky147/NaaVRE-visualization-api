#!/usr/bin/env python3
import os, asyncio, time, httpx, subprocess

# --------------------------------------------
# Configuration
# --------------------------------------------
API = os.getenv("API_URL", "http://localhost:8000")
NAMESPACE = os.getenv("K8S_NAMESPACE", "default")

SCENARIOS = {
    "jupyter": {
        "endpoint": "/visualizations",
        "payload": {
            "name": "perf-jupyter",
            "label": "perf-jupyter",
            "base_url": "perf-jupyter",
            "needs_base_path": True,
            "target_port": 8888,
            "viz_type": "jupyter"
        },
        # Used for kubectl selector and DELETE API
        "label": "perf-jupyter"
    },
    "rshiny": {
        "endpoint": "/visualizations",
        "payload": {
            "name": "perf-rshiny",
            "label": "perf-rshiny",
            "base_url": "perf-rshiny",
            "needs_base_path": False,
            "target_port": 3838,
            "viz_type": "rshiny"
        },
        "label": "perf-rshiny"
    },
    "scientific": {
        "endpoint": "/visualizations/scientific",
        "payload": {
            "title": "perf-scientific",
            "chart_type": "line",
            "data": {"x": [1, 2, 3], "y": [1, 4, 9]},
            "layout": {}, "options": {}, "metadata": {}
        },
        # The scientific scenario does not create Service/Ingress and does not require deletion
        "label": None
    }
}

# --------------------------------------------
# Send a single POST request and measure latency
# --------------------------------------------
async def single_request(endpoint, payload):
    async with httpx.AsyncClient(base_url=API, timeout=20.0) as client:
        t0 = time.time()
        r = await client.post(endpoint, json=payload)
        t1 = time.time()
        return (t1 - t0) * 1000, r.status_code

# --------------------------------------------
# DELETE request via API
# --------------------------------------------
async def api_delete(name, label):
    async with httpx.AsyncClient(base_url=API, timeout=30.0) as client:
        # Note: your DELETE endpoint is /visualizations?name=…&label=…
        r = await client.delete(f"/visualizations?name={name}&label={label}")
    return r.status_code

# --------------------------------------------
# Polling to ensure K8s resources are fully cleaned up
# --------------------------------------------
def wait_cleanup(label, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        out = subprocess.run([
            "kubectl", "get", "svc,ing",
            "-n", NAMESPACE,
            "-l", f"workflows.argoproj.io/workflow={label}"
        ], capture_output=True, text=True).stdout
        # Exit if no resources are found
        if not out.strip() or "No resources found" in out:
            return True
        time.sleep(1)
    return False

# --------------------------------------------
# Cold/Warm startup test for a given scenario
# --------------------------------------------
async def run_scenario(name, cfg, N=5, delete_before=False):
    print(f"\n-- Scenario: {name} | delete_before={delete_before} --")
    lbl = cfg.get("label")
    # Only delete if label is specified
    if delete_before and lbl:
        code = await api_delete(cfg["payload"].get("name", ""), lbl)
        print(f" DELETE /visualizations -> HTTP {code}")
        if not wait_cleanup(lbl):
            print(" WARN: K8s resources not fully cleaned up after timeout")

    # Execute N POST requests and collect latency and errors
    lats, errs = [], 0
    for i in range(N):
        d, status = await single_request(cfg["endpoint"], cfg["payload"])
        lats.append(d)
        if status >= 400:
            errs += 1
        # Avoid sending requests too quickly; adjust as needed
        await asyncio.sleep(1)

    lats.sort()
    avg = sum(lats) / N
    p95 = lats[int(N * 0.95)]
    print(f" Avg {avg:.1f} ms | P95 {p95:.1f} ms | errs {errs}/{N}")

# --------------------------------------------
# Main routine: run cold and warm tests for each scenario
# --------------------------------------------
async def main():
    for name, cfg in SCENARIOS.items():
        # Cold start
        await run_scenario(name, cfg, N=5, delete_before=True)
        # Warm start
        await run_scenario(name, cfg, N=5, delete_before=False)

if __name__ == "__main__":
    asyncio.run(main())