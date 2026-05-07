import os
import zipfile
from io import BytesIO
from fastapi.testclient import TestClient

from serve import app

client = TestClient(app)


def test_mixed_language_project_upload():
    # 1. Zip the directory
    buffer = BytesIO()
    project_dir = "tests/fixtures/mixed_project"

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Ensure the paths in zip are relative to project_dir
                arcname = os.path.relpath(file_path, project_dir)
                zf.write(file_path, arcname)

    buffer.seek(0)

    # 2. POST to /api/upload-project
    files = {"files": ("project.zip", buffer, "application/zip")}
    response = client.post("/api/upload-project", files=files, timeout=30.0)

    # 3. Assert: response 200
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "nodes" in data, "Response should contain nodes"

    # 4. Assert: graph contains at least one node with language="python"
    nodes = data.get("nodes", [])
    languages = [node.get("data", {}).get("language") for node in nodes]

    assert "python" in languages, (
        "Graph should contain at least one node with language='python'"
    )

    # 5. Assert: graph contains at least one node with language="javascript"
    assert "javascript" in languages, (
        "Graph should contain at least one node with language='javascript'"
    )

    # 6. GET /api/languages and assert response contains "python" and "javascript" in the list
    lang_response = client.get("/api/languages")
    assert lang_response.status_code == 200, (
        f"Expected 200, got {lang_response.status_code}"
    )

    lang_data = lang_response.json()
    supported_languages = lang_data.get("languages", [])
    supported_language_ids = [lang.get("id") for lang in supported_languages]

    assert "python" in supported_language_ids, (
        "Supported languages should include 'python'"
    )
    assert "javascript" in supported_language_ids, (
        "Supported languages should include 'javascript'"
    )
