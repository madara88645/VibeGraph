import time
from fastapi.testclient import TestClient
from serve import app, SnippetRequest

client = TestClient(app)

def run_benchmark(n=1000):
    start = time.perf_counter()
    for _ in range(n):
        response = client.post("/api/snippet", json={
            "file_path": "serve.py",
            "node_id": "serve.get_snippet"
        })
        assert response.status_code == 200
    end = time.perf_counter()
    return end - start

if __name__ == "__main__":
    duration = run_benchmark(100)
    print(f"Baseline for 100 requests: {duration:.3f} seconds")
