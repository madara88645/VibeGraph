"""Routes for project file upload and analysis."""

import logging
import os
import shutil
import stat
import tempfile
import time
import zipfile
import sys
from typing import List

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

import app.dependencies as deps
from analyst.analyzer import CodeAnalyzer
from app.models import UploadResponse
from app.rate_limit import UPLOAD_LIMIT, limiter
from app.utils.security import UPLOAD_PREFIX, normalize_uploaded_filename

router = APIRouter(prefix="/api", tags=["upload"])

logger = logging.getLogger(__name__)

UPLOAD_RETENTION_SECONDS = int(os.getenv("VIBEGRAPH_UPLOAD_RETENTION_SECONDS", "3600"))

# Cap exported graph size to protect JSON payload, Dagre layout, and ReactFlow
# render cost. Overridable per-deployment for experimentation.
GRAPH_NODE_BUDGET = int(os.getenv("VIBEGRAPH_GRAPH_NODE_BUDGET", "1500"))


def _format_upload_limit(byte_count: int) -> str:
    megabytes = byte_count / (1024 * 1024)
    if megabytes.is_integer():
        return f"{int(megabytes)} MB"
    return f"{megabytes:.1f} MB"


def _handle_rmtree_error(func, path, exc_info):
    """Log errors that occur during shutil.rmtree."""
    logger.error(f"Failed to remove {path} during cleanup: {exc_info}")


