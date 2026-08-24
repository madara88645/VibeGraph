import json
import sys


def main():
    try:
        with open("testing_report.json", "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("Error: Root must be a JSON array")
            sys.exit(1)
    except FileNotFoundError:
        print("Error: testing_report.json not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
