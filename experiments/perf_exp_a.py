#!/usr/bin/env python3
import os, asyncio, time, httpx, subprocess

# --------------------------------------------
# 配置项
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
        # 用于 kubectl selector 和 DELETE 接口
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
            "data": {"x":[1,2,3],"y":[1,4,9]},
            "layout": {}, "options": {}, "metadata": {}
        },
        # scientific 场景不创建 Service/Ingress，不需要删除
        "label": None
    }
}

# --------------------------------------------
# 单次 POST 请求
# --------------------------------------------
async def single_request(endpoint, payload):
    async with httpx.AsyncClient(base_url=API, timeout=20.0) as client:
        t0 = time.time()
        r = await client.post(endpoint, json=payload)
        t1 = time.time()
        return (t1 - t0) * 1000, r.status_code

# --------------------------------------------
# 走 API DELETE 接口
# --------------------------------------------
async def api_delete(name, label):
    async with httpx.AsyncClient(base_url=API, timeout=30.0) as client:
        # 注意：你的 DELETE 端点是 /visualizations?name=…&label=…
        r = await client.delete(f"/visualizations?name={name}&label={label}")
    return r.status_code

# --------------------------------------------
# 轮询等待 K8s 资源真正清理
# --------------------------------------------
def wait_cleanup(label, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        out = subprocess.run([
            "kubectl", "get", "svc,ing",
            "-n", NAMESPACE,
            "-l", f"workflows.argoproj.io/workflow={label}"
        ], capture_output=True, text=True).stdout
        # 没有资源存在时结束
        if not out.strip() or "No resources found" in out:
            return True
        time.sleep(1)
    return False

# --------------------------------------------
# 针对某个场景的冷/热启动测试
# --------------------------------------------
async def run_scenario(name, cfg, N=5, delete_before=False):
    print(f"\n-- 场景: {name} | delete_before={delete_before} --")
    lbl = cfg.get("label")
    # 只有 label 非空时才做删除
    if delete_before and lbl:
        code = await api_delete(cfg["payload"].get("name", ""), lbl)
        print(f" DELETE /visualizations -> HTTP {code}")
        if not wait_cleanup(lbl):
            print(" WARN: K8s 资源在超时后仍未清理完毕")

    # 执行 N 次 POST 并收集延迟与错误
    lats, errs = [], 0
    for i in range(N):
        d, status = await single_request(cfg["endpoint"], cfg["payload"])
        lats.append(d)
        if status >= 400:
            errs += 1
        # 避免请求过快，可根据需要调节
        await asyncio.sleep(1)

    lats.sort()
    avg = sum(lats) / N
    p95 = lats[int(N * 0.95)]
    print(f" Avg {avg:.1f} ms | P95 {p95:.1f} ms | errs {errs}/{N}")

# --------------------------------------------
# 主流程：依次对每个场景做冷/热启动
# --------------------------------------------
async def main():
    for name, cfg in SCENARIOS.items():
        # 冷启动
        await run_scenario(name, cfg, N=5, delete_before=True)
        # 热启动
        await run_scenario(name, cfg, N=5, delete_before=False)

if __name__ == "__main__":
    asyncio.run(main())