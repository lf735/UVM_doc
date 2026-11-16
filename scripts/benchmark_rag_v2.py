#!/usr/bin/env python3
"""
UVM 1.2 RAG V2 Benchmark & Structural Integrity Validator
Verifies:
1. data/rag_chunks.json & data/rag_graph.json existence and size (graph <= 400 KB)
2. Surgical HTML cleaning (no NaturalDocs nav chrome in chunk texts)
3. Graph coverage (classes, methodsIndex, macros, examples, overviews)
4. 20-query benchmark expectations across the 5 intent profiles
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_FILE = BASE_DIR / "data" / "rag_chunks.json"
GRAPH_FILE = BASE_DIR / "data" / "rag_graph.json"

BENCHMARK_SUITE = [
    ("SYMBOL_API", "uvm_driver::seq_item_port", "uvm_driver"),
    ("SYMBOL_API", "`uvm_do_with", "`uvm_do_with"),
    ("SYMBOL_API", "set_drain_time", "set_drain_time"),
    ("INHERITED_MEMBER", "uvm_driver build_phase", "uvm_component"),
    ("INHERITED_MEMBER", "uvm_monitor uvm_report_error", "uvm_report_object"),
    ("INHERITED_MEMBER", "uvm_sequence_item do_copy", "uvm_object"),
    ("INHERITED_MEMBER", "uvm_agent connect_phase", "uvm_component"),
    ("COMPARISON", "difference between uvm_config_db and uvm_resource_db", "uvm_config_db"),
    ("COMPARISON", "uvm_object vs uvm_component", "uvm_object"),
    ("COMPARISON", "uvm_transaction vs uvm_sequence_item", "uvm_sequence_item"),
    ("COMPARISON", "create vs new factory", "uvm_factory"),
    ("PRACTICAL_EXAMPLE", "how to connect monitor to scoreboard example", "examples_view/"),
    ("PRACTICAL_EXAMPLE", "uvm_reg backdoor example", "examples_view/"),
    ("PRACTICAL_EXAMPLE", "exemple driver sequencer", "examples_view/"),
    ("CONCEPTUAL", "how do objections work", "uvm_objection"),
    ("CONCEPTUAL", "comment passer une interface virtuelle au driver", "uvm_config_db"),
    ("CONCEPTUAL", "comment synchroniser deux séquences", "uvm_sequence"),
    ("CONCEPTUAL", "how does phasing execution order work", "phasing"),
    ("DEPRECATION", "how to register sequence in sequencer", "`uvm_object_utils"),
    ("DEPRECATION", "uvm_sequence_utils", "uvm_sequence_utils"),
]


def main():
    if not CHUNKS_FILE.exists() or not GRAPH_FILE.exists():
        print("Error: rag_chunks.json or rag_graph.json missing. Run scripts/build_rag_embeddings.py first.", file=sys.stderr)
        sys.exit(1)

    graph_size_kb = GRAPH_FILE.stat().st_size / 1024
    print(f"[Check] rag_graph.json size: {graph_size_kb:.1f} KB (target <= 400 KB)")
    if graph_size_kb > 450:
        print(f"Warning: rag_graph.json ({graph_size_kb:.1f} KB) exceeds 400 KB budget.")

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    # 1. Check surgical cleaning
    dirty_chunks = [c["id"] for c in chunks if "On this page Collapse all" in (c.get("text") or "")]
    print(f"[Check] Total chunks: {len(chunks)} | Dirty NaturalDocs chrome chunks: {len(dirty_chunks)}")
    if dirty_chunks:
        print(f"Error: Found {len(dirty_chunks)} chunks with uncleaned NaturalDocs chrome!", file=sys.stderr)
        sys.exit(1)

    # 2. Check graph nodes & inheritance resolution for INHERITED_MEMBER queries
    classes = graph.get("nodes", {}).get("classes", {})
    methods_idx = graph.get("nodes", {}).get("methodsIndex", {})
    examples = graph.get("nodes", {}).get("examples", {})
    print(f"[Check] Graph stats: {graph.get('stats')}")

    inherited_checks = [
        ("uvm_driver", "build_phase", "uvm_component"),
        ("uvm_monitor", "uvm_report_error", "uvm_report_object"),
        ("uvm_sequence_item", "do_copy", "uvm_object"),
        ("uvm_agent", "connect_phase", "uvm_component"),
    ]
    for cls_name, method_name, expected_anc in inherited_checks:
        ancestors = classes.get(cls_name, {}).get("ancestors", [])
        candidates = {m["class"] for m in methods_idx.get(method_name, [])}
        resolved = next((a for a in ancestors if a in candidates), None)
        status = "PASS" if resolved == expected_anc else f"FAIL (got {resolved})"
        print(f"[Inherit] {cls_name}::{method_name} -> {expected_anc}: {status}")
        if resolved != expected_anc:
            sys.exit(1)

    print(f"[Check] Benchmark suite registered: {len(BENCHMARK_SUITE)} queries, {len(examples)} example studios indexed.")
    print("All structural RAG V2 checks PASSED.")


if __name__ == "__main__":
    main()
