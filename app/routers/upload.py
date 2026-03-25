"""Routes for project file upload and analysis."""

import logging
import os
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from analyst.analyzer import CodeAnalyzer
import app.dependencies as deps
from app.models import UploadResponse
from app.utils.security import UPLOAD_PREFIX, normalize_uploaded_filename

router = APIRouter(prefix="/api", tags=["upload"])

logger = logging.getLogger(__name__)

UPLOAD_RETENTION_SECONDS = int(os.getenv("VIBEGRAPH_UPLOAD_RETENTION_SECONDS", "3600"))


def cleanup_tmp_dir(path: str) -> None:
    """Background task to remove temp directory."""
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def cleanup_expired_upload_dirs(
    retention_seconds: int = UPLOAD_RETENTION_SECONDS,
) -> None:
    """Remove old upload temp folders, keeping recent uploads available."""
    now = time.time()
    temp_root = Path(tempfile.gettempdir())
    for candidate in temp_root.glob(f"{UPLOAD_PREFIX}*"):
        try:
            if not candidate.is_dir():
                continue
            age = now - candidate.stat().st_mtime
            if age > retention_seconds:
                shutil.rmtree(candidate, ignore_errors=True)
        except Exception:
            continue


@router.post(
    "/upload-project",
    response_model=UploadResponse,
    summary="Upload and analyse a project",
)
def upload_project(
    background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)
):
    """
    Receives dynamic uploads (single .py, multiple files, or .zip), saves to a
    temporary folder, runs analysis, and returns the graph data directly.
    """
    background_tasks.add_task(cleanup_expired_upload_dirs)
    tmp_dir = tempfile.mkdtemp(prefix=UPLOAD_PREFIX)

    MAX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024  # 100 MB

    try:
        for file in files:
            safe_name = normalize_uploaded_filename(file.filename)
            file_path = os.path.join(tmp_dir, safe_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # If it's a zip file, validate and extract it
            if safe_name.endswith(".zip"):
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    tmp_dir_abs = os.path.abspath(tmp_dir)
                    safe_members = []
                    total_size = 0
                    for member in zip_ref.infolist():
                        safe_filename = member.filename.lstrip("/\\")
                        extracted_path = os.path.abspath(
                            os.path.join(tmp_dir_abs, safe_filename)
                        )
                        if (
                            not extracted_path.startswith(tmp_dir_abs + os.sep)
                            and extracted_path != tmp_dir_abs
                        ):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Unsafe zip file detected: {safe_name}",
                            )

                        total_size += member.file_size
                        if total_size > MAX_UNCOMPRESSED_SIZE:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Zip contents too large: {total_size} bytes (max {MAX_UNCOMPRESSED_SIZE})",
                            )

                        member.filename = safe_filename
                        safe_members.append(member)

                    zip_ref.extractall(tmp_dir, members=safe_members)
                os.remove(file_path)

        result = CodeAnalyzer().analyze_file(tmp_dir)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        if result.get("errors") and result["graph"].number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail=result["errors"][0])

        graph = result["graph"]
        response_data = deps.exporter.export_to_react_flow(graph)

        return response_data

    except HTTPException:
        cleanup_tmp_dir(tmp_dir)
        raise
    except Exception as e:
        logger.error(f"Upload/Analysis failed: {e}", exc_info=True)
        cleanup_tmp_dir(tmp_dir)
        raise HTTPException(
            status_code=500, detail="Upload/Analysis failed due to an internal error."
        )
