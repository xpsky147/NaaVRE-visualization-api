import requests
import os
import time
from requests.exceptions import RequestException

# Configuration
API_URL = "http://visualization-api:80/visualizations"
MAX_RETRIES = 20
WAIT_SECONDS = 5

# Build request payload, support visualization type
payload = {
    "name": os.environ["WORKFLOW_NAME"],
    "label": "naavre-visualizer-notebook",
    "base_url": os.environ.get("BASE_URL", ""),
    "target_port": int(os.environ.get("TARGET_PORT", "5173")),
    "needs_base_path": os.environ.get("NEEDS_BASE_PATH", "false").lower() == "true"
}

# Support viz_type environment variable
viz_type = os.environ.get("VIZ_TYPE", "")
if viz_type:
    payload["viz_type"] = viz_type
    print(f"Using visualization type: {viz_type}")

print(f"Starting visualization creation for workflow: {payload['name']}")
start_time = time.time()

# Retry logic
for attempt in range(MAX_RETRIES):
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Successfully created visualization: {result}")
            
            # Save visualization_url
            if "visualization_url" in result:
                with open("/tmp/visualization_url.txt", "w") as f:
                    f.write(result["visualization_url"])
                print(f"Visualization URL saved: {result['visualization_url']}")
            
            # Status check (for information only)
            if "status" in result and result["status"] == "running":
                print("Visualization service is running")
            else:
                print("Warning: Visualization service status unclear")
            break
        else:
            print(f"Attempt {attempt + 1} failed: API returned {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.ConnectionError as e:
        print(f"Attempt {attempt + 1} failed: Connection error - service may be unavailable")
        print(f"Error details: {str(e)}")
    except requests.Timeout as e:
        print(f"Attempt {attempt + 1} failed: Request timed out - service may be overloaded")
        print(f"Error details: {str(e)}")
    except RequestException as e:
        print(f"Attempt {attempt + 1} failed: {str(e)}")
    
    if attempt < MAX_RETRIES - 1:
        print(f"Waiting {WAIT_SECONDS} seconds before next attempt...")
        time.sleep(WAIT_SECONDS)
    else:
        raise Exception(f"Failed after {MAX_RETRIES} attempts")

end_time = time.time()
print(f"Visualization creation completed in {end_time - start_time:.2f} seconds")