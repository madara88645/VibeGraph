"""Routes for project file upload and analysis."""

import logging
import os
import shutil
import stat
import tempfile
import time
import zipfile
import sys
from collections.abc import AsyncGenerator, AsyncIterator
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

import app.dependencies as deps
from analyst.analyzer import IGNORED_DIRS, CodeAnalyzer
from app.models import UploadResponse
from app.rate_limit import UPLOAD_LIMIT, limiter
from app.utils.security import (
    UPLOAD_PREFIX,
    normalize_uploaded_filename,
    normalize_zip_member_path,
    sensitive_upload_segment,
)

router = APIRouter(prefix="/api", tags=["upload"])

logger = logging.getLogger(__name__)

UPLOAD_RETENTION_SECONDS = int(os.getenv("VIBEGRAPH_UPLOAD_RETENTION_SECONDS", "3600"))

# Cap exported graph size to protect JSON payload, Dagre layout, and ReactFlow
# render cost. Overridable per-deployment for experimentation.
GRAPH_NODE_BUDGET = int(os.getenv("VIBEGRAPH_GRAPH_NODE_BUDGET", "1500"))

MAX_UPLOAD_FILES = 10000

# MAX_ZIP_FILES caps the zip members we extract. Members we skip (.git,
# node_modules, ...) are free, so MAX_ZIP_ENTRIES caps every entry we scan.
MAX_ZIP_FILES = 10000
MAX_ZIP_ENTRIES = 10 * MAX_ZIP_FILES

# .env templates hold placeholders, not code, so zips may carry them.
ENV_TEMPLATE_NAMES = frozenset(
    {".env.example", ".env.sample", ".env.template", ".env.dist"}
)

# Raw multipart bytes allowed per file on top of its contents: the boundary
# line plus the Content-Disposition (relative path) and Content-Type headers.
MULTIPART_OVERHEAD_PER_FILE = 1024

_UPLOAD_REQUEST_BODY = {
    "required": True,
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "required": ["files"],
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "contentMediaType": "application/octet-stream",
                        },
                    }
                },
            }
        }
    },
}


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


def _is_skipped_zip_member(safe_filename: str, is_dir: bool) -> bool:
    """Return True for zip members the analyzer would never read: anything
    inside an IGNORED_DIRS folder, a git submodule's ``.git`` file, or an
    .env template such as .env.example."""
    parts = safe_filename.split("/")
    folders = parts if is_dir else parts[:-1]
    if any(part in IGNORED_DIRS for part in folders):
        return True
    return parts[-1] == ".git" or parts[-1].lower() in ENV_TEMPLATE_NAMES


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


def _upload_too_large(max_upload_size: int) -> HTTPException:
    return HTTPException(
        status_code=413,
        detail=(
            "Upload too large. Max total upload size is "
            f"{_format_upload_limit(max_upload_size)}."
        ),
    )


async def read_upload_files(request: Request) -> AsyncIterator[List[UploadFile]]:
    """Parse the multipart upload body and close its files after the request.

    FastAPI's File(...) parsing stops at Starlette's default of 1000 files,
    below MAX_UPLOAD_FILES. Raising that cap alone would let thousands of
    parts pile up in memory before upload_project's size check runs, so the
    raw body is counted against a byte budget while it streams in.
    """
    media_type = request.headers.get("content-type", "").partition(";")[0]
    if media_type.strip().lower() != "multipart/form-data":
        raise HTTPException(
            status_code=400, detail="Expected a multipart/form-data upload."
        )

    max_upload_size = deps.get_max_upload_bytes()
    byte_budget = max_upload_size + MAX_UPLOAD_FILES * MULTIPART_OVERHEAD_PER_FILE
    content_length = request.headers.get("content-length", "")
    if content_length.isdecimal() and int(content_length) > byte_budget:
        raise _upload_too_large(max_upload_size)

    async def counted_stream() -> AsyncGenerator[bytes, None]:
        received = 0
        async for chunk in request.stream():
            received += len(chunk)
            if received > byte_budget:
                raise _upload_too_large(max_upload_size)
            yield chunk

    # The frontend sends only file parts, so plain fields get a small cap.
    parser = MultiPartParser(
        request.headers, counted_stream(), max_files=MAX_UPLOAD_FILES, max_fields=16
    )
    try:
        form = await parser.parse()
    except MultiPartException as exc:
        raise HTTPException(status_code=400, detail=exc.message)
    except HTTPException:
        raise
    except Exception as exc:
        # Same fallback FastAPI uses when it parses File(...) bodies itself.
        raise HTTPException(
            status_code=400, detail="There was an error parsing the body"
        ) from exc

    try:
        files = [item for item in form.getlist("files") if isinstance(item, UploadFile)]
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
        yield files
    finally:
        await form.close()


@router.post(
    "/upload-project",
    response_model=UploadResponse,
    summary="Upload and analyse a project",
    openapi_extra={"requestBody": _UPLOAD_REQUEST_BODY},
)
@limiter.limit(UPLOAD_LIMIT)
def upload_project(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = Depends(read_upload_files, scope="function"),
):
    """
    Receives dynamic uploads (single .py, multiple files, or .zip), saves to a
    temporary folder, runs analysis, and returns the graph data directly.
    """
    background_tasks.add_task(cleanup_expired_upload_dirs)
    tmp_dir = tempfile.mkdtemp(prefix=UPLOAD_PREFIX)

    MAX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024
    max_upload_size = deps.get_max_upload_bytes()

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
        total_zip_entries = 0
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
                    members = zip_ref.infolist()
                    total_zip_entries += len(members)
                    if total_zip_entries > MAX_ZIP_ENTRIES:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Too many entries in zip archive (max {MAX_ZIP_ENTRIES})",
                        )

                    safe_members = []
                    for member in members:
                        try:
                            if stat.S_ISLNK(member.external_attr >> 16):
                                raise ValueError("Symlink in zip file detected")

                            safe_filename = normalize_zip_member_path(member.filename)
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

                        # Read before member.filename loses its trailing "/".
                        is_dir = member.is_dir()
                        if _is_skipped_zip_member(safe_filename, is_dir):
                            continue

                        if sensitive_upload_segment(safe_filename) is not None:
                            raise HTTPException(
                                status_code=400,
                                detail=(
                                    f"Unsafe zip file detected: {safe_name} contains "
                                    "a secrets file or folder such as .env or .ssh. "
                                    "Remove it and zip the project again."
                                ),
                            )

                        total_zip_files += 1
                        if total_zip_files > MAX_ZIP_FILES:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Too many files in zip archive (max {MAX_ZIP_FILES})",
                            )

                        total_uncompressed_header_size += member.file_size
                        if total_uncompressed_header_size > MAX_UNCOMPRESSED_SIZE:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Zip contents too large: {total_uncompressed_header_size} bytes (max {MAX_UNCOMPRESSED_SIZE})",
                            )

                        member.filename = safe_filename
                        safe_members.append((member, extracted_path, is_dir))

                    # PERFORMANCE OPTIMIZATION (Bolt): Cache created directories
                    # during ZIP extraction to avoid redundant O(N) os.makedirs syscalls,
                    # which reduces directory creation overhead by >90% for large archives.
                    created_dirs = set()
                    for member, extracted_path, is_dir in safe_members:
                        if is_dir:
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
