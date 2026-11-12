#!/usr/bin/env python3
"""
Unified test runner for UVM 1.2 Interactive Documentation.
Executes all unit and DOM/integration verification scripts in scripts/
and returns a non-zero exit code if any suite fails.
"""

import sys
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"

TEST_SUITES = [
    ("Syntax Highlighter Unit Tests", "test_syntax_highlighter.py"),
    ("Code Containers Verification", "verify_code_containers.py"),
    ("Code Editor Tools & Clickable Symbols", "verify_code_editor_tools.py"),
    ("Interactive Examples Studios", "verify_examples.py"),
    ("Inherited Members & Class Hierarchy", "verify_inherited_members.py"),
    ("Search Pilot & Session Persistence", "verify_search_pilot.py"),
    ("Source Notes & License Hygiene", "verify_source_notes.py"),
    ("Stepper Calibration & Log Sync", "verify_stepper_calibration.py"),
]


def run_suite(label: str, script_name: str) -> tuple[bool, float]:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.is_file():
        print(f"  [FAIL] Missing script: {script_path.relative_to(BASE_DIR)}", file=sys.stderr)
        return False, 0.0

    print(f"\n--- [{label}] ({script_name}) ---")
    t0 = time.monotonic()
    result = subprocess.run([sys.executable, str(script_path)], cwd=BASE_DIR)
    elapsed = time.monotonic() - t0
    ok = result.returncode == 0
    return ok, elapsed


def main() -> int:
    print("=" * 64)
    print("  UVM 1.2 Interactive Documentation — Unified Test Runner")
    print("=" * 64)

    results = []
    for label, script_name in TEST_SUITES:
        ok, elapsed = run_suite(label, script_name)
        results.append((label, script_name, ok, elapsed))

    print("\n" + "=" * 64)
    print("  Test Summary")
    print("=" * 64)
    failed = 0
    for label, script_name, ok, elapsed in results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{status}] {label:<40} ({elapsed:.2f}s)")

    total = len(results)
    passed = total - failed
    print("-" * 64)
    print(f"  Result: {passed}/{total} suites passed.")
    print("=" * 64)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

