import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from serve import app

client = TestClient(app)

def test_health_get():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok', 'vibe': 'checked'}

def test_health_post_405():
    response = client.post('/api/health')
    assert response.status_code == 405
