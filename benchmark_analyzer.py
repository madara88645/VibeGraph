import time
import os
from analyst.analyzer import CodeAnalyzer
import tempfile

def run_benchmark():
    analyzer = CodeAnalyzer()

    with tempfile.TemporaryDirectory() as target_dir:
        for i in range(500):
            with open(os.path.join(target_dir, f"file_{i}.py"), "w") as f:
                for j in range(20):
                    f.write(f"import module_{j}\n")
                    f.write(f"from package_{j} import thing\n")

        start = time.perf_counter()

        # analyze deps for all files
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".py"):
                    analyzer.extract_dependencies(os.path.join(root, file), target_dir)

        end = time.perf_counter()
        return end - start

if __name__ == "__main__":
    duration = run_benchmark()
    print(f"Baseline: {duration:.3f} seconds")
