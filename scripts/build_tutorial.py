#!/usr/bin/env python3
"""
UVM 1.2 Progressive Tutorial Static Site Generator.
Reads curriculum definitions (tutorial_curriculum.py, tutorial_curriculum_part2.py),
graph specs (config/tutorial_capstone_graph.yaml), and progressive SystemVerilog/C
sources (tutorial_src/), and generates interactive HTML pages in tutorial_view/
plus standalone source views in src_view/tutorial/ using Jinja2, markdown-it-py,
and syntax_highlighter.py.
"""

import difflib
import html
import json
import re
import shutil
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import page_builder_common as pbc  # noqa: E402

TUTORIAL_SRC_DIR = BASE_DIR / "tutorial_src"
TUTORIAL_CONTENT_DIR = BASE_DIR / "tutorial_content" / "chapters"
MANIFEST_PATH = BASE_DIR / "tutorial_content" / "tutorial_manifest.yaml"
OUTPUT_TUTORIAL_VIEW = BASE_DIR / "tutorial_view"
OUTPUT_SRC_TUTORIAL_DIR = BASE_DIR / "src_view" / "tutorial"
OUTPUT_TUTORIAL_META_JS = BASE_DIR / "js" / "tutorial_meta.js"
GRAPH_YAML_PATH = BASE_DIR / "tutorial_content" / "tutorial_capstone_graph.yaml"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def parse_chapter_markdown(md_path: Path) -> Dict[str, Any]:
    """Parse a chapter Markdown file with YAML frontmatter into a chapter dict."""
    raw = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$", raw)
    if not m:
        raise ValueError(f"Missing YAML frontmatter in {md_path}")
    meta = yaml.safe_load(m.group(1)) or {}
    meta["markdown_body"] = m.group(2).strip()
    return meta


