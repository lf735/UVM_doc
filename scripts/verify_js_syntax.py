#!/usr/bin/env python3
"""
Verification script for JavaScript Syntax & Redeclaration Hygiene.
Validates all JS bundles in js/ (including js/doc_topics/) and inline <script>
blocks in root HTML pages using Node.js V8 parser (`node --check` / `vm.Script`)
to catch SyntaxError, duplicate `const`/`let` declarations, and malformed scripts
before deployment.
"""

import os
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
JS_DIR = BASE_DIR / "js"
DOC_TOPICS_DIR = JS_DIR / "doc_topics"
ROOT_HTML_FILES = [
    "index.html",
    "home.html",
    "mobile_preview.html",
    "uvm_database_explorer.html",
]


class InlineScriptExtractor(HTMLParser):
    """Extract inline <script> blocks (without src attribute) from an HTML file."""

    def __init__(self) -> None:
        super().__init__()
        self._in_inline_script = False
        self._current_chunks: list[str] = []
        self._current_line = 1
        self.scripts: list[tuple[int, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            attr_dict = {k.lower(): v for k, v in attrs}
            script_type = (attr_dict.get("type") or "").strip().lower()
            is_js = script_type in ("", "text/javascript", "application/javascript", "module")
            if "src" not in attr_dict and is_js:
                self._in_inline_script = True
                self._current_chunks = []
                self._current_line = self.getpos()[0]

    def handle_data(self, data: str) -> None:
        if self._in_inline_script:
            self._current_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_inline_script:
            code = "".join(self._current_chunks)
            if code.strip():
                self.scripts.append((self._current_line, code))
            self._in_inline_script = False
            self._current_chunks = []


def check_top_level_js(node_bin: str) -> list[str]:
    """Run `node --check` on every top-level .js file in js/."""
    failures: list[str] = []
    js_files = sorted(JS_DIR.glob("*.js"))
    assert js_files, f"No .js files found in {JS_DIR}"

    for js_file in js_files:
        proc = subprocess.run(
            [node_bin, "--check", str(js_file)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            err_msg = (proc.stderr or proc.stdout).strip()
            failures.append(f"{js_file.relative_to(BASE_DIR)}:\n{err_msg}")
    print(f"  [PASS] Checked {len(js_files)} top-level js/*.js files via `node --check`")
    return failures


def check_doc_topics_js(node_bin: str) -> list[str]:
    """Validate all js/doc_topics/*.js bundles in a single Node vm.Script pass."""
    if not DOC_TOPICS_DIR.is_dir():
        print("  [SKIP] js/doc_topics/ directory not present")
        return []

    topic_files = sorted(DOC_TOPICS_DIR.glob("*.js"))
    if not topic_files:
        print("  [SKIP] No .js files in js/doc_topics/")
        return []

    node_script = (
        "const fs = require('fs');\n"
        "const vm = require('vm');\n"
        "const files = fs.readFileSync(0, 'utf8').split(/\\r?\\n/).filter(Boolean);\n"
        "let failed = 0;\n"
        "for (const f of files) {\n"
        "  try {\n"
        "    const code = fs.readFileSync(f, 'utf8');\n"
        "    new vm.Script(code, { filename: f });\n"
        "  } catch (err) {\n"
        "    console.error(f + ': ' + err.message);\n"
        "    failed++;\n"
        "  }\n"
        "}\n"
        "process.exit(failed > 0 ? 1 : 0);\n"
    )
    payload = "\n".join(str(p) for p in topic_files) + "\n"
    proc = subprocess.run(
        [node_bin, "-e", node_script],
        input=payload,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        err_msg = (proc.stderr or proc.stdout).strip()
        return [f"js/doc_topics/*.js:\n{err_msg}"]
    print(f"  [PASS] Checked {len(topic_files)} js/doc_topics/*.js bundles via V8 vm.Script")
    return []


def check_inline_html_scripts(node_bin: str) -> list[str]:
    """Validate inline <script> blocks in root HTML files via V8 vm.Script."""
    failures: list[str] = []
    checked_blocks = 0

    node_script = (
        "const fs = require('fs');\n"
        "const vm = require('vm');\n"
        "const code = fs.readFileSync(0, 'utf8');\n"
        "const filename = process.argv[1] || 'inline.js';\n"
        "try {\n"
        "  new vm.Script(code, { filename });\n"
        "} catch (err) {\n"
        "  console.error(err.message);\n"
        "  process.exit(1);\n"
        "}\n"
    )

    for rel_name in ROOT_HTML_FILES:
        html_path = BASE_DIR / rel_name
        if not html_path.is_file():
            continue
        parser = InlineScriptExtractor()
        parser.feed(html_path.read_text(encoding="utf-8", errors="replace"))
        for line_no, code in parser.scripts:
            checked_blocks += 1
            label = f"{rel_name}:inline-script@L{line_no}"
            proc = subprocess.run(
                [node_bin, "-e", node_script, label],
                input=code,
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode != 0:
                err_msg = (proc.stderr or proc.stdout).strip()
                failures.append(f"{label}: {err_msg}")

    print(f"  [PASS] Checked {checked_blocks} inline <script> blocks across root HTML files")
    return failures


def find_node_binary() -> str | None:
    node_bin = shutil.which("node")
    if node_bin:
        return node_bin
    candidates = [
        Path(r"C:\Program Files\nodejs\node.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs" / "node.exe",
        Path(os.environ.get("NVM_SYMLINK", "")) / "node.exe",
    ]
    for cand in candidates:
        if cand.is_file():
            return str(cand)
    return None


def main() -> int:
    node_bin = find_node_binary()
    if not node_bin:
        msg = "Node.js (`node`) not found in PATH; cannot run V8 JS syntax verification."
        if os.environ.get("CI"):
            print(f"  [FAIL] {msg}", file=sys.stderr)
            return 1
        print(f"  [WARN] {msg}")
        return 0

    failures: list[str] = []
    failures.extend(check_top_level_js(node_bin))
    failures.extend(check_doc_topics_js(node_bin))
    failures.extend(check_inline_html_scripts(node_bin))

    if failures:
        print("\n[FAIL] JavaScript syntax errors detected:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        return 1

    print("ALL JAVASCRIPT SYNTAX CHECKS PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
