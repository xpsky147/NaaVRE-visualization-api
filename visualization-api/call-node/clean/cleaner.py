import requests
import os

# 配置
API_URL = "http://visualization-api:80/visualizations"

# 获取环境变量
workflow_name = os.environ["WORKFLOW_NAME"]

# 构造请求参数
params = {
    "name": workflow_name,
    "label": "naavre-visualizer-notebook"  # 与create_viz.py保持一致
}

try:
    response = requests.delete(
        API_URL,
        params=params,  # 使用URL参数而不是json body
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print(f"Successfully deleted visualization for workflow: {workflow_name}")
    else:
        print(f"Failed to delete: API returned {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Failed to delete: {str(e)}")