import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_home_status():
    path = "/create_system"
    
    response = client.get(path)
    status_code = response.status_code
    content_type = response.headers.get("content-type")
    
    assert status_code == 200
    assert content_type == "application/json"