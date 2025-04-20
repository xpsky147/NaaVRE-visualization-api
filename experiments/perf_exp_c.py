#!/usr/bin/env python3
import os, time, subprocess, statistics
import httpx

API = os.getenv("API_URL", "http://localhost:8000")
NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
REPEAT = 5

# 前缀要和你的 K8sResourceManager 一致
SVC_PREFIX = "viz-svc-"
ING_PREFIX = "viz-ing-"

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

def wait_for_presence(label, timeout=60):
    """等 svc 和 ing 都被创建"""
    svc = SVC_PREFIX + label
    ing = ING_PREFIX + label
    end = time.time() + timeout
    while time.time() < end:
        svc_ok = subprocess.run(
            ["kubectl","get","svc",svc,"-n",NAMESPACE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        ing_ok = subprocess.run(
            ["kubectl","get","ing",ing,"-n",NAMESPACE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        if svc_ok and ing_ok:
            return True
        time.sleep(1)
    return False

def wait_for_absence(label, timeout=120):
    """等 svc 和 ing 都被删除"""
    svc = SVC_PREFIX + label
    ing = ING_PREFIX + label
    end = time.time() + timeout
    while time.time() < end:
        svc_exists = subprocess.run(
            ["kubectl","get","svc",svc,"-n",NAMESPACE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        ing_exists = subprocess.run(
            ["kubectl","get","ing",ing,"-n",NAMESPACE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        if not svc_exists and not ing_exists:
            return True
        time.sleep(1)
    return False

def measure_cleanup(label, name, payload):
    # 1. POST 创建
    r = httpx.post(f"{API}/visualizations", json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"POST 失败: {r.status_code} {r.text}")

    # 2. 等待资源出现
    if not wait_for_presence(label):
        raise RuntimeError("资源未在规定时间内出现")

    # 3. 记录开始时刻
    t1 = time.time()

    # 4. DELETE
    d = httpx.delete(f"{API}/visualizations",
                     params={"name": name, "label": label},
                     timeout=60)
    if d.status_code >= 400:
        raise RuntimeError(f"DELETE 失败: {d.status_code} {d.text}")

    # 5. 等待资源消失
    if not wait_for_absence(label):
        raise RuntimeError("资源未在规定时间内清理")

    t2 = time.time()
    return (t2 - t1) * 1000

def main():
    print(f"Experiment C: 资源清理延迟 x {REPEAT}\n")
    for scen, cfg in SCENARIOS.items():
        print(f"-- 场景 {scen} --")
        results = []
        for i in range(REPEAT):
            try:
                ms = measure_cleanup(
                    label=cfg["label"],
                    name=cfg["post_payload"]["name"],
                    payload=cfg["post_payload"]
                )
                print(f" [{i+1}] cleanup latency: {ms:.1f} ms")
                results.append(ms)
            except Exception as e:
                print(f" [{i+1}] ERROR: {e}")
            time.sleep(5)
        if results:
            avg = statistics.mean(results)
            p95 = statistics.quantiles(results, n=100)[94]
            print(f" → Avg {avg:.1f} ms | P95 {p95:.1f} ms | min {min(results):.1f} ms | max {max(results):.1f} ms\n")
        else:
            print(" → 全部失败，无有效数据\n")

if __name__ == "__main__":
    main()