import requests
import json
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualizationApiTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/visualizations"

    def delete_visualization(self, name: str, label: str) -> None:
        try:
            response = requests.delete(
                self.endpoint,
                params={"name": name, "label": label}
            )
            response.raise_for_status()
            logger.info(f"Successfully deleted visualization for {name}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete visualization: {e}")
            pass

    def test_create_visualization(self, payload: Dict) -> Dict:
        try:
            # 先删除已存在的资源，传入name和label
            self.delete_visualization(payload['name'], payload['label'])
            
            # 然后创建新资源
            response = requests.post(
                self.endpoint,
                headers={"Content-Type": "application/json"},
                json=payload
            )
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"Successfully created visualization for {payload['name']}")
            logger.info(f"Access URL: {response_data['visualization_url']}")
            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create visualization: {e}")
            raise

    def run_test_cases(self):
        test_cases = [
            {
                "name": "n-a-a-vre-im-zhuyh-gmail-com-ncgqw-sd2g8",
                "label": "naavre-visualizer-notebook",
                "base_url": "",
                "needs_base_path": False,
                "target_port": 3838
            },
            {
                "name": "n-a-a-vre-im-zhuyh-gmail-com-crc5p",
                "label": "naavre-visualizer-notebook",
                "base_url": "naavre-visualizer-notebook",
                "needs_base_path": True,
                "target_port": 5173
            }
        ]

        for case in test_cases:
            try:
                self.test_create_visualization(case)
            except Exception as e:
                logger.error(f"Test case failed: {case['name']}")

def main():
    tester = VisualizationApiTester()
    tester.run_test_cases()

if __name__ == "__main__":
    main()