"""Zip members the analyzer never reads are skipped instead of failing the upload.

.git, node_modules and the other IGNORED_DIRS folders, a git submodule's
``.git`` file and .env templates are left out of the extraction, while
traversal, symlinks and real secrets files still reject the whole zip.
"""

import os
import shutil
import stat
import tempfile
import zipfile
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from analyst.analyzer import IGNORED_DIRS
from app.routers import upload
from serve import app

client = TestClient(app)

APP_SOURCE = "def run():\n    return helper()\n\n\ndef helper():\n    return 1\n"


@pytest.fixture
def upload_dirs(monkeypatch):
    """Record the temp dirs the endpoint extracts into, and remove them after."""
    created = []
    real_mkdtemp = tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(upload.tempfile, "mkdtemp", recording_mkdtemp)
    yield created
    for path in created:
        shutil.rmtree(path, ignore_errors=True)


def _zip(entries):
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries:
            zf.writestr(name, data)
    archive.seek(0)
    return archive


def _post(archive):
    return client.post(
        "/api/upload-project",
        files={"files": ("project.zip", archive, "application/zip")},
    )


def _on_disk(root):
    """Relative paths of every file and folder under root."""
    found = set()
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            found.add(rel.replace(os.sep, "/"))
    return found


def _node_ids(response):
    return {node["id"] for node in response.json()["nodes"]}


def test_git_folder_and_submodule_git_file_are_skipped(upload_dirs):
    response = _post(
        _zip(
            [
                (".git/", ""),
                (".git/config", "[core]\n"),
                (".git/HEAD", "ref: refs/heads/main\n"),
                (".git/objects/ab/cdef", "blob"),
                (".git\\hooks\\pre-commit", "#!/bin/sh\n"),
                ("vendor/lib/.git", "gitdir: ../../.git/modules/lib\n"),
                ("vendor/lib/util.py", "def util():\n    return 2\n"),
                ("app.py", APP_SOURCE),
            ]
        )
    )

    assert response.status_code == 200, response.text
    assert {"run", "helper", "util"} <= _node_ids(response)
    assert _on_disk(upload_dirs[0]) == {
        "app.py",
        "vendor",
        "vendor/lib",
        "vendor/lib/util.py",
    }


def test_ignored_dirs_are_skipped_at_any_depth(upload_dirs):
    entries = [
        (f"pkg/{name}/skipped.py", "def skipped():\n    pass\n")
        for name in sorted(IGNORED_DIRS)
    ]
    entries.append(("pkg/app.py", APP_SOURCE))

    response = _post(_zip(entries))

    assert response.status_code == 200, response.text
    assert "skipped" not in _node_ids(response)
    assert _on_disk(upload_dirs[0]) == {"pkg", "pkg/app.py"}


def test_node_modules_above_the_zip_file_cap_is_skipped(upload_dirs):
    entries = [
        (f"node_modules/pkg_{i}/index.js", "") for i in range(upload.MAX_ZIP_FILES + 1)
    ]
    entries += [("src/app.py", APP_SOURCE), ("src/web.js", "export const a = 1;\n")]

    response = _post(_zip(entries))

    assert response.status_code == 200, response.text
    assert {"run", "helper"} <= _node_ids(response)
    assert _on_disk(upload_dirs[0]) == {"src", "src/app.py", "src/web.js"}


def test_skipped_members_do_not_count_toward_the_uncompressed_budget(upload_dirs):
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        # Above the endpoint's 100 MB uncompressed budget; compresses to ~100 KB.
        with zf.open("node_modules/big/blob.bin", "w") as blob:
            for _ in range(101):
                blob.write(bytes(1024 * 1024))
        zf.writestr("app.py", APP_SOURCE)
    archive.seek(0)

    response = _post(archive)

    assert response.status_code == 200, response.text
    assert _on_disk(upload_dirs[0]) == {"app.py"}


@pytest.mark.parametrize(
    "template",
    [".env.example", ".ENV.Sample", "proj/.env.template", "config/.env.dist"],
)
def test_env_templates_are_skipped(upload_dirs, template):
    response = _post(_zip([(template, "API_KEY=changeme\n"), ("app.py", APP_SOURCE)]))

    assert response.status_code == 200, response.text
    assert {"run", "helper"} <= _node_ids(response)
    on_disk = _on_disk(upload_dirs[0])
    assert not any(".env" in path.lower() for path in on_disk), on_disk
    assert "app.py" in on_disk


