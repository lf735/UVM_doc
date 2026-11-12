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
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_VIEW = BASE_DIR / "examples_view"


class _SourceNotesParser(HTMLParser):
    """Lightweight stdlib HTML parser to inspect .example-source-notes blocks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found_notes_box = False
        self.has_badge = False
        self.found_body = False
        self.body_chunks = []
        self._notes_depth = 0
        self._body_depth = 0

    VOID_TAGS = frozenset({
        "area", "base", "br", "col", "embed", "hr", "img",
        "input", "link", "meta", "param", "source", "track", "wbr"
    })

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        classes = set((attr_map.get("class") or "").split())
        is_void = tag.lower() in self.VOID_TAGS

        if self._notes_depth > 0:
            if not is_void:
                self._notes_depth += 1
        elif "example-source-notes" in classes:
            self.found_notes_box = True
            self._notes_depth = 1

        if self._notes_depth > 0:
            if "notes-file-badge" in classes and attr_map.get("data-file"):
                self.has_badge = True
            if self._body_depth > 0:
                if not is_void:
                    self._body_depth += 1
            elif "source-notes-body" in classes:
                self.found_body = True
                self._body_depth = 1

    def handle_endtag(self, tag):
        if self._body_depth > 0:
            self._body_depth -= 1
        if self._notes_depth > 0:
            self._notes_depth -= 1

    def handle_data(self, data):
        if self._body_depth > 0:
            self.body_chunks.append(data)

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
        parser = _SourceNotesParser()
        parser.feed(content)
        parser.close()

        if not parser.found_notes_box:
            failures.append(f"{rel}: Missing .example-source-notes container")
            continue

        if not parser.has_badge:
            failures.append(f"{rel}: Missing or empty .notes-file-badge")
            continue

        body_raw = "".join(parser.body_chunks)
        if not parser.found_body or not body_raw.strip():
            failures.append(f"{rel}: Empty .source-notes-body")
            continue

        body_text = body_raw.lower()
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

