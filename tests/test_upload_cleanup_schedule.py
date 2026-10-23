"""Tests for the upload cleanup that runs at startup and on a timer."""

import asyncio
import gc
import logging
import os
import shutil
import tempfile
import threading
import time
import uuid

import pytest
from fastapi.testclient import TestClient

import app.routers.upload as upload
from app import app
from app.utils.security import UPLOAD_PREFIX

INTERVAL_ENV = "VIBEGRAPH_UPLOAD_CLEANUP_INTERVAL_SECONDS"


def wait_for(condition, timeout=5.0):
    """Poll condition until it is true or the deadline passes."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return condition()


@pytest.fixture
def make_upload_dir():
    """Create uniquely named upload folders in the real temp dir and remove
    whatever is left of them after the test."""
    created = []

    def make(expired):
        path = os.path.join(
            tempfile.gettempdir(), f"{UPLOAD_PREFIX}schedule_test_{uuid.uuid4().hex}"
        )
        os.mkdir(path)
        with open(os.path.join(path, "main.py"), "w") as f:
            f.write("print('hello')\n")
        if expired:
            old = time.time() - upload.UPLOAD_RETENTION_SECONDS - 60
            os.utime(path, (old, old))
        created.append(path)
        return path

    yield make
    for path in created:
        shutil.rmtree(path, ignore_errors=True)


def test_startup_removes_expired_uploads_and_keeps_fresh_ones(make_upload_dir):
    expired = make_upload_dir(expired=True)
    fresh = make_upload_dir(expired=False)

    with TestClient(app):
        # The startup sweep finishes before the app starts serving.
        assert not os.path.exists(expired)
        assert os.path.isdir(fresh)


def test_periodic_sweep_removes_uploads_that_expire_after_startup(
    monkeypatch, make_upload_dir
):
    monkeypatch.setattr(upload, "UPLOAD_CLEANUP_INTERVAL_SECONDS", 0.01)

    with TestClient(app):
        expired = make_upload_dir(expired=True)
        fresh = make_upload_dir(expired=False)
        assert wait_for(lambda: not os.path.exists(expired))
        assert os.path.isdir(fresh)


def test_failed_sweep_is_logged_and_later_sweeps_still_run(monkeypatch, caplog):
    calls = []

    def flaky_cleanup():
        calls.append(None)
        if len(calls) <= 2:
            raise RuntimeError("disk unavailable")

    monkeypatch.setattr(upload, "cleanup_expired_upload_dirs", flaky_cleanup)
    monkeypatch.setattr(upload, "UPLOAD_CLEANUP_INTERVAL_SECONDS", 0.01)

    with caplog.at_level(logging.ERROR, logger="app.routers.upload"):
        # The first call (at startup) and the second (first timed run) fail.
        with TestClient(app):
            assert wait_for(lambda: len(calls) >= 4)

    failures = [r for r in caplog.records if r.getMessage() == "Upload cleanup failed"]
    assert len(failures) == 2


def test_sweep_runs_in_a_worker_thread(monkeypatch):
    threads = []
    monkeypatch.setattr(
        upload,
        "cleanup_expired_upload_dirs",
        lambda: threads.append(threading.get_ident()),
    )

    async def scenario():
        await upload.sweep_expired_uploads()
        return threading.get_ident()

    loop_thread = asyncio.run(scenario())
    # The filesystem work must not run on the event loop's thread.
    assert len(threads) == 1
    assert threads[0] != loop_thread


def test_cancelling_the_task_during_a_sweep_stops_it(monkeypatch):
    in_sweep = threading.Event()
    release = threading.Event()

    def blocking_cleanup():
        in_sweep.set()
        release.wait(5)

    monkeypatch.setattr(upload, "cleanup_expired_upload_dirs", blocking_cleanup)
    monkeypatch.setattr(upload, "UPLOAD_CLEANUP_INTERVAL_SECONDS", 0.01)

    async def scenario():
        task = asyncio.create_task(upload.run_upload_cleanup_periodically())
        try:
            assert await asyncio.to_thread(in_sweep.wait, 5)
            task.cancel()
            await asyncio.wait({task}, timeout=1)
            # A swallowed CancelledError would leave the task running.
            assert task.cancelled()
        finally:
            release.set()
            while not task.done():
                task.cancel()
                await asyncio.wait({task}, timeout=0.1)

    asyncio.run(scenario())


def test_leaving_the_client_cancels_the_cleanup_task(monkeypatch, caplog):
    tasks = []
    real_loop = upload.run_upload_cleanup_periodically

    async def tracked_loop():
        tasks.append(asyncio.current_task())
        await real_loop()

    monkeypatch.setattr(upload, "run_upload_cleanup_periodically", tracked_loop)

    with caplog.at_level(logging.ERROR, logger="asyncio"):
        with TestClient(app):
            assert wait_for(lambda: tasks)
        gc.collect()

    assert len(tasks) == 1
    assert tasks[0].cancelled()
    assert not [r for r in caplog.records if r.name == "asyncio"]


def test_lifespan_waits_for_the_cancelled_task_before_returning():
    async def scenario():
        async with app.router.lifespan_context(app):
            tasks = [t for t in asyncio.all_tasks() if t.get_name() == "upload-cleanup"]
            assert len(tasks) == 1
            assert not tasks[0].done()
        # Checked while the event loop still runs, so nothing else could
        # have cancelled the task for us.
        assert tasks[0].cancelled()
        assert asyncio.all_tasks() == {asyncio.current_task()}

    asyncio.run(scenario())


def test_cleanup_interval_defaults_to_five_minutes(monkeypatch):
    monkeypatch.delenv(INTERVAL_ENV, raising=False)
    assert upload._read_upload_cleanup_interval() == 300


def test_cleanup_interval_reads_positive_whole_seconds(monkeypatch):
    monkeypatch.setenv(INTERVAL_ENV, "45")
    assert upload._read_upload_cleanup_interval() == 45


@pytest.mark.parametrize("raw", ["abc", "1.5", "", "0", "-5"])
def test_invalid_cleanup_interval_falls_back_to_default(monkeypatch, caplog, raw):
    monkeypatch.setenv(INTERVAL_ENV, raw)
    with caplog.at_level(logging.WARNING, logger="app.routers.upload"):
        assert upload._read_upload_cleanup_interval() == 300
    assert INTERVAL_ENV in caplog.text
