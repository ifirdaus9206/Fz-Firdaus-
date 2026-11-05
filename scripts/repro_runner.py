import sys, traceback
sys.path.insert(0, "scripts")
import run_tests_parallel as R
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

root = Path(".").resolve()
f = Path("tests/test_install_macos_launcher.py").resolve()
try:
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(R._run_one_file, f, ["-q"], root, 60.0, 0)
        fpath, rc, output, summary, wall = fut.result()
    print("RC:", rc, "| summary:", summary)
    print(output[-400:])
except Exception:
    traceback.print_exc()
