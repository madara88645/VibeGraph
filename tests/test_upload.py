import httpx

BASE_URL = "http://localhost:8000"


def test_case_a_single_file():
    print("Running Case A: Single File Upload...")
    file_path = "tests/upload_cases/case_a.py"
    with open(file_path, "rb") as f:
        files = {"files": ("case_a.py", f, "text/x-python")}
        response = httpx.post(
            f"{BASE_URL}/api/upload-project", files=files, timeout=30.0
        )

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "nodes" in data
    print("Case A: Passed!")


def test_case_b_multi_file():
    print("Running Case B: Multi-File Folder Upload...")
    f1 = open("tests/upload_cases/lib/core.py", "rb")
    f2 = open("tests/upload_cases/lib/utils.py", "rb")
    files = [
        ("files", ("lib/core.py", f1, "text/x-python")),
        ("files", ("lib/utils.py", f2, "text/x-python")),
    ]
    try:
        response = httpx.post(
            f"{BASE_URL}/api/upload-project", files=files, timeout=30.0
        )
    finally:
        f1.close()
        f2.close()

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    node_ids = [node["id"] for node in data["nodes"]]
    assert "run_lib" in node_ids
    assert "helper" in node_ids
    print("Case B: Passed!")


def test_case_c_error_handling():
    print("Running Case C: Error Handling (Invalid Syntax)...")
    file_path = "tests/upload_cases/invalid.py"
    with open(file_path, "rb") as f:
        files = {"files": ("invalid.py", f, "text/x-python")}
        response = httpx.post(
            f"{BASE_URL}/api/upload-project", files=files, timeout=30.0
        )

    print(f"Response status: {response.status_code}")
    assert (
        response.status_code == 400
    ), f"Expected 400, got {response.status_code}: {response.text}"
    assert "Syntax error" in response.json()["detail"]
    print("Case C: Passed!")


if __name__ == "__main__":
    try:
        test_case_a_single_file()
        test_case_b_multi_file()
        test_case_c_error_handling()
        print("\nSUCCESS: All Project Upload verification cases passed!")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
