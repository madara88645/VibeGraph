"""Folder uploads above Starlette's 1000-file default, with a bounded body."""

import asyncio
import tempfile
import zipfile
from io import BytesIO

import httpx
import pytest
from fastapi.testclient import TestClient
from starlette import formparsers

from app.routers import upload
from serve import app

client = TestClient(app)

BOUNDARY = "vibegraph-test-boundary"


def _py_files(count):
    return [
        (
            "files",
            (
                f"pkg/mod_{i}.py",
                f"def func_{i}():\n    return {i}\n".encode(),
                "text/x-python",
            ),
        )
        for i in range(count)
    ]


def _record_spooled_files(monkeypatch):
    opened = []

    class RecordingSpooledFile(tempfile.SpooledTemporaryFile):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            opened.append(self)

    monkeypatch.setattr(formparsers, "SpooledTemporaryFile", RecordingSpooledFile)
    return opened


def _post_streamed(chunks, headers):
    """POST the body chunk by chunk and count how many chunks the app read."""
    pulled = 0

    async def body():
        nonlocal pulled
        for chunk in chunks:
            pulled += 1
            yield chunk

    async def send():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            return await async_client.post(
                "/api/upload-project", content=body(), headers=headers
            )

    response = asyncio.run(send())
    return response, pulled


def _oversized_body_chunks(chunk_count):
    head = (
        f"--{BOUNDARY}\r\n"
        'Content-Disposition: form-data; name="files"; filename="big.py"\r\n'
        "Content-Type: text/x-python\r\n\r\n"
    ).encode()
    tail = f"\r\n--{BOUNDARY}--\r\n".encode()
    return [head] + [b"#" * 65536] * chunk_count + [tail]


@pytest.mark.parametrize("count", [1001, 2000])
def test_folder_upload_above_starlette_default_returns_graph(count):
    response = client.post("/api/upload-project", files=_py_files(count))

    assert response.status_code == 200, response.text
    assert response.json()["nodes"]


def test_file_count_cap_follows_max_upload_files(monkeypatch):
    # The full 10,001-part case lives in test_upload_security.py.
    monkeypatch.setattr(upload, "MAX_UPLOAD_FILES", 5)
    opened = _record_spooled_files(monkeypatch)

    response = client.post("/api/upload-project", files=_py_files(6))

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Too many files. Maximum number of files is 5."
    )
    assert len(opened) == 5
    assert all(spooled.closed for spooled in opened)


def test_zip_upload_still_returns_graph():
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(
            "pkg/a.py", "from pkg.b import helper\n\ndef run():\n    helper()\n"
        )
        zf.writestr("pkg/b.py", "def helper():\n    return 1\n")
    archive.seek(0)

    response = client.post(
        "/api/upload-project",
        files={"files": ("project.zip", archive, "application/zip")},
    )

    assert response.status_code == 200, response.text
    node_ids = {node["id"] for node in response.json()["nodes"]}
    assert {"run", "helper"} <= node_ids


def test_body_over_budget_is_rejected_from_content_length_without_reading(
    monkeypatch,
):
    monkeypatch.setenv("VIBEGRAPH_MAX_UPLOAD_BYTES", str(1024 * 1024))
    monkeypatch.setattr(upload, "MULTIPART_OVERHEAD_PER_FILE", 0)
    chunks = _oversized_body_chunks(64)

    response, pulled = _post_streamed(
        chunks,
        {
            "content-type": f"multipart/form-data; boundary={BOUNDARY}",
            "content-length": str(sum(len(chunk) for chunk in chunks)),
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "Upload too large. Max total upload size is 1 MB."
    )
    assert pulled == 0


def test_streamed_body_over_budget_stops_parsing_and_closes_files(monkeypatch):
    monkeypatch.setenv("VIBEGRAPH_MAX_UPLOAD_BYTES", str(1024 * 1024))
    monkeypatch.setattr(upload, "MULTIPART_OVERHEAD_PER_FILE", 0)
    opened = _record_spooled_files(monkeypatch)
    chunks = _oversized_body_chunks(64)

    # No Content-Length: httpx sends the body chunked, so only the running
    # byte count can stop it.
    response, pulled = _post_streamed(
        chunks, {"content-type": f"multipart/form-data; boundary={BOUNDARY}"}
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "Upload too large. Max total upload size is 1 MB."
    )
    # 1 MB budget / 64 KB chunks: the parser gives up right after the budget.
    assert pulled <= 18 < len(chunks)
    assert opened and all(spooled.closed for spooled in opened)


def test_uploaded_files_are_closed_after_success_and_endpoint_error(monkeypatch):
    opened = _record_spooled_files(monkeypatch)

    ok = client.post("/api/upload-project", files=_py_files(3))
    rejected = client.post(
        "/api/upload-project",
        files={"files": ("empty.py", BytesIO(b"ANSWER = 42\n"), "text/x-python")},
    )

    assert ok.status_code == 200, ok.text
    assert rejected.status_code == 400
    assert len(opened) == 4
    assert all(spooled.closed for spooled in opened)


@pytest.mark.parametrize(
    ("kwargs", "detail"),
    [
        ({}, "Expected a multipart/form-data upload."),
        ({"json": {"files": []}}, "Expected a multipart/form-data upload."),
        (
            {
                "content": b"files",
                "headers": {"content-type": "multipart/form-data"},
            },
            "Missing boundary in multipart.",
        ),
        (
            {
                "content": b"not multipart",
                "headers": {
                    "content-type": f"multipart/form-data; boundary={BOUNDARY}"
                },
            },
            "Invalid multipart data.",
        ),
        ({"data": {"files": "not a file"}}, "Expected a multipart/form-data upload."),
    ],
)
def test_non_multipart_or_malformed_body_returns_400(kwargs, detail):
    response = client.post("/api/upload-project", **kwargs)

    assert response.status_code == 400
    assert response.json()["detail"] == detail


def test_multipart_without_file_parts_returns_400():
    response = client.post(
        "/api/upload-project",
        data={"files": "not a file"},
        files={"other": ("a.py", b"def a():\n    pass\n", "text/x-python")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No files uploaded."


def test_plain_form_fields_are_capped():
    # Starlette's default is 1000 fields; the frontend sends none.
    response = client.post(
        "/api/upload-project",
        data={f"field_{i}": "x" for i in range(17)},
        files=_py_files(1),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Too many fields. Maximum number of fields is 16."
    )


def test_openapi_documents_multipart_files_field():
    operation = client.get("/openapi.json").json()["paths"]["/api/upload-project"][
        "post"
    ]
    schema = operation["requestBody"]["content"]["multipart/form-data"]["schema"]

    assert operation["requestBody"]["required"] is True
    assert schema["required"] == ["files"]
    assert schema["properties"]["files"]["type"] == "array"
