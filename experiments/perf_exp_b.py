#!/usr/bin/env python3
import os, asyncio, time, httpx

API = os.getenv("API_URL", "http://localhost:8000")
NAMESPACE = os.getenv("K8S_NAMESPACE", "default")

INTERFACES = {
  "streamlit_basic": {
    "endpoint": "/visualizations/streamlit",
    "payload": {
      "title": "Perf Streamlit Basic",
      "chart_type": "line",
      "data": {"x":[1,2,3,4],"y":[4,3,2,1]},
      "layout": {"title":"Basic Streamlit"},
      "options": {}
    }
  },
  "streamlit_dashboard": {
    "endpoint": "/visualizations/dashboard",
    "payload": {
      "title":"Perf Dashboard",
      "data": {
        "layout":{"rows":1,"cols":1},
        "charts":[
          {
            "title":"Chart1",
            "type":"bar",
            "data":{"x":[1,2,3],"y":[3,2,1]},
            "layout": {"title":"Inner Chart"},
          }
        ]
      },
      "options": {},
      "metadata": {}
    }
  },
  "scientific": {
    "endpoint": "/visualizations/scientific",
    "payload": {
      "title":"Perf Scientific",
      "chart_type":"line",
      "data":{"x":[1,2,3],"y":[1,4,9]},
      "layout":{}, "options":{}, "metadata":{}
    }
  }
}

async def post_and_get(ep, payload):
    async with httpx.AsyncClient(base_url=API, timeout=30) as c:
        t0 = time.time()
        r = await c.post(ep, json=payload)
        dt = (time.time()-t0)*1000
        if r.status_code != 200:
            return dt, r.status_code, None, False

        body = r.json()
        vid = body.get("visualization_id") or body.get("id")
        # now GET the data
        get_r = await c.get(f"/api/visualization/data/{vid}")
        ok = get_r.status_code == 200
        return dt, r.status_code, vid, ok

async def run_test(name, cfg, N=10):
    print(f"\n-- {name} x {N} --")
    lats, errs = [], 0
    for i in range(N):
        dt, status, vid, ok = await post_and_get(cfg["endpoint"], cfg["payload"])
        lats.append(dt)
        if status != 200:
            errs += 1
        print(f"[{i+1:2d}] {status=}, write_ok={ok}, lat={dt:.1f}ms, vid={vid}")
        await asyncio.sleep(1)
    lats.sort()
    avg = sum(lats)/N
    p95 = lats[int(N*0.95)]
    print(f"→ Result: Avg {avg:.1f} ms | P95 {p95:.1f} ms | errs {errs}/{N}")

async def main():
    for name, cfg in INTERFACES.items():
        await run_test(name, cfg, N=10)

if __name__=="__main__":
    asyncio.run(main())