def load_tutorial_curriculum() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Load tutorial_manifest.yaml and resolve numbered chapters, parts, and auto-inheritance."""
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}
    parts_list = manifest.get("parts", [])
    parts_by_id = {p["id"]: (idx + 1, p["title"]) for idx, p in enumerate(parts_list)}

    chapters: List[Dict[str, Any]] = []
    prev_code_slug: Optional[str] = None

    for idx, slug in enumerate(manifest.get("chapters", [])):
        md_path = TUTORIAL_CONTENT_DIR / f"{slug}.md"
        if not md_path.is_file():
            raise FileNotFoundError(f"Chapter content file missing for slug '{slug}': {md_path}")
        raw_ch = parse_chapter_markdown(md_path)
        num = idx + 1
        part_id = raw_ch.get("part", "")
        part_num, part_title = parts_by_id.get(part_id, (1, part_id or "General"))

        raw_title = re.sub(r"^\s*\d+\.\s*", "", str(raw_ch.get("title", slug))).strip()
        raw_short = re.sub(r"^\s*\d+\.\s*", "", str(raw_ch.get("short_title", raw_title))).strip()

        ch = dict(raw_ch)
        ch["slug"] = slug
        ch["num"] = num
        ch["part_id"] = part_id
        ch["part"] = part_num
        ch["part_title"] = part_title
        ch["raw_title"] = raw_title
        ch["raw_short_title"] = raw_short
        ch["title"] = f"{num:02d}. {raw_title}"
        ch["short_title"] = f"{num:02d}. {raw_short}"
        ch["href"] = f"tutorial_view/{slug}.html"

        inh = ch.get("inherit_from")
        if inh == "auto":
            ch["inherit_from"] = prev_code_slug
        if ch.get("src_dir"):
            prev_code_slug = slug

        chapters.append(ch)

    return manifest, chapters


TUTORIAL_MANIFEST, ALL_CHAPTERS = load_tutorial_curriculum()
CHAPTER_BY_SLUG: Dict[str, Dict[str, Any]] = {ch["slug"]: ch for ch in ALL_CHAPTERS}

MD_PARSER = MarkdownIt("commonmark", {"breaks": False, "html": True}).enable(["table", "strikethrough"])
JINJA_ENV = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

CDN_HEAD_HTML = (
    '<link rel="stylesheet" '
    'href="https://cdn.jsdelivr.net/npm/diff2html@3.4.48/bundles/css/diff2html.min.css">'
)
CDN_SCRIPTS = [
    "https://cdn.jsdelivr.net/npm/cytoscape@3.30.4/dist/cytoscape.min.js",
    "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js",
    "https://cdn.jsdelivr.net/npm/diff2html@3.4.48/bundles/js/diff2html-ui.min.js",
    "https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js",
]


def load_graph_specs() -> Dict[str, Any]:
    with open(GRAPH_YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_chapter_files(chapter: Dict[str, Any]) -> OrderedDict:
    """
    Resolve complete source file map {rel_name: (content, origin_slug)} for a chapter
    by recursively inheriting files from `inherit_from` and overlaying current dir files.
    """
    merged: OrderedDict = OrderedDict()

    parent_slug = chapter.get("inherit_from")
    if parent_slug and parent_slug in CHAPTER_BY_SLUG:
        parent_files = resolve_chapter_files(CHAPTER_BY_SLUG[parent_slug])
        excluded = set(chapter.get("exclude_inherited", []))
        for fname, info in parent_files.items():
            # Skip old chapter-specific dut files when replaced
            if fname in excluded or fname.startswith("dut/") or fname.startswith("c_model/"):
                continue
            merged[fname] = info

    # Overlay chapter's own source files
    src_dir_name = chapter.get("src_dir")
    own_files: Dict[str, str] = {}
    if src_dir_name:
        src_path = TUTORIAL_SRC_DIR / src_dir_name
        if src_path.is_dir():
            for fp in sorted(src_path.iterdir()):
                if fp.is_file():
                    own_files[fp.name] = fp.read_text(encoding="utf-8", errors="replace")

    for fname, content in own_files.items():
        merged[fname] = {
            "content": content,
            "origin": chapter["slug"],
            "is_own": True,
        }

    # Add DUT and C reference model files declared for this chapter
    for rel_dut in chapter.get("dut_files", []):
        dut_path = TUTORIAL_SRC_DIR / rel_dut
        if dut_path.is_file():
            merged[rel_dut] = {
                "content": dut_path.read_text(encoding="utf-8", errors="replace"),
                "origin": "shared",
                "is_own": False,
            }

    # Ensure primary_file appears first in Code Studio tabs
    primary = chapter.get("primary_file")
    ordered: OrderedDict = OrderedDict()
    if primary and primary in merged:
        ordered[primary] = merged[primary]
    for fname, info in merged.items():
        if fname != primary:
            ordered[fname] = info

    return ordered


def compute_chapter_diff(
    chapter: Dict[str, Any],
    curr_files: OrderedDict,
    prev_files: Optional[OrderedDict],
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Compute unified diff vs previous practical chapter using difflib.
    Returns (unified_diff_text, human_summary, file_meta_map).
    """
    file_meta: Dict[str, Any] = {}
    if not prev_files:
        for fname in curr_files:
            file_meta[fname] = {"status": "new", "added_lines": []}
        return "", "", file_meta

    diff_chunks: List[str] = []
    new_count = 0
    mod_count = 0

    for fname, info in curr_files.items():
        curr_text = info["content"]
        curr_lines = curr_text.splitlines(keepends=True)

        if fname not in prev_files:
            new_count += 1
            file_meta[fname] = {"status": "new", "added_lines": list(range(1, len(curr_lines) + 1))}
            udiff = list(
                difflib.unified_diff(
                    [],
                    curr_lines,
                    fromfile=f"a/{fname}",
                    tofile=f"b/{fname}",
                    lineterm="\n",
                )
            )
            if udiff:
                diff_chunks.append("".join(udiff))
        else:
            prev_text = prev_files[fname]["content"]
            if prev_text == curr_text:
                file_meta[fname] = {"status": "same", "added_lines": []}
                continue

            mod_count += 1
            prev_lines = prev_text.splitlines(keepends=True)
            udiff = list(
                difflib.unified_diff(
                    prev_lines,
                    curr_lines,
                    fromfile=f"a/{fname}",
                    tofile=f"b/{fname}",
                    lineterm="\n",
                )
            )
            if udiff:
                diff_chunks.append("".join(udiff))

            # Track exact 1-based line numbers added/changed in current file
            added_lines: List[int] = []
            sm = difflib.SequenceMatcher(None, prev_text.splitlines(), curr_text.splitlines())
            for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
                if tag in ("insert", "replace"):
                    added_lines.extend(range(j1 + 1, j2 + 1))
            file_meta[fname] = {"status": "mod", "added_lines": added_lines}

    summary_parts = []
    if new_count:
        summary_parts.append(f"{new_count} new file{'s' if new_count > 1 else ''}")
    if mod_count:
        summary_parts.append(f"{mod_count} updated file{'s' if mod_count > 1 else ''}")
    summary = ", ".join(summary_parts) if summary_parts else "No code diffs"

    return "\n".join(diff_chunks), summary, file_meta


