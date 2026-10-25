import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
print('health', client.get('/health').status_code)
print('list_scans', client.get('/scans').status_code)
print('analytics', client.get('/analytics').status_code)
print('root', client.get('/').status_code)
