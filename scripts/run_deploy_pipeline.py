#!/usr/bin/env python3
"""
Local deployment & build pipeline runner.
Reproduces the build and verification steps executed by .github/workflows/deploy.yml.
Works seamlessly across Windows, Linux, and macOS.
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_step(step_name: str, cmd: list[str]) -> None:
    print(f"\n==================================================")
    print(f"▶ Step: {step_name}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"==================================================")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"\n❌ Error: Step '{step_name}' failed with exit code {result.returncode}.", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"✔ Step '{step_name}' completed successfully.")

def main() -> None:
    python_exe = sys.executable

    # 1. Install / ensure dependencies
    run_step(
        "Install RAG embedding dependencies",
        [python_exe, "-m", "pip", "install", "-r", "requirements-ci.txt"]
    )

    # 2. Generate search data, modern docs views and source views
    run_step(
        "Generate search data and views",
        [python_exe, "scripts/build_docs.py"]
    )

    # 3. Generate RAG embeddings database
    run_step(
        "Generate RAG embeddings database",
        [python_exe, "scripts/build_rag_embeddings.py"]
    )

    # 4. Verify generated search, symbol, and RAG assets
    print(f"\n==================================================")
    print(f"▶ Step: Verify generated search, symbol, and RAG assets")
    print(f"==================================================")

    required_files = [
        BASE_DIR / "js" / "search_data.js",
        BASE_DIR / "js" / "uvm_symbol_quick.js",
        BASE_DIR / "data" / "rag_chunks.json",
        BASE_DIR / "data" / "rag_embeddings.bin"
    ]

    missing = []
    for filepath in required_files:
        if not filepath.is_file() or filepath.stat().st_size == 0:
            missing.append(filepath)
        else:
            size_kb = filepath.stat().st_size / 1024
            size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
            print(f"  [OK] {filepath.relative_to(BASE_DIR)} ({size_str})")

    doc_topics_dir = BASE_DIR / "js" / "doc_topics"
    topic_files = list(doc_topics_dir.glob("*.js")) if doc_topics_dir.is_dir() else []
    if not topic_files:
        missing.append(doc_topics_dir)
    else:
        print(f"  [OK] {doc_topics_dir.relative_to(BASE_DIR)} ({len(topic_files)} topic bundles)")

    if missing:
        print("\n❌ Error: The following expected build assets are missing:", file=sys.stderr)
        for m in missing:
            print(f"  - {m.relative_to(BASE_DIR)}", file=sys.stderr)
        sys.exit(1)

    print("\n🎉 All deploy.yml build steps executed and verified successfully!")

if __name__ == "__main__":
    main()

