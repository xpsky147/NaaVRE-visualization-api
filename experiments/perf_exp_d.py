#!/usr/bin/env python3
import os, asyncio, time, httpx
from statistics import mean, quantiles

API = os.getenv("API_URL", "http://localhost:8000")
CONCURRENCY = int(os.getenv("CONCURRENCY", "50"))
TOTAL = int(os.getenv("TOTAL", "500"))

ENDPOINTS = {
  "scientific": {
    "ep": "/visualizations/scientific",
    "payload": {
      "title":"D Sci", "chart_type":"line",
      "data":{"x":[1,2,3],"y":[1,4,9]},
      "layout":{}, "options":{}, "metadata":{}
    }
  },
  "streamlit": {
    "ep": "/visualizations/streamlit",
    "payload": {
      "title":"D Streamlit","chart_type":"line",
      "data":{"x":[1,2,3],"y":[3,2,1]},
      "layout":{}, "options":{}
    }
  },
  "dashboard": {
    "ep": "/visualizations/dashboard",
    "payload": {
      "title":"D Dash",
      "data":{"layout":{"rows":1,"cols":1},"charts":[]},
      "options":{}, "metadata":{}
    }
  }
}

async def worker(name, ep, payload, queue, results):
    async with httpx.AsyncClient(base_url=API, timeout=30) as client:
        while True:
            idx = await queue.get()
            if idx is None:
                queue.task_done()
                break
            t0 = time.time()
            try:
                r = await client.post(ep, json=payload)
                dt = (time.time()-t0)*1000
                results.append((dt, r.status_code))
            except Exception as e:
                results.append((None, None))
            finally:
                queue.task_done()
            if idx % 50 == 0:
                print(f"{name} worker processed {idx}")
    
async def run_benchmark(name, cfg):
    print(f"\n== {name} 并发压测: {TOTAL} 次， 并发数 {CONCURRENCY} ==")
    queue = asyncio.Queue()
    for i in range(TOTAL):
        await queue.put(i)
    for _ in range(CONCURRENCY):
        await queue.put(None)

    results = []
    tasks = [asyncio.create_task(worker(name, cfg["ep"], cfg["payload"], queue, results))
             for _ in range(CONCURRENCY)]

    t_start = time.time()
    await queue.join()
    t_end = time.time()

    for task in tasks:
        task.cancel()

    lats = [d for d,s in results if d is not None]
    codes = [s for d,s in results]
    total_time = t_end - t_start
    qps = sum(1 for c in codes if c==200) / total_time

    print(f"· 总耗时: {total_time:.1f}s | QPS: {qps:.1f}")
    print(f"· Success: {sum(1 for c in codes if c==200)}/{len(codes)}")
    if lats:
        lats.sort()
        p50, p95, p99 = quantiles(lats, n=100)[49], quantiles(lats, n=100)[94], quantiles(lats, n=100)[98]
        print(f"· Latency ms: Avg {mean(lats):.1f} | P50 {p50:.1f} | P95 {p95:.1f} | P99 {p99:.1f}")

async def main():
    for name,cfg in ENDPOINTS.items():
        await run_benchmark(name, cfg)

if __name__=="__main__":
    asyncio.run(main())