import requests
import os
import time
from requests.exceptions import RequestException

# 配置
API_URL = "http://visualization-api:80/visualizations"
MAX_RETRIES = 20
WAIT_SECONDS = 5

# 构造请求
payload = {
    "name": os.environ["WORKFLOW_NAME"],
    "label": "naavre-visualizer-notebook",
    "base_url": os.environ.get("BASE_URL", ""),
    "target_port": int(os.environ.get("TARGET_PORT", "5173")),
    "needs_base_path": os.environ.get("NEEDS_BASE_PATH", "false").lower() == "true"
}

# 重试逻辑
for attempt in range(MAX_RETRIES):
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            print(f"Successfully created visualization: {response.json()}")
            break
        else:
            print(f"Attempt {attempt + 1} failed: API returned {response.status_code}")
            print(f"Response: {response.text}")
    
    except RequestException as e:
        print(f"Attempt {attempt + 1} failed: {str(e)}")
    
    if attempt < MAX_RETRIES - 1:  # 不是最后一次尝试
        print(f"Waiting {WAIT_SECONDS} seconds before next attempt...")
        time.sleep(WAIT_SECONDS)
    else:  # 最后一次尝试也失败
        raise Exception(f"Failed after {MAX_RETRIES} attempts")