@pytest.mark.parametrize(
    "secret",
    [
        ".env",
        "proj/.env.local",
        ".ENV.Production",
        ".ssh/id_rsa",
        ".aws/credentials",
        "proj/.npmrc",
    ],
)
def test_real_secrets_still_reject_the_zip_next_to_a_template(upload_dirs, secret):
    response = _post(
        _zip(
            [
                (".env.example", "API_KEY=changeme\n"),
                (secret, "API_KEY=real\n"),
                ("app.py", APP_SOURCE),
            ]
        )
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail.startswith("Unsafe zip file detected: project.zip")
    assert not os.path.exists(upload_dirs[0])


@pytest.mark.parametrize(
    "look_alike",
    [".env.example.local", ".env.sample.bak", ".env.example/.env", ".GIT/config"],
)
def test_look_alikes_of_skipped_names_still_reject_the_zip(upload_dirs, look_alike):
    """Only exact template names and exact IGNORED_DIRS names are skipped."""
    response = _post(_zip([(look_alike, "API_KEY=real\n"), ("app.py", APP_SOURCE)]))

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail.startswith("Unsafe zip file detected: project.zip")
    assert not os.path.exists(upload_dirs[0])


def test_secrets_rejection_does_not_echo_the_member_path():
    response = _post(
        _zip([("deep/private_dir_x/.env.local", "KEY=1\n"), ("app.py", APP_SOURCE)])
    )

    assert response.status_code == 400
    assert "private_dir_x" not in response.json()["detail"]


@pytest.mark.parametrize(
    "unsafe_name",
    [
        "../evil.py",
        "node_modules/../../evil.py",
        ".git/../../evil.py",
        "node_modules\\..\\..\\evil.py",
        "/node_modules/pkg/index.js",
        "/tmp/.git/config",
    ],
)
def test_traversal_and_absolute_paths_still_win_over_skipping(upload_dirs, unsafe_name):
    response = _post(
        _zip(
            [
                (".git/config", "[core]\n"),
                (unsafe_name, "print('escaped')\n"),
                ("app.py", APP_SOURCE),
            ]
        )
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsafe zip file detected: project.zip"
    assert not os.path.exists(upload_dirs[0])


def test_symlink_inside_node_modules_still_rejects_the_zip(upload_dirs):
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        link = zipfile.ZipInfo("node_modules/.bin/tool")
        link.create_system = 3  # Unix
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(link, "/etc/passwd")
        zf.writestr("app.py", APP_SOURCE)
    archive.seek(0)

    response = _post(archive)

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsafe zip file detected: project.zip"


def test_total_zip_entries_are_capped_even_when_skipped(monkeypatch, upload_dirs):
    monkeypatch.setattr(upload, "MAX_ZIP_ENTRIES", 50)
    skipped = [(f"node_modules/pkg_{i}.js", "") for i in range(49)]

    at_cap = _post(_zip(skipped + [("app.py", APP_SOURCE)]))
    over_cap = _post(
        _zip(skipped + [("node_modules/one_more.js", ""), ("app.py", APP_SOURCE)])
    )

    assert at_cap.status_code == 200, at_cap.text
    assert over_cap.status_code == 400
    assert over_cap.json()["detail"] == "Too many entries in zip archive (max 50)"


def test_zip_with_directory_entries_is_extracted(upload_dirs):
    response = _post(
        _zip(
            [
                ("pkg/", ""),
                ("pkg/sub/", ""),
                ("pkg/sub/app.py", APP_SOURCE),
            ]
        )
    )

    assert response.status_code == 200, response.text
    root = upload_dirs[0]
    assert os.path.isdir(os.path.join(root, "pkg", "sub"))
    assert _on_disk(root) == {"pkg", "pkg/sub", "pkg/sub/app.py"}


def test_real_project_archive_is_analyzed(tmp_path, upload_dirs):
    """shutil.make_archive, like zip -r and Finder, stores folder entries."""
    project = tmp_path / "proj"
    for rel, text in {
        "src/app.py": APP_SOURCE,
        "src/web.js": "export const a = 1;\n",
        ".gitignore": "node_modules/\n",
        ".env.example": "API_KEY=changeme\n",
        ".git/config": "[core]\n",
        ".git/refs/heads/main": "0" * 40 + "\n",
        "node_modules/left-pad/index.js": "module.exports = 1;\n",
        "venv/lib/site.py": "def site():\n    pass\n",
    }.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    archive_path = shutil.make_archive(str(tmp_path / "proj"), "zip", tmp_path, "proj")

    with open(archive_path, "rb") as archive:
        response = _post(archive)

    assert response.status_code == 200, response.text
    assert {"run", "helper"} <= _node_ids(response)
    assert _on_disk(upload_dirs[0]) == {
        "proj",
        "proj/.gitignore",
        "proj/src",
        "proj/src/app.py",
        "proj/src/web.js",
    }
