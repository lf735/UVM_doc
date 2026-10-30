#!/usr/bin/env python3
"""
UVM 1.2 Documentation RAG Embeddings & Intelligent Chunker Generator
Parses modernized HTML documentation in docs_view/ to extract:
- Conceptual overviews (architecture, phasing, factory, TLM, sequences)
- Class definitions and hierarchies
- Methods, tasks, and functions with prototypes and descriptions
- Macro specifications
Computes 384-dimensional normalized embeddings using fastembed (all-MiniLM-L6-v2)
and writes:
- data/rag_chunks.json (Metadata, URLs, anchors, clean text snippets)
- data/rag_embeddings.bin (Raw Float32 contiguous vectors)
"""

import os
import re
import sys
import html
import json
import struct
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_VIEW_DIR = BASE_DIR / "docs_view"
DATA_DIR = BASE_DIR / "data"

def clean_html(raw_html: str) -> str:
    """Strip HTML tags, unescape entities, and normalize whitespace."""
    if not raw_html:
        return ""
    # Remove script and style elements
    text = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>', ' ', raw_html, flags=re.IGNORECASE)
    # Replace block breaks with space
    text = re.sub(r'<(br|p|div|tr|li|h[1-6])\b[^>]*>', ' ', text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Unescape entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def extract_chunks():
    """Extract structured semantic chunks from docs_view/."""
    print("Extracting intelligent semantic chunks from docs_view/...")
    if not DOCS_VIEW_DIR.exists():
        raise FileNotFoundError(f"docs_view directory not found at {DOCS_VIEW_DIR}")

    chunks = []
    chunk_id = 0

    # 1. Process Overviews (Highest Conceptual Value)
    overviews_dir = DOCS_VIEW_DIR / "overviews"
    if overviews_dir.exists():
        for f in sorted(overviews_dir.glob("*.html")):
            rel_file = f"docs_view/overviews/{f.name}"
            try:
                with open(f, 'r', encoding='utf-8') as ofile:
                    content = ofile.read()
            except Exception as e:
                print(f"Error reading {f}: {e}")
                continue

            # Extract main title
            title_m = re.search(r'<h1[^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h1>', content, re.IGNORECASE)
            title = clean_html(title_m.group(1)) if title_m else f.stem.replace("-txt", "").capitalize()

            # Split by CTopic sections if present, or take entire body
            topics = re.findall(r'<div class=["\']?CTopic["\']?[^>]*>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
            if not topics:
                topics = [content]

            for idx, top in enumerate(topics):
                # Extract sub-heading or anchor
                sub_title_m = re.search(r'<h[1-4][^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', top, re.IGNORECASE)
                sub_title = clean_html(sub_title_m.group(1)) if sub_title_m else title

                anchor_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', top, re.IGNORECASE)
                anchor = anchor_m.group(1) if anchor_m else f"section_{idx}"

                clean_text = clean_html(top)
                # Skip trivial or empty sections
                if len(clean_text) < 50:
                    continue

                # Contextual retrieval header
                context_header = f"[UVM 1.2 Architecture Guide] [Overview: {title}] [Topic: {sub_title}]"

                chunks.append({
                    "id": chunk_id,
                    "title": sub_title,
                    "class": title,
                    "category": "Conceptual Overview",
                    "type": "overview",
                    "url": f"{rel_file}#{anchor}",
                    "anchor": anchor,
                    "breadcrumb": f"Overviews > {title} > {sub_title}",
                    "text": clean_text[:1200],  # Bound length for embedding quality
                    "context_header": context_header
                })
                chunk_id += 1

    # 2. Process Classes, Methods, Macros in other subdirectories
    for root, dirs, files in os.walk(DOCS_VIEW_DIR):
        root_path = Path(root)
        if root_path.name == "overviews" or root_path.name == "images":
            continue

        for f in sorted(files):
            if not f.endswith('.html'):
                continue

            full_file = root_path / f
            rel_file = full_file.relative_to(BASE_DIR).as_posix()
            category = root_path.name.capitalize()

            try:
                with open(full_file, 'r', encoding='utf-8') as cfile:
                    content = cfile.read()
            except Exception as e:
                print(f"Error reading {full_file}: {e}")
                continue

            # Extract main class/topic
            main_title_m = re.search(r'id=["\']?MainTopic["\']?[\s\S]*?<h[1-4] class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', content, re.IGNORECASE)
            main_title = clean_html(main_title_m.group(1)) if main_title_m else f.stem

            # Extract Main Topic Overview Chunk
            main_body_m = re.search(r'<div class=["\']?CTopic["\']? id=["\']?MainTopic["\']?>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
            if main_body_m:
                main_text = clean_html(main_body_m.group(1))
                if len(main_text) >= 40:
                    context_header = f"[UVM 1.2 Class Reference] [Class: {main_title}] [Category: {category}] Overview & Hierarchy:"
                    chunks.append({
                        "id": chunk_id,
                        "title": main_title,
                        "class": main_title,
                        "category": category,
                        "type": "class",
                        "url": f"{rel_file}#MainTopic",
                        "anchor": "MainTopic",
                        "breadcrumb": f"{category} > {main_title}",
                        "text": main_text[:1200],
                        "context_header": context_header
                    })
                    chunk_id += 1

            # Extract specific CTopics (Methods, Tasks, Macros, Variables)
            topic_divs = re.finditer(r'<div class=["\']?(C[A-Za-z0-9_]+)["\']?[^>]*>\s*<div class=["\']?CTopic["\']?[^>]*>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
            for m in topic_divs:
                cls_type = m.group(1)  # CMethod, CFunction, CTask, CMacro, CVariable, etc.
                topic_html = m.group(2)

                # Skip Summary or main topic already captured
                if 'id="MainTopic"' in topic_html or 'id=MainTopic' in topic_html:
                    continue

                sub_m = re.search(r'<h[1-4]\b[^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', topic_html, re.IGNORECASE)
                if not sub_m:
                    continue
                sub_title = clean_html(sub_m.group(1))
                if not sub_title:
                    continue

                anchor_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', sub_m.group(1), re.IGNORECASE)
                anchor = anchor_m.group(1) if anchor_m else sub_title

                topic_text = clean_html(topic_html)
                if len(topic_text) < 40:
                    continue

                # Type classification
                inferred_type = "method"
                if "macro" in cls_type.lower() or sub_title.startswith("`"):
                    inferred_type = "macro"
                elif "task" in cls_type.lower():
                    inferred_type = "task"
                elif "function" in cls_type.lower():
                    inferred_type = "function"
                elif "class" in cls_type.lower():
                    inferred_type = "class"

                context_header = f"[UVM 1.2 {inferred_type.capitalize()}] [{main_title}::{sub_title}] Class: {main_title}. Category: {category}."

                chunks.append({
                    "id": chunk_id,
                    "title": sub_title,
                    "class": main_title,
                    "category": category,
                    "type": inferred_type,
                    "url": f"{rel_file}#{anchor}",
                    "anchor": anchor,
                    "breadcrumb": f"{category} > {main_title} > {sub_title}",
                    "text": topic_text[:1000],
                    "context_header": context_header
                })
                chunk_id += 1

    print(f"Extracted {len(chunks)} structured semantic chunks.")
    return chunks

def generate_embeddings(chunks, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """Compute dense normalized 384-d embeddings using fastembed."""
    print(f"Initializing embedding model: {model_name}...")
    try:
        from fastembed import TextEmbedding
    except ImportError:
        print("Error: fastembed is not installed. Please install it with 'pip install fastembed'.", file=sys.stderr)
        sys.exit(1)

    model = TextEmbedding(model_name)

    # Format texts for embedding by prepending contextual retrieval header
    texts = [f"{c['context_header']} {c['text']}" for c in chunks]
    print(f"Computing embeddings for {len(texts)} texts in batches...")

    embeddings_gen = model.embed(texts, batch_size=64)
    embeddings = list(embeddings_gen)

    print(f"Computed {len(embeddings)} vectors with dimension {len(embeddings[0])}.")
    return embeddings

def save_data(chunks, embeddings):
    """Save chunks metadata JSON and contiguous binary float32 embeddings."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    chunks_file = DATA_DIR / "rag_chunks.json"
    embeddings_file = DATA_DIR / "rag_embeddings.bin"

    # 1. Save chunks JSON
    with open(chunks_file, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved {chunks_file} ({chunks_file.stat().st_size / 1024:.1f} KB).")

    # 2. Save contiguous binary Float32Array (dim = 384)
    with open(embeddings_file, 'wb') as f:
        for vec in embeddings:
            f.write(struct.pack(f"{len(vec)}f", *vec))
    print(f"Saved {embeddings_file} ({embeddings_file.stat().st_size / 1024:.1f} KB).")

def main():
    parser = argparse.ArgumentParser(description="Generate UVM 1.2 RAG Embeddings & Intelligent Chunks")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Fastembed model name")
    args = parser.parse_args()

    print("=" * 60)
    print("  UVM 1.2 RAG Chunker & Embedding Generator")
    print("=" * 60)

    chunks = extract_chunks()
    if not chunks:
        print("Error: No chunks extracted!", file=sys.stderr)
        sys.exit(1)

    embeddings = generate_embeddings(chunks, model_name=args.model)
    save_data(chunks, embeddings)

    print("=" * 60)
    print("  RAG embeddings generation completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()