def render_markdown_prose(md_text: str) -> str:
    """
    Render Markdown prose via markdown-it-py, upgrading fenced Mermaid diagrams to
    <pre class="mermaid"> and fenced SystemVerilog/C code blocks to syntax-highlighted
    portal .code-block-container cards.
    """
    raw_html = MD_PARSER.render(md_text.strip())

    def _replace_code_block(m: re.Match) -> str:
        lang = (m.group(1) or "").lower()
        code_raw = html.unescape(m.group(2)).rstrip("\n")
        if lang == "mermaid":
            return f'<div class="tut-mermaid-wrap"><pre class="mermaid">{html.escape(code_raw)}</pre></div>'
        lang_label = "C / DPI" if lang in ("c", "cpp") else ("SystemVerilog" if lang in ("sv", "systemverilog") else None)
        return pbc.render_code_block(code_raw, lang=lang_label)

    return re.sub(
        r'<pre><code(?:\s+class="language-([^"]+)")?>([\s\S]*?)</code></pre>',
        _replace_code_block,
        raw_html,
    )


def resolve_slug_layer(entry: Dict[str, Any]) -> Optional[int]:
    """Resolve a node/edge/layer entry's layerSlug (or numeric layer) to active chapter num."""
    l_slug = entry.get("layerSlug")
    if l_slug:
        ch = CHAPTER_BY_SLUG.get(l_slug)
        return ch["num"] if ch else None
    return entry.get("layer")


