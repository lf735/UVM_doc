#!/usr/bin/env python3
"""
Verify Source Specification & Design Notes across all 39 interactive example pages.
Ensures:
1. Every example page contains the '.example-source-notes' container.
2. Every notes block has a valid source file badge (e.g. data-file="test.sv").
3. No Apache 2.0 license text or legal boilerplate leaked into the notes.
4. Content is non-empty and well-structured.
"""

import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_VIEW = BASE_DIR / "examples_view"

def verify_source_notes():
    html_files = sorted(EXAMPLES_VIEW.glob("*/*.html"))
    total_suites = len(html_files)
    print("=" * 60)
    print(f"  Verifying Source Specification & Design Notes ({total_suites} suites)")
    print("=" * 60)

    if total_suites < 39:
        print(f"  [FAIL] Expected at least 39 suites, found {total_suites}")
        return False

    failures = []
    license_leaks = []

    license_markers = [
        "licensed under the apache",
        "all rights reserved",
        "mentor graphics corporation",
        "synopsys, inc.",
        "cadence design systems",
        "limitations under the license"
    ]

    for p in html_files:
        rel = p.relative_to(EXAMPLES_VIEW)
        content = p.read_text(encoding="utf-8")
        soup = BeautifulSoup(content, "html.parser")

        notes_box = soup.find(class_="example-source-notes")
        if not notes_box:
            failures.append(f"{rel}: Missing .example-source-notes container")
            continue

        badge = notes_box.find(class_="notes-file-badge")
        if not badge or not badge.get("data-file"):
            failures.append(f"{rel}: Missing or empty .notes-file-badge")
            continue

        body = notes_box.find(class_="source-notes-body")
        if not body or not body.get_text(strip=True):
            failures.append(f"{rel}: Empty .source-notes-body")
            continue

        body_text = body.get_text().lower()
        for marker in license_markers:
            if marker in body_text:
                license_leaks.append(f"{rel}: Leaked license text '{marker}'")
                break

    if failures:
        print(f"  [FAIL] {len(failures)} suites failed structure validation:")
        for f in failures[:10]:
            print(f"    - {f}")
        return False

    if license_leaks:
        print(f"  [FAIL] {len(license_leaks)} suites contain leaked license text:")
        for l in license_leaks[:10]:
            print(f"    - {l}")
        return False

    print(f"  [PASS] All {total_suites} example suites contain valid, structured Source Notes")
    print("  [PASS] Zero Apache 2.0 license boilerplate leaks detected")
    print("  [PASS] All source file badges and data-file attributes verified")
    print("=" * 60)
    print("  Source Notes Integration: 100% SUCCESS")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = verify_source_notes()
    sys.exit(0 if success else 1)

