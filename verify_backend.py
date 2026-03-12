import requests
import sys

BASE_URL = "http://localhost:8000"


def test_health():
    try:
        resp = requests.get(f"{BASE_URL}/api/health")
        if resp.status_code == 200 and resp.json().get("status") == "ok":
            print("[PASS] Health Check")
            return True
        else:
            print(f"[FAIL] Health Check: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Health Check Exception: {e}")
        return False


def test_explain():
    payload = {"file_path": "main.py", "node_id": "main", "level": "intermediate"}
    try:
        resp = requests.post(f"{BASE_URL}/api/explain", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            if "explanation" in data and "snippet" in data:
                print("[PASS] Explain API")
                return True
            else:
                print(f"[FAIL] Explain API missing keys: {data.keys()}")
                return False
        else:
            print(f"[FAIL] Explain API: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Explain API Exception: {e}")
        return False


if __name__ == "__main__":
    print("Running Backend Verification...")
    h = test_health()
    e = test_explain()

    if h and e:
        print("\nBackend Verification: SUCCESS")
        sys.exit(0)
    else:
        print("\nBackend Verification: FAILED")
        sys.exit(1)
