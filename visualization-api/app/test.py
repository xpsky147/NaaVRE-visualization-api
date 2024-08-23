import unittest
from fastapi.testclient import TestClient
from main import app
from services.k8s_service import create_k8s_resources, delete_k8s_resources

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_visualization(self):
        response = self.client.post(
            "/visualization_ingress_service",
            json={"name": "test-w"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("visualization_url", response.json())
        print("Visualization URL:", response.json()["visualization_url"])

    def test_delete_visualization(self):
        # First, create the visualization to ensure it exists
        self.client.post(
            "/visualization_ingress_service",
            json={"name": "test-visualization"}
        )
        
        # Now, delete the visualization
        response = self.client.delete("/visualization_ingress_service", params={"id": "test-visualization"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Resource deleted successfully"})

    def tearDown(self):
        # Cleanup resources
        try:
            delete_k8s_resources("test-visualization")
        except Exception as e:
            print(f"Error during tearDown: {e}")

if __name__ == '__main__':
    unittest.main()