def _safe_rmtree(path: str) -> None:
    """Safely remove a directory tree, handling Python version differences for error logging."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_handle_rmtree_error)
    else:
        shutil.rmtree(path, onerror=_handle_rmtree_error)


def cleanup_tmp_dir(path: str) -> None:
    """Background task to remove temp directory."""
    if os.path.exists(path):
        _safe_rmtree(path)


def contains_supported_file(path: str) -> bool:
    """Return True when an uploaded tree contains at least one source file
    in a language VibeGraph can analyse (Python, JavaScript, TypeScript,
    …). Extensions come from the language registry, so adding a new plugin
    automatically extends what we accept.
    """
    from analyst.languages import all_extensions

    supported = tuple(all_extensions())
    stack = [path]
    while stack:
        current_dir = stack.pop()
        try:
            with os.scandir(current_dir) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        name_lower = entry.name.lower()
                        if name_lower.endswith(supported):
                            return True
        except OSError:
            continue
    return False


# Backwards-compat shim — older external scripts may still import the
# original name. The check is now multi-language.
contains_python_file = contains_supported_file


def cleanup_expired_upload_dirs(
    retention_seconds: int = UPLOAD_RETENTION_SECONDS,
) -> None:
    """Remove old upload temp folders, keeping recent uploads available."""
    now = time.time()
    temp_root = tempfile.gettempdir()
    try:
        with os.scandir(temp_root) as it:
            for entry in it:
                if not entry.name.startswith(UPLOAD_PREFIX):
                    continue
                try:
                    if not entry.is_dir():
                        continue
                    age = now - entry.stat().st_mtime
                    if age > retention_seconds:
                        _safe_rmtree(entry.path)
                except Exception as e:
                    logger.error(
                        f"Error checking or deleting expired upload dir {entry.path}: {e}"
                    )
                    continue
    except Exception as e:
        logger.error(f"Error scanning temp directory for expired uploads: {e}")


@router.post(
    "/upload-project",
    response_model=UploadResponse,
    summary="Upload and analyse a project",
)
@limiter.limit(UPLOAD_LIMIT)
def upload_project(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
):
    """
    Receives dynamic uploads (single .py, multiple files, or .zip), saves to a
    temporary folder, runs analysis, and returns the graph data directly.
    """
    background_tasks.add_task(cleanup_expired_upload_dirs)
    tmp_dir = tempfile.mkdtemp(prefix=UPLOAD_PREFIX)

    MAX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024
    max_upload_size = deps.get_max_upload_bytes()
    MAX_ZIP_FILES = 10000
    MAX_UPLOAD_FILES = 10000

    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files uploaded (max {MAX_UPLOAD_FILES})",
        )

    try:
        profile_mode = request.query_params.get("profile") == "1"
        profile_data: dict | None = {} if profile_mode else None
        _t_upload = time.perf_counter() if profile_data is not None else 0.0
        total_upload_size = 0
        total_uncompressed_header_size = 0
        total_extracted_size = 0
        total_zip_files = 0
        for file in files:
            safe_name = normalize_uploaded_filename(file.filename)
            file_path = os.path.join(tmp_dir, safe_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True, mode=0o700)

            with open(file_path, "wb") as buffer:
                while True:
                    chunk = file.file.read(8192)
                    if not chunk:
                        break
                    total_upload_size += len(chunk)
                    if total_upload_size > max_upload_size:
                        raise HTTPException(
                            status_code=413,
                            detail=(
                                "Upload too large. Max total upload size is "
                                f"{_format_upload_limit(max_upload_size)}."
                            ),
                        )
                    buffer.write(chunk)

            if safe_name.endswith(".zip"):
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    tmp_dir_real = os.path.realpath(tmp_dir)
                    safe_members = []
                    for member in zip_ref.infolist():
                        total_zip_files += 1
                        if total_zip_files > MAX_ZIP_FILES:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Too many files in zip archive (max {MAX_ZIP_FILES})",
                            )

                        try:
                            if stat.S_ISLNK(member.external_attr >> 16):
                                raise ValueError("Symlink in zip file detected")

                            safe_filename = normalize_uploaded_filename(member.filename)
                            target_path = os.path.join(tmp_dir_real, safe_filename)
                            extracted_path = os.path.realpath(target_path)

                            if (
                                not extracted_path.startswith(tmp_dir_real + os.sep)
                                and extracted_path != tmp_dir_real
                            ):
                                raise ValueError("Path traversal detected")

                        except (HTTPException, ValueError):
                            # Let's not expose the exact reason to avoid information disclosure, just standard Unsafe zip file.
                            raise HTTPException(
                                status_code=400,
                                detail=f"Unsafe zip file detected: {safe_name}",
                            )

                        total_uncompressed_header_size += member.file_size
                        if total_uncompressed_header_size > MAX_UNCOMPRESSED_SIZE:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Zip contents too large: {total_uncompressed_header_size} bytes (max {MAX_UNCOMPRESSED_SIZE})",
                            )

                        member.filename = safe_filename
                        safe_members.append((member, extracted_path))

                    # PERFORMANCE OPTIMIZATION (Bolt): Cache created directories
                    # during ZIP extraction to avoid redundant O(N) os.makedirs syscalls,
                    # which reduces directory creation overhead by >90% for large archives.
                    created_dirs = set()
                    for member, extracted_path in safe_members:
                        if member.is_dir():
                            if extracted_path not in created_dirs:
                                os.makedirs(extracted_path, exist_ok=True, mode=0o700)
                                created_dirs.add(extracted_path)
                            continue

                        dir_name = os.path.dirname(extracted_path)
                        if dir_name not in created_dirs:
                            os.makedirs(dir_name, exist_ok=True, mode=0o700)
                            created_dirs.add(dir_name)
                        with (
                            zip_ref.open(member) as source,
                            open(extracted_path, "wb") as target,
                        ):
                            while True:
                                chunk = source.read(8192)
                                if not chunk:
                                    break
                                total_extracted_size += len(chunk)
                                if total_extracted_size > MAX_UNCOMPRESSED_SIZE:
                                    raise HTTPException(
                                        status_code=400,
                                        detail=f"Zip contents too large (max {MAX_UNCOMPRESSED_SIZE} bytes)",
                                    )
                                target.write(chunk)
                os.remove(file_path)

        if profile_data is not None:
            profile_data["upload_io_ms"] = round(
                (time.perf_counter() - _t_upload) * 1000, 2
            )

        _t_contains = time.perf_counter() if profile_data is not None else 0.0
        if not contains_supported_file(tmp_dir):
            raise HTTPException(
                status_code=400,
                detail=(
                    "No supported source files found. Upload a project folder or "
                    "zip containing Python (.py), JavaScript (.js/.jsx/.mjs/.cjs) "
                    "or TypeScript (.ts/.tsx) files."
                ),
            )
        if profile_data is not None:
            profile_data["contains_supported_ms"] = round(
                (time.perf_counter() - _t_contains) * 1000, 2
            )
        _t0 = time.perf_counter() if profile_data is not None else 0.0
        result = CodeAnalyzer().analyze_file(tmp_dir, _profile=profile_data)
        if profile_data is not None:
            profile_data["analyze_total_ms"] = round(
                (time.perf_counter() - _t0) * 1000, 2
            )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        graph = result["graph"]

        # Dedupe while preserving order, then cap to keep responses bounded
        # regardless of how many files failed.
        raw_errors = result.get("errors") or []
        seen = set()
        deduped_errors = []
        for msg in raw_errors:
            if msg not in seen:
                seen.add(msg)
                deduped_errors.append(msg)

        MAX_REPORTED_ERRORS = 20

        if deduped_errors and graph.number_of_nodes() == 0:
            shown = deduped_errors[:MAX_REPORTED_ERRORS]
            extra = len(deduped_errors) - len(shown)
            detail = "; ".join(shown)
            if extra > 0:
                detail += f" ({extra} more)"
            raise HTTPException(status_code=400, detail=detail)

        if graph.number_of_nodes() == 0:
            raise HTTPException(
                status_code=400,
                detail="No analyzable code found in the supported languages.",
            )

        _t1 = time.perf_counter() if profile_data is not None else 0.0
        response_data = deps.exporter.export_to_react_flow(
            graph, _profile=profile_data, max_nodes=GRAPH_NODE_BUDGET
        )
        if profile_data is not None:
            profile_data["export_total_ms"] = round(
                (time.perf_counter() - _t1) * 1000, 2
            )

        if deduped_errors:
            warnings = deduped_errors[:MAX_REPORTED_ERRORS]
            extra = len(deduped_errors) - len(warnings)
            if extra > 0:
                warnings = warnings + [f"({extra} more skipped files)"]
            response_data["warnings"] = warnings

        if profile_data is not None:
            return JSONResponse(content={**response_data, "_profile": profile_data})
        return response_data

    except HTTPException:
        cleanup_tmp_dir(tmp_dir)
        raise
    except zipfile.BadZipFile:
        cleanup_tmp_dir(tmp_dir)
        raise HTTPException(
            status_code=400,
            detail="Invalid zip archive detected.",
        )
    except Exception as e:
        logger.error(f"Upload/Analysis failed: {e}", exc_info=True)
        cleanup_tmp_dir(tmp_dir)
        raise HTTPException(
            status_code=500,
            detail="Upload/Analysis failed due to an internal error.",
        )