def build_chapter_graph_payload(chapter: Dict[str, Any], specs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build Cytoscape.js graph payload tailored to the chapter's interactive widget."""
    widget = chapter.get("interactive_widget")
    if widget == "vcycle":
        return {
            "mode": "vcycle",
            "nodes": specs.get("vcycle_nodes", []),
            "edges": specs.get("vcycle_edges", []),
        }

    if widget in ("arch_diff", "capstone"):
        max_layer = chapter["num"] if widget == "arch_diff" else (ALL_CHAPTERS[-1]["num"] if ALL_CHAPTERS else 13)
        all_nodes = specs.get("capstone_nodes", [])
        all_edges = specs.get("capstone_edges", [])

        visible_nodes = []
        for n in all_nodes:
            n_layer = resolve_slug_layer(n)
            if n_layer is None or n_layer > max_layer:
                continue
            copy_n = dict(n)
            copy_n["layer"] = n_layer
            ch_slug = copy_n.get("chapterSlug")
            if ch_slug and ch_slug in CHAPTER_BY_SLUG:
                ref_ch = CHAPTER_BY_SLUG[ch_slug]
                copy_n["chapterNum"] = ref_ch["num"]
                copy_n["chapterUrl"] = ref_ch["href"]
            else:
                copy_n.pop("chapterUrl", None)
            visible_nodes.append(copy_n)

        visible_ids = {n["id"] for n in visible_nodes}
        shaped_nodes = []
        for copy_n in visible_nodes:
            if copy_n.get("parent") and copy_n["parent"] not in visible_ids:
                copy_n.pop("parent", None)
            if widget == "arch_diff":
                copy_n["isNew"] = (
                    copy_n.get("layer") == chapter["num"]
                    or copy_n["id"] in set(chapter.get("new_components", []))
                )
            shaped_nodes.append(copy_n)

        shaped_edges = []
        for e in all_edges:
            e_layer = resolve_slug_layer(e)
            if e_layer is None or e_layer > max_layer:
                continue
            if e.get("source") in visible_ids and e.get("target") in visible_ids:
                copy_e = dict(e)
                copy_e["layer"] = e_layer
                shaped_edges.append(copy_e)

        # Structural fallback edges when intermediate orchestrators (v_seqr / ref_model) are absent
        if "v_seqr" not in visible_ids and "uvm_test" in visible_ids and "data_seqr" in visible_ids:
            shaped_edges.append({"source": "uvm_test", "target": "data_seqr", "label": "seq.start()", "layer": chapter["num"]})
        if "ref_model" not in visible_ids and "data_mon" in visible_ids and "scoreboard" in visible_ids:
            shaped_edges.append({"source": "data_mon", "target": "scoreboard", "label": "req_ap / rsp_ap", "layer": chapter["num"]})

        payload: Dict[str, Any] = {
            "mode": widget,
            "chapterNum": chapter["num"],
            "nodes": shaped_nodes,
            "edges": shaped_edges,
        }
        if widget == "capstone":
            resolved_layers = []
            for l_entry in specs.get("capstone_layers", []):
                l_slug = l_entry.get("layerSlug")
                if l_slug and l_slug in CHAPTER_BY_SLUG:
                    l_ch = CHAPTER_BY_SLUG[l_slug]
                    resolved_layers.append({
                        "layer": l_ch["num"],
                        "slug": l_slug,
                        "label": f"Ch.{l_ch['num']:02d}: {l_entry.get('label', l_ch['raw_short_title'])}",
                    })
                elif isinstance(l_entry.get("layer"), int):
                    resolved_layers.append(l_entry)
            resolved_layers.sort(key=lambda x: x["layer"])
            payload["layers"] = resolved_layers
        return payload

    return None


def calibrate_stepper_steps(
    chapter: Dict[str, Any], files_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Clamp stepper line targets cleanly against actual generated file lengths."""
    line_counts = {fd["name"]: fd["lines"] for fd in files_data}
    calibrated: List[Dict[str, Any]] = []
    for st in chapter.get("stepper", []):
        copy_st = dict(st)
        fname = copy_st.get("file", "")
        if fname in line_counts:
            copy_st["line"] = max(1, min(int(copy_st.get("line", 1)), line_counts[fname]))
        calibrated.append(copy_st)
    return calibrated


def build_chapter_page(
    idx: int,
    chapter: Dict[str, Any],
    specs: Dict[str, Any],
    prev_resolved_files: Optional[OrderedDict],
) -> Tuple[Dict[str, Any], Optional[OrderedDict]]:
    """Render one tutorial chapter HTML page and its source_view pages."""
    slug = chapter["slug"]
    out_file = OUTPUT_TUTORIAL_VIEW / f"{slug}.html"
    href = f"tutorial_view/{slug}.html"

    # Resolve progressive source files
    curr_files = resolve_chapter_files(chapter) if chapter.get("src_dir") else OrderedDict()
    files_data: List[Dict[str, Any]] = []
    diff_text = ""
    diff_summary = ""
    diff_meta: Dict[str, Any] = {}

    if curr_files:
        diff_text, diff_summary, diff_meta = compute_chapter_diff(chapter, curr_files, prev_resolved_files)
        shared_class_base_map = pbc.sh.build_suite_class_base_map(
            [(fn, inf["content"]) for fn, inf in curr_files.items()]
        )
        for fname, info in curr_files.items():
            content = info["content"]
            rows, line_count = pbc.highlight_code_lines(
                content, fname, clickable_sym_links=True, shared_class_base_map=shared_class_base_map
            )
            files_data.append({
                "name": fname,
                "raw_content": content,
                "table_html": "\n".join(rows),
                "lines": line_count,
                "size_kb": round(len(content.encode("utf-8")) / 1024, 1),
            })

        # Generate standalone src_view/tutorial/<slug>/<fname>.html for Split View
        src_base = OUTPUT_SRC_TUTORIAL_DIR / slug
        for fd in files_data:
            fname = fd["name"]
            src_rel_path = f"tutorial/{slug}/{fname}"
            out_src_file = src_base / f"{fname}.html"
            out_src_file.parent.mkdir(parents=True, exist_ok=True)
            src_depth = len(src_rel_path.split("/"))
            src_root_rel = "../" * src_depth
            if fname.startswith("dut/") or fname.startswith("c_model/"):
                raw_href = f"{src_root_rel}tutorial_src/{fname}"
            else:
                raw_href = f"{src_root_rel}tutorial_src/{chapter['src_dir']}/{fname}"
            src_html = pbc.render_source_viewer(
                rel_path=src_rel_path,
                code=fd["raw_content"],
                rows=[fd["table_html"]],
                syms=[],
                doc_rel=None,
                root_rel=src_root_rel,
                raw_href=raw_href,
            )
            out_src_file.write_text(src_html, encoding="utf-8", newline="\n")

    # Calibrate stepper + render Studio / Console / Stepper
    stepper_list = calibrate_stepper_steps(chapter, files_data) if files_data else []
    studio_html = ""
    sim_html = ""
    stepper_html = ""

    if files_data:
        primary_file = chapter.get("primary_file", files_data[0]["name"])
        studio_html = pbc.render_code_studio(files_data, primary_file, "../", stepper_steps=stepper_list or None)
    if chapter.get("sim_log"):
        sim_html = pbc.render_simulation_console(chapter["sim_log"])
    if stepper_list:
        stepper_html = pbc.render_flow_stepper(stepper_list, "")

    prose_html = render_markdown_prose(chapter["markdown_body"])

    prev_ch = ALL_CHAPTERS[idx - 1] if idx > 0 else None
    next_ch = ALL_CHAPTERS[idx + 1] if idx + 1 < len(ALL_CHAPTERS) else None
    prev_ctx = {"num": prev_ch["num"], "short_title": prev_ch["short_title"], "href": f"tutorial_view/{prev_ch['slug']}.html"} if prev_ch else None
    next_ctx = {"num": next_ch["num"], "short_title": next_ch["short_title"], "href": f"tutorial_view/{next_ch['slug']}.html"} if next_ch else None

    graph_payload = build_chapter_graph_payload(chapter, specs)
    capstone_meta = None
    if graph_payload and graph_payload.get("layers"):
        l_nums = [x["layer"] for x in graph_payload["layers"]]
        capstone_meta = {
            "min_num": min(l_nums),
            "max_num": max(l_nums),
            "min_short": f"Ch.{min(l_nums):02d}",
            "max_short": f"Ch.{max(l_nums):02d}",
            "max_label": graph_payload["layers"][-1]["label"],
        }

    template = JINJA_ENV.get_template("tutorial_chapter.html.j2")
    body_content = template.render(
        chapter=chapter,
        total_chapters=len(ALL_CHAPTERS),
        root_rel="../",
        prose_html=prose_html,
        diff_text=diff_text,
        diff_summary=diff_summary,
        studio_html=studio_html,
        sim_html=sim_html,
        stepper_html=stepper_html,
        prev_chapter=prev_ctx,
        next_chapter=next_ctx,
        capstone_meta=capstone_meta,
    )

    breadcrumbs_html = pbc.render_breadcrumbs(
        [
            {"title": "Tutorial", "href": "../index.html#/tutorial", "is_home": True},
            {"title": chapter["part_title"]},
            {"title": chapter["short_title"]},
        ],
        "../",
    )

    diff_badge = f'<span class="badge badge-diff badge-diff-{chapter["difficulty"].lower()}">{html.escape(chapter["difficulty"])}</span>'
    files_badge = f'<span class="badge badge-files">{len(files_data)} files</span>' if files_data else '<span class="badge badge-files">Concept Guide</span>'
    info_html = (
        f'<svg class="banner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
        f'<path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>'
        f'<span class="file-label">Course:</span>'
        f'<code class="banner-file-code">Chapter {chapter["num"]:02d}/{len(ALL_CHAPTERS)}</code>'
        f'{diff_badge} {files_badge}'
    )

    actions_html = ""
    if files_data:
        actions_html = (
            '<button type="button" class="btn btn-primary" id="btn-download-zip" title="Download chapter SystemVerilog project (.zip)">'
            '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'
            '<span>Download (.zip)</span></button>'
        )
    banner_html = pbc.render_banner(info_html, actions_html, extra_classes="example-source-banner tutorial-banner")

    data_payloads: Dict[str, str] = {}
    if files_data:
        zip_payload = [{"name": fd["name"], "content": fd["raw_content"]} for fd in files_data]
        data_payloads["zip-payload"] = html.escape(json.dumps(zip_payload))
        data_payloads["tut-diff-meta-payload"] = html.escape(json.dumps(diff_meta))
    if stepper_list:
        data_payloads["stepper-payload"] = html.escape(json.dumps(stepper_list))
    if diff_text:
        data_payloads["tut-diff-payload"] = html.escape(json.dumps({"diff": diff_text}))
    if chapter.get("quizzes"):
        data_payloads["tut-quiz-payload"] = html.escape(json.dumps(chapter["quizzes"]))
    if graph_payload:
        data_payloads["tut-graph-payload"] = html.escape(json.dumps(graph_payload))

    extra_scripts = list(CDN_SCRIPTS) + ["../js/example_page.js", "../js/tutorial_page.js"]

    page_html = pbc.render_html_shell(
        title=f"{chapter['title']} | UVM 1.2 Step-by-Step Tutorial",
        body_content=body_content,
        root_rel="../",
        breadcrumbs_html=breadcrumbs_html,
        banner_html=banner_html,
        extra_html_classes="example-page tutorial-page",
        extra_body_classes="example-body tutorial-body",
        extra_head_html=CDN_HEAD_HTML,
        extra_scripts=extra_scripts,
        data_payloads=data_payloads,
        include_toc=True,
    )
    out_file.write_text(page_html, encoding="utf-8", newline="\n")

    primary_src = ""
    if files_data:
        pfile = chapter.get("primary_file", files_data[0]["name"])
        primary_src = f"src_view/tutorial/{slug}/{pfile}.html#L1"

    meta_out = {
        "num": chapter["num"],
        "slug": slug,
        "title": chapter["title"],
        "short_title": chapter["short_title"],
        "part": chapter["part"],
        "part_title": chapter["part_title"],
        "difficulty": chapter["difficulty"],
        "summary": chapter["summary"],
        "apis": chapter.get("apis", []),
        "href": href,
        "files_count": len(files_data),
        "primary_src": primary_src,
    }
    return meta_out, (curr_files if curr_files else prev_resolved_files)


def generate_all_tutorial() -> Dict[str, Any]:
    """Generate all tutorial chapters from manifest and return catalog metadata for search_data.js."""
    global TUTORIAL_MANIFEST, ALL_CHAPTERS, CHAPTER_BY_SLUG
    TUTORIAL_MANIFEST, ALL_CHAPTERS = load_tutorial_curriculum()
    CHAPTER_BY_SLUG = {ch["slug"]: ch for ch in ALL_CHAPTERS}

    print("=" * 60)
    print("  Generating UVM 1.2 Interactive Step-by-Step Tutorial")
    print("=" * 60)

    OUTPUT_TUTORIAL_VIEW.mkdir(parents=True, exist_ok=True)
    # Remove stale chapter HTML and src_view folders from deleted/renamed slugs
    active_slugs = set(CHAPTER_BY_SLUG.keys())
    for old_html in OUTPUT_TUTORIAL_VIEW.glob("*.html"):
        if old_html.stem not in active_slugs:
            old_html.unlink()
    if OUTPUT_SRC_TUTORIAL_DIR.is_dir():
        for old_dir in OUTPUT_SRC_TUTORIAL_DIR.iterdir():
            if old_dir.is_dir() and old_dir.name not in active_slugs:
                shutil.rmtree(old_dir)

    specs = load_graph_specs()

    chapters_built: List[Dict[str, Any]] = []
    prev_files: Optional[OrderedDict] = None

    for idx, chapter in enumerate(ALL_CHAPTERS):
        meta_out, prev_files = build_chapter_page(idx, chapter, specs, prev_files)
        chapters_built.append(meta_out)
        print(f"Generated tutorial chapter {meta_out['num']:02d}: {meta_out['href']} ({meta_out['files_count']} files)")

    # Build tutorialTree grouped by part_title
    parts_order: OrderedDict = OrderedDict()
    for ch in chapters_built:
        ptitle = ch["part_title"]
        if ptitle not in parts_order:
            parts_order[ptitle] = {
                "type": "group",
                "title": ptitle,
                "part": ch["part"],
                "children": [],
            }
        parts_order[ptitle]["children"].append({
            "type": "tutorial",
            "num": ch["num"],
            "slug": ch["slug"],
            "title": ch["short_title"],
            "full_title": ch["title"],
            "href": ch["href"],
            "difficulty": ch["difficulty"],
            "part": ch["part"],
            "files_count": ch["files_count"],
            "summary": ch["summary"],
        })

    tutorial_tree = list(parts_order.values())

    tutorial_search_items = []
    tutorial_to_src: Dict[str, str] = {}
    for ch in chapters_built:
        rel_clean = f"{ch['slug']}.html"
        if ch["primary_src"]:
            tutorial_to_src[rel_clean] = ch["primary_src"]
        tutorial_search_items.append({
            "name": ch["title"],
            "type": "tutorial",
            "category": f"Tutorial / {ch['part_title']}",
            "difficulty": ch["difficulty"],
            "src": ch["primary_src"] or None,
            "doc": ch["href"],
            "desc": f"UVM Tutorial Ch.{ch['num']:02d}: {ch['summary']} ({ch['difficulty']}, {ch['files_count']} files)",
        })

    # Emit lightweight js/tutorial_meta.js for home.html
    featured_cards = []
    for ch in ALL_CHAPTERS:
        hf = ch.get("home_featured")
        if isinstance(hf, dict):
            featured_cards.append({
                "slug": ch["slug"],
                "num": ch["num"],
                "href": ch["href"],
                "title": f"{ch['num']:02d}. {hf.get('title', ch['raw_short_title'])}",
                "badge": hf.get("badge", ch["difficulty"]),
                "badge_class": hf.get("badge_class", f"home-badge-{ch['difficulty'].lower()}"),
                "desc": hf.get("desc", ch["summary"]),
            })
    tutorial_meta_js = {
        "totalChapters": len(chapters_built),
        "defaultUrl": chapters_built[0]["href"] if chapters_built else "",
        "chapters": [
            {
                "num": c["num"],
                "slug": c["slug"],
                "href": c["href"],
                "short_title": c["short_title"],
                "difficulty": c["difficulty"],
            }
            for c in chapters_built
        ],
        "featured": featured_cards,
    }
    OUTPUT_TUTORIAL_META_JS.write_text(
        "// Auto-generated by scripts/build_tutorial.py — do not edit manually.\n"
        f"const TUTORIAL_META = {json.dumps(tutorial_meta_js, indent=2)};\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"\nSuccessfully generated {len(chapters_built)} tutorial chapters in {OUTPUT_TUTORIAL_VIEW}.")
    return {
        "chapters": chapters_built,
        "tutorialTree": tutorial_tree,
        "searchItems": tutorial_search_items,
        "tutorialToSrc": tutorial_to_src,
    }


if __name__ == "__main__":
    generate_all_tutorial()
