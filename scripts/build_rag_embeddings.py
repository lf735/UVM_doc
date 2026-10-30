#!/usr/bin/env python3
"""
UVM 1.2 Documentation Hierarchical 2-Level RAG Embeddings Generator
Parses modernized HTML documentation in docs_view/ to extract:
- Level 1: Parent Macro-Segments (Classes & Conceptual Architecture Guides) ~1,500 chars
- Level 2: Child Functional Chunks (Methods, Tasks, Macros, Subsections) ~800-1,200 chars
Incorporate expert domain intent & synonym injection from config/rag_intent_catalog.json
Excludes noisy release notes (relnotes-txt.html) and table-of-contents summary tables.

Computes 384-dimensional normalized embeddings using fastembed (all-MiniLM-L6-v2)
and writes:
- data/rag_chunks.json (Metadata, hierarchy, URLs, anchors, clean text snippets)
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
CONFIG_DIR = BASE_DIR / "config"

def clean_html(raw_html: str) -> str:
    """Strip HTML tags, unescape entities, and normalize whitespace."""
    if not raw_html:
        return ""
    # Strip script and style elements
    text = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>', ' ', raw_html, flags=re.IGNORECASE)
    # Strip Summary table blocks entirely
    text = re.sub(r'<!--START_ND_SUMMARY[\s\S]*?<!--END_ND_SUMMARY-->', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<div class=["\']?Summary["\']?[\s\S]*?</table>\s*</div>\s*</div>', ' ', text, flags=re.IGNORECASE)
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

def load_intents():
    """Load curated domain intent catalog."""
    catalog_file = CONFIG_DIR / "rag_intent_catalog.json"
    if not catalog_file.exists():
        print("Notice: config/rag_intent_catalog.json not found, proceeding without domain intent injection.")
        return []
    try:
        with open(catalog_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        entries = data.get("entries", [])
        print(f"Loaded {len(entries)} domain intent entries from config/rag_intent_catalog.json.")
        return entries
    except Exception as e:
        print(f"Warning: Could not parse intent catalog: {e}")
        return []

def match_intents(identifier_str, catalog):
    """Find matching intent keywords for an identifier (class name, file name, topic)."""
    id_lower = identifier_str.lower().replace("-", "_").replace(".", "_")
    matched_intents = []
    matched_synonyms = []
    for entry in catalog:
        for pat in entry.get("patterns", []):
            pat_clean = pat.lower().replace("-", "_")
            if pat_clean in id_lower:
                matched_intents.extend(entry.get("intents", []))
                matched_synonyms.extend(entry.get("synonyms", []))
                break
    return list(dict.fromkeys(matched_intents))[:4], list(dict.fromkeys(matched_synonyms))[:8]

def extract_chunks():
    """Extract hierarchical semantic chunks from docs_view/."""
    print("Extracting 2-level hierarchical semantic chunks from docs_view/...")
    if not DOCS_VIEW_DIR.exists():
        raise FileNotFoundError(f"docs_view directory not found at {DOCS_VIEW_DIR}")

    catalog = load_intents()
    chunks = []
    parent_count = 0
    child_count = 0

    # 1. Process Overviews (Highest Conceptual Architecture Value)
    overviews_dir = DOCS_VIEW_DIR / "overviews"
    if overviews_dir.exists():
        for f in sorted(overviews_dir.glob("*.html")):
            if f.name == "relnotes-txt.html":
                # Exclude release notes completely from RAG
                continue

            rel_file = f"docs_view/overviews/{f.name}"
            try:
                with open(f, 'r', encoding='utf-8') as ofile:
                    content = ofile.read()
            except Exception as e:
                print(f"Error reading {f}: {e}")
                continue

            title_m = re.search(r'<h1[^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h1>', content, re.IGNORECASE)
            title = clean_html(title_m.group(1)) if title_m else f.stem.replace("-txt", "").capitalize()

            # Level 1: Parent Overview Chunk
            full_clean = clean_html(content)
            intents, synonyms = match_intents(f"{f.name} {title}", catalog)
            intent_suffix = ""
            if intents or synonyms:
                intent_suffix = f" [Intents: {', '.join(intents)}] [Keywords: {', '.join(synonyms)}]"

            parent_id = len(chunks)
            parent_chunk = {
                "id": parent_id,
                "level": "parent",
                "parentId": None,
                "docUrl": rel_file,
                "url": f"{rel_file}#MainTopic",
                "anchor": "MainTopic",
                "title": title,
                "pageHeading": title,
                "class": title,
                "category": "Overviews",
                "type": "overview",
                "breadcrumb": f"Overviews > {title}",
                "text": full_clean[:1500],
                "context_header": f"[UVM 1.2 Architecture Guide] [Overview: {title}]{intent_suffix}"
            }
            chunks.append(parent_chunk)
            parent_count += 1

            # Level 2: Child Sections in Overview
            topics = re.findall(r'<div class=["\']?CTopic["\']?[^>]*>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
            for idx, top in enumerate(topics):
                sub_title_m = re.search(r'<h[1-4][^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', top, re.IGNORECASE)
                sub_title = clean_html(sub_title_m.group(1)) if sub_title_m else f"Section {idx+1}"
                if sub_title == title:
                    continue

                anchor_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', top, re.IGNORECASE)
                anchor = anchor_m.group(1) if anchor_m else f"section_{idx}"

                clean_text = clean_html(top)
                if len(clean_text) < 70:
                    continue

                c_intents, c_synonyms = match_intents(f"{title} {sub_title}", catalog)
                c_intent_suffix = ""
                if c_intents or c_synonyms:
                    c_intent_suffix = f" [Intents: {', '.join(c_intents)}] [Keywords: {', '.join(c_synonyms)}]"

                child_chunk = {
                    "id": len(chunks),
                    "level": "child",
                    "parentId": parent_id,
                    "docUrl": rel_file,
                    "url": f"{rel_file}#{anchor}",
                    "anchor": anchor,
                    "title": f"{title} > {sub_title}",
                    "rawTitle": sub_title,
                    "class": title,
                    "category": "Overviews",
                    "type": "overview",
                    "breadcrumb": f"Overviews > {title} > {sub_title}",
                    "text": clean_text[:1200],
                    "context_header": f"[UVM 1.2 Architecture Guide] [Overview: {title}] [Section: {sub_title}]{c_intent_suffix}"
                }
                chunks.append(child_chunk)
                child_count += 1

    # 2. Process Classes, Methods, Macros in other directories
    for root, dirs, files in os.walk(DOCS_VIEW_DIR):
        root_path = Path(root)
        if root_path.name in ["overviews", "images"]:
            continue

        category = root_path.name.capitalize()
        for f in sorted(files):
            if not f.endswith(".html"):
                continue

            full_file = root_path / f
            rel_file = full_file.relative_to(BASE_DIR).as_posix()
            file_base = f.replace("-svh.html", "").replace(".html", "")

            try:
                with open(full_file, 'r', encoding='utf-8') as cfile:
                    content = cfile.read()
            except Exception as e:
                print(f"Error reading {full_file}: {e}")
                continue

            # Identify canonical class name
            class_anchor_m = re.search(r'<div class=["\']?CClass["\']?[^>]*data-anchor=["\']?([^"\'>]+)["\']?', content, re.IGNORECASE)
            main_title_m = re.search(r'id=["\']?MainTopic["\']?[\s\S]*?<h[1-4] class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', content, re.IGNORECASE)

            if class_anchor_m:
                canonical_class = class_anchor_m.group(1)
            elif file_base.startswith("uvm_"):
                canonical_class = file_base
            elif main_title_m:
                canonical_class = clean_html(main_title_m.group(1))
            else:
                canonical_class = file_base

            page_heading = clean_html(main_title_m.group(1)) if main_title_m else canonical_class

            # Extract substantive introductory / class description
            intro_m = re.search(r'<div class=["\']?CGeneric["\']?[^>]*data-anchor=["\']?Intro["\']?[\s\S]*?<div class=CBody>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
            class_m = re.search(r'<div class=["\']?CClass["\']?[\s\S]*?<div class=CBody>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)

            parent_body = ""
            if intro_m:
                parent_body += clean_html(intro_m.group(1)) + " "
            if class_m:
                parent_body += clean_html(class_m.group(1))
            if not parent_body.strip():
                main_body_m = re.search(r'<div class=["\']?CTopic["\']? id=["\']?MainTopic["\']?>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
                if main_body_m:
                    parent_body = clean_html(main_body_m.group(1))

            intents, synonyms = match_intents(f"{f} {canonical_class} {page_heading}", catalog)
            intent_suffix = ""
            if intents or synonyms:
                intent_suffix = f" [Intents: {', '.join(intents)}] [Keywords: {', '.join(synonyms)}]"

            # Level 1: Parent Class Chunk
            parent_id = len(chunks)
            parent_chunk = {
                "id": parent_id,
                "level": "parent",
                "parentId": None,
                "docUrl": rel_file,
                "url": f"{rel_file}#MainTopic",
                "anchor": "MainTopic",
                "title": canonical_class,
                "pageHeading": page_heading,
                "class": canonical_class,
                "category": category,
                "type": "class",
                "breadcrumb": f"{category} > {canonical_class}",
                "text": parent_body[:1500] if parent_body else f"{canonical_class} ({page_heading}) class reference in {category}.",
                "context_header": f"[UVM 1.2 Class Reference] [Class: {canonical_class}] [Category: {category}] [Title: {page_heading}] Overview:{intent_suffix}"
            }
            chunks.append(parent_chunk)
            parent_count += 1

            # Level 2: Child Methods, Tasks, Functions, Macros
            topic_divs = re.finditer(r'<div class=["\']?(C[A-Za-z0-9_]+)["\']?[^>]*>\s*<div class=["\']?CTopic["\']?[^>]*>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
            for m in topic_divs:
                cls_type = m.group(1)
                topic_html = m.group(2)

                # Skip Summary, MainTopic, Intro, or duplicates
                if any(x in topic_html for x in ['id="MainTopic"', 'id=MainTopic', 'data-anchor="Intro"', 'data-anchor="Summary"']):
                    continue
                if cls_type in ["CGroup", "CSection", "CGeneric"] and any(w in topic_html for w in ["Methods", "Variables", "Types", "Constants", "Port / Export / Imp Types"]):
                    continue

                sub_m = re.search(r'<h[1-4]\b[^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', topic_html, re.IGNORECASE)
                if not sub_m:
                    continue
                sub_title = clean_html(sub_m.group(1))
                if not sub_title or sub_title == canonical_class or sub_title == page_heading or sub_title == "Intro":
                    continue

                anchor_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', sub_m.group(1), re.IGNORECASE)
                anchor = anchor_m.group(1) if anchor_m else sub_title

                topic_text = clean_html(topic_html)
                if len(topic_text) < 55:
                    continue

                inferred_type = "method"
                if "macro" in cls_type.lower() or sub_title.startswith("`"):
                    inferred_type = "macro"
                elif "task" in cls_type.lower():
                    inferred_type = "task"
                elif "function" in cls_type.lower():
                    inferred_type = "function"
                elif "variable" in cls_type.lower() or "type" in cls_type.lower():
                    inferred_type = "variable"
                elif "class" in cls_type.lower():
                    inferred_type = "class"

                c_intents, c_synonyms = match_intents(f"{canonical_class} {sub_title}", catalog)
                c_intent_suffix = ""
                if c_intents or c_synonyms:
                    c_intent_suffix = f" [Intents: {', '.join(c_intents)}] [Keywords: {', '.join(c_synonyms)}]"

                display_title = f"{canonical_class}::{sub_title}" if inferred_type in ["method", "function", "task"] else sub_title

                child_chunk = {
                    "id": len(chunks),
                    "level": "child",
                    "parentId": parent_id,
                    "docUrl": rel_file,
                    "url": f"{rel_file}#{anchor}",
                    "anchor": anchor,
                    "title": display_title,
                    "rawTitle": sub_title,
                    "class": canonical_class,
                    "category": category,
                    "type": inferred_type,
                    "breadcrumb": f"{category} > {canonical_class} > {sub_title}",
                    "text": topic_text[:1200],
                    "context_header": f"[UVM 1.2 {inferred_type.capitalize()}] [{display_title}] Class: {canonical_class}. Category: {category}.{c_intent_suffix}"
                }
                chunks.append(child_chunk)
                child_count += 1

    print(f"Hierarchical extraction complete: {len(chunks)} total chunks ({parent_count} parents, {child_count} children).")
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

    # Prepend contextual retrieval header for each chunk
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
    parser = argparse.ArgumentParser(description="Generate UVM 1.2 Hierarchical RAG Embeddings & Intelligent Chunks")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Fastembed model name")
    args = parser.parse_args()

    print("=" * 60)
    print("  UVM 1.2 Hierarchical 2-Level RAG Chunker & Embedding Generator")
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
