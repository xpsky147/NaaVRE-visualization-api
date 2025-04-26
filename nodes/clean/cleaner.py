import requests
import os
import socket
import time

# Configuration
API_HOST = os.environ.get("API_URL", "http://viz-test-visualization-api")
API_URL  = f"{API_HOST}/visualizations"
MAX_RETRIES = 3
WAIT_SECONDS = 5

start_time = time.time()

# Get environment variable
workflow_name = os.environ["WORKFLOW_NAME"]

# Debug info
print(f"Attempting to resolve visualization-api...")
try:
    print(f"visualization-api IP: {socket.gethostbyname('visualization-api')}")
except Exception as e:
    print(f"DNS lookup failed: {str(e)}")

print(f"Cleaning up visualization for workflow: {workflow_name}")
print(f"Using API URL: {API_URL}")

# Build request parameters
params = {
    "name": workflow_name,
    "label": "naavre-visualizer-notebook"
}

for attempt in range(MAX_RETRIES):
    try:
        print(f"Attempt {attempt + 1} - Sending DELETE request with params: {params}")
        response = requests.delete(
            API_URL,
            params=params,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code in [200, 404]:  # Successfully deleted or already gone
            print(f"Successfully deleted visualization for workflow: {workflow_name}")
            break
        else:
            print(f"Attempt {attempt + 1} failed: API returned {response.status_code}")
            print(f"Response: {response.text}")
            
            if attempt == MAX_RETRIES - 1:  # Last attempt failed
                raise Exception(f"Failed to delete visualization after {MAX_RETRIES} attempts")
            
    except (requests.exceptions.RequestException, Exception) as e:
        print(f"Attempt {attempt + 1} failed: {str(e)}")
        
        if attempt == MAX_RETRIES - 1:  # Last attempt failed
            raise  # Re-raise
        
    if attempt < MAX_RETRIES - 1:
        print(f"Waiting {WAIT_SECONDS} seconds before next attempt...")
        time.sleep(WAIT_SECONDS)

end_time = time.time()
print(f"Cleanup completed in {end_time - start_time:.2f} seconds")