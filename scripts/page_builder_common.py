#!/usr/bin/env python3
"""
UVM 1.2 Common Page Builder Toolkit
Universal, reusable component library and HTML page shell generator.
Shared by scripts/build_docs.py, scripts/build_examples.py, and any future page generators.
"""

import os
import re
import html
import json
import posixpath
from pathlib import Path
from collections import OrderedDict
from typing import List, Dict, Any, Tuple, Optional, Union

# Import core syntax highlighter
BASE_DIR = Path(__file__).resolve().parent.parent
import syntax_highlighter as sh


def get_rel_root(depth_or_path: Union[int, Path, str]) -> str:
    """
    Compute relative path back to repository root (e.g. './', '../', '../../').
    Accepts an integer depth, a relative file path as str or Path.
    """
    if isinstance(depth_or_path, int):
        depth = depth_or_path
    else:
        p = str(depth_or_path).replace('\\', '/').strip('/')
        depth = len(p.split('/')) - 1 if '/' in p else 0

    return "../" * depth if depth > 0 else "./"


def highlight_code_lines(code: str, filename: str, clickable_sym_links: bool = False) -> Tuple[List[str], int]:
    """
    Renders syntax-highlighted HTML table rows with line numbers.
    Delegates to syntax_highlighter.py.
    Returns: (list_of_html_rows, line_count)
    """
    return sh.highlight_source_code_table_rows(code, filename, clickable_sym_links=clickable_sym_links)


def render_breadcrumbs(items: List[Dict[str, Any]], root_rel: str) -> str:
    """
    Renders a unified <nav class="doc-breadcrumbs"> breadcrumb component.
    items: list of dicts with keys:
      - 'title': label text
      - 'href': optional navigation href (hash or URL)
      - 'data_href': optional data-doc-href or data-example-url attribute
      - 'is_home': optional boolean indicating the root home item
    """
    if not items:
        return ""

    parts = []
    total = len(items)

    for i, it in enumerate(items):
        title = html.escape(it.get('title', ''))
        href = it.get('href')
        data_href = it.get('data_href')
        is_home = it.get('is_home', False)
        is_last = (i == total - 1)

        if is_last:
            parts.append(f'<span class="doc-breadcrumb-item active">{title}</span>')
        elif href:
            home_cls = " doc-breadcrumb-home" if is_home else ""
            data_attr = f' data-doc-href="{html.escape(data_href)}"' if data_href else ""
            parts.append(f'<a href="{href}" class="doc-breadcrumb-item doc-breadcrumb-link{home_cls}"{data_attr}>{title}</a>')
        else:
            parts.append(f'<span class="doc-breadcrumb-item">{title}</span>')

    sep_html = '\n  <span class="doc-breadcrumb-sep">/</span>\n  '
    return f'''<nav class="doc-breadcrumbs" aria-label="Breadcrumb navigation">
  {sep_html.join(parts)}
</nav>'''


def render_banner(info_html: str, actions_html: str = "", extra_classes: str = "") -> str:
    """
    Renders a standard .doc-source-banner with info section and actions buttons.
    """
    cls_str = f"doc-source-banner {extra_classes}".strip()
    actions_block = f'<div class="banner-actions">\n    {actions_html}\n  </div>' if actions_html else ''

    return f'''<div class="{cls_str}">
  <div class="banner-info">
    {info_html}
  </div>
  {actions_block}
</div>'''


def render_toc_sidebar() -> str:
    """
    Renders the sticky In-Page Table of Contents ("On this page") sidebar.
    """
    return '''<aside class="doc-toc-sidebar" id="doc-toc-sidebar" aria-label="On this page">
  <div class="doc-toc-inner">
    <div class="doc-toc-header">
      <span class="doc-toc-title">On this page</span>
      <button class="doc-toc-toggle-all-btn" id="doc-toc-toggle-all" type="button" title="Collapse or expand all sections">
        <svg class="toc-toggle-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="4 14 12 6 20 14"/>
        </svg>
        <span class="toc-toggle-text">Collapse all</span>
      </button>
    </div>
    <nav class="doc-toc-nav" id="doc-toc-nav"></nav>
  </div>
</aside>'''


def render_code_pane(table_html: str, pane_id: str = "file-pane-0", is_active: bool = True, filename: str = "") -> str:
    """
    Renders a single file code pane containing the syntax-highlighted code table.
    """
    active_cls = " active" if is_active else ""
    data_attr = f' data-filename="{html.escape(filename)}"' if filename else ""
    return f'<div class="file-code-pane{active_cls}" id="{pane_id}"{data_attr}><table class="sv-code-table"><tbody>{table_html}</tbody></table></div>'


def render_code_container(panes_html: str, container_id: str = "studio-code-container", extra_classes: str = "") -> str:
    """
    Renders the unified code container wrapping code panes.
    Carries both .code-container and contextual classes (.studio-code-container, .src-code-container)
    for 100% backward compatibility.
    """
    classes = f"code-container {extra_classes}".strip()
    return f'<div class="{classes}" id="{container_id}">{panes_html}</div>'


def render_code_studio(files_data: List[Dict[str, Any]], primary_file: str, root_rel: str) -> str:
    """
    Renders the complete Multi-File Code Studio component:
    - Quick file select dropdown with folder hierarchy
    - Action toolbar (Copy code, download raw, shareable link)
    - Scrollable tab bar with chevron scroll buttons
    - Multi-file code panes
    """
    # 1. Quick file selector options
    has_dirs = any('/' in fd['name'] or '\\' in fd['name'] for fd in files_data)
    if not has_dirs:
        select_options = ''.join([
            f'<option value="{i}">📄 {html.escape(fd["name"])}</option>'
            for i, fd in enumerate(files_data)
        ])
    else:
        groups = OrderedDict()
        for i, fd in enumerate(files_data):
            raw_name = fd['name'].replace('\\', '/')
            if '/' in raw_name:
                folder, fname = raw_name.rsplit('/', 1)
                folder_key = folder + '/'
            else:
                folder_key = 'root/'
                fname = raw_name
            if folder_key not in groups:
                groups[folder_key] = []
            groups[folder_key].append((i, fname))

        select_options_list = []
        for folder_label, items in groups.items():
            select_options_list.append(f'<optgroup label="📁 {html.escape(folder_label)}">')
            total = len(items)
            for idx, (file_idx, fname) in enumerate(items):
                branch = '└── ' if idx == total - 1 else '├── '
                select_options_list.append(f'<option value="{file_idx}">{branch}{html.escape(fname)}</option>')
            select_options_list.append('</optgroup>')
        select_options = ''.join(select_options_list)

    # 2. Tabs
    tabs_html = ''.join([
        f'<button type="button" class="studio-tab {("active" if i == 0 else "")}" data-file-idx="{i}" title="{html.escape(fd["name"])}"><span class="tab-icon">📄</span><span class="tab-name">{html.escape(fd["name"])}</span></button>'
        for i, fd in enumerate(files_data)
    ])

    # 3. Panes
    panes_html = ''.join([
        render_code_pane(fd["table_html"], pane_id=f"file-pane-{i}", is_active=(i == 0), filename=fd["name"])
        for i, fd in enumerate(files_data)
    ])
    code_container_html = render_code_container(panes_html, container_id="studio-code-container", extra_classes="studio-code-container")

    return f'''<div class="CGroup" id="doc-nav-studio" data-doc-topic="doc-nav-studio" data-anchor="Studio">
  <div class="CTopic">
    <h2 class="CTitle"><a name="Studio">Multi-File Code Studio</a></h2>
    <div class="CBody">
      <div class="studio-section">
        <div class="studio-header">
          <div class="studio-toolbar">
            <div class="studio-toolbar-left">
              <div class="studio-file-select-wrapper" title="Jump directly to any file in this studio">
                <select class="studio-file-select" id="studio-file-select" aria-label="Select file">
                  {select_options}
                </select>
              </div>
            </div>

            <div class="studio-toolbar-actions">
              <button type="button" class="btn btn-sm btn-outline studio-action-btn" id="btn-copy-code" title="Copy active file code" aria-label="Copy code">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
              <button type="button" class="btn btn-sm btn-outline studio-action-btn" id="btn-download-raw" title="Download active file" aria-label="Download file">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              </button>
              <button type="button" class="btn btn-sm btn-outline studio-action-btn" id="btn-copy-example-link" title="Copy shareable link" aria-label="Copy link">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
              </button>
            </div>
          </div>

          <div class="studio-tab-bar-wrapper">
            <button type="button" class="studio-tab-scroll-btn scroll-left" id="studio-tab-scroll-left" title="Scroll tabs left" aria-label="Scroll tabs left">&#10094;</button>
            <div class="studio-tab-bar" id="studio-tab-bar">
              {tabs_html}
            </div>
            <button type="button" class="studio-tab-scroll-btn scroll-right" id="studio-tab-scroll-right" title="Scroll tabs right" aria-label="Scroll tabs right">&#10095;</button>
          </div>
        </div>

        {code_container_html}
      </div>
    </div>
  </div>
</div>'''


def render_simulation_console(sim_log: str, custom_commands: Optional[Dict[str, str]] = None) -> str:
    """
    Renders the Simulation Output Console & Terminal Log with simulator tabs and severity filters.
    """
    default_cmd = "make -f Makefile.questa run"
    return f'''<div class="CGroup" id="doc-nav-sim" data-doc-topic="doc-nav-sim" data-anchor="Simulation">
  <div class="CTopic">
    <h2 class="CTitle"><a name="Simulation">Simulation &amp; Execution Output</a></h2>
    <div class="CBody">
      <div class="sim-section">
        <!-- Simulator Command Selector -->
        <div class="sim-cmd-card">
          <div class="sim-tabs">
            <button type="button" class="sim-tab active" data-sim="questa">Questa / ModelSim</button>
            <button type="button" class="sim-tab" data-sim="vcs">Synopsys VCS</button>
            <button type="button" class="sim-tab" data-sim="xcelium">Cadence Xcelium</button>
          </div>
          <div class="sim-cmd-box">
            <code id="sim-cmd-text">{default_cmd}</code>
            <button type="button" class="btn btn-sm btn-outline" id="btn-copy-cmd" title="Copy command">Copy</button>
          </div>
        </div>

        <!-- Terminal Log -->
        <div class="terminal-card">
          <div class="terminal-header">
            <div class="terminal-dots">
              <span class="dot red"></span>
              <span class="dot yellow"></span>
              <span class="dot green"></span>
            </div>
            <span class="terminal-title">Simulation Output Console (UVM 1.2 Execution Log)</span>
            <div class="terminal-filters">
              <button type="button" class="term-filter active" data-level="all">All</button>
              <button type="button" class="term-filter" data-level="info">Info</button>
              <button type="button" class="term-filter" data-level="warning">Warning</button>
              <button type="button" class="term-filter" data-level="error">Error</button>
            </div>
          </div>
          <pre class="terminal-body" id="terminal-body">{html.escape(sim_log)}</pre>
        </div>
      </div>
    </div>
  </div>
</div>'''


def render_flow_stepper(stepper_steps: List[Dict[str, Any]]) -> str:
    """
    Renders the Interactive Visual Flow Stepper Section.
    """
    if not stepper_steps:
        return ""

    stepper_nodes_html = ''.join([
        f'<div class="step-node {("active" if i == 0 else "")}" data-step="{i+1}">'
        f'<span class="step-num">{i+1}</span>'
        f'<span class="step-title">{html.escape(s["title"].split(". ")[1] if ". " in s["title"] else s["title"])}</span>'
        f'</div>'
        for i, s in enumerate(stepper_steps)
    ])

    first = stepper_steps[0]
    return f'''<!-- Interactive Visual Flow Stepper Section -->
<div class="CGroup" id="doc-nav-stepper" data-doc-topic="doc-nav-stepper" data-anchor="FlowStepper">
  <div class="CTopic">
    <h2 class="CTitle"><a name="FlowStepper">Simulation Flow Stepper</a></h2>
    <div class="CBody">
      <div class="stepper-section" id="visual-flow-stepper">
        <div class="section-header-row">
          <div class="section-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            <span class="section-title-text">Interactive Execution Progression</span>
          </div>
          <div class="stepper-controls">
            <button type="button" class="btn btn-sm btn-outline" id="stepper-prev" disabled>&larr; Previous</button>
            <button type="button" class="btn btn-sm btn-outline" id="stepper-play">Play &#9654;</button>
            <button type="button" class="btn btn-sm btn-primary" id="stepper-next">Next Step &rarr;</button>
          </div>
        </div>

        <div class="stepper-timeline" id="stepper-timeline">
          {stepper_nodes_html}
        </div>

        <div class="step-card" id="step-detail-card">
          <div class="step-card-header">
            <h4 id="step-active-title">{html.escape(first.get("title", ""))}</h4>
            <span class="step-active-comp" id="step-active-comp">Target: {html.escape(first.get("component", ""))}</span>
          </div>
          <p id="step-active-desc">{html.escape(first.get("desc", ""))}</p>
          <div class="step-log-hint">
            <strong>Expected Log Output:</strong>
            <code id="step-active-log">{html.escape(first.get("log_snippet", ""))}</code>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>'''


def render_topology_grid(topology_nodes: List[Dict[str, Any]]) -> str:
    """
    Renders the Testbench Architecture Topology grid.
    """
    if not topology_nodes:
        return ""

    cards_html = []
    for node in topology_nodes:
        name = node.get("name", "")
        ntype = node.get("type", "")
        det = node.get("details", "")
        details_block = f'<div class="topo-details">{html.escape(det)}</div>' if det else ''
        cards_html.append(f'''<div class="topo-card">
  <div class="topo-header">
    <span class="topo-badge">{html.escape(ntype)}</span>
    <strong>{html.escape(name)}</strong>
  </div>
  {details_block}
</div>''')

    return f'''<div class="CGroup topo-section" id="doc-nav-topo" data-doc-topic="doc-nav-topo" data-anchor="Topology">
  <div class="CTopic">
    <h2 class="CTitle"><a name="Topology">Testbench Architecture Topology</a></h2>
    <div class="CBody">
      <div class="topo-grid">
        {"".join(cards_html)}
      </div>
    </div>
  </div>
</div>'''


def render_derived_classes_card(
    children: List[str],
    root_rel: str,
    class_to_doc_map: Optional[Dict[str, str]] = None,
    uvm_db: Optional[Dict[str, Any]] = None,
    global_anchor_maps: Optional[Dict[str, Any]] = None
) -> str:
    """
    Renders the collapsible Direct Subclasses card.
    """
    if not children:
        return ""

    class_to_doc_map = class_to_doc_map or {}
    uvm_db = uvm_db or {}
    global_anchor_maps = global_anchor_maps or {}

    pills = []
    for child in sorted(children):
        if child in class_to_doc_map:
            ch_doc = class_to_doc_map[child]
            target_id = global_anchor_maps.get(ch_doc, {}).get(child, 'doc-nav-main')
            pills.append(f'<a href="{root_rel}docs_view/{ch_doc}#{target_id}" class="derived-class-pill" data-target-id="{target_id}" title="Documentation for {child}">{child}</a>')
        elif child in uvm_db.get('classes', {}):
            ch_f = uvm_db['classes'][child]['file']
            ch_l = uvm_db['classes'][child]['start_line']
            pills.append(f'<a href="{root_rel}src_view/{ch_f}.html#L{ch_l}" class="derived-class-pill src-code-link" data-src-file="{ch_f}" data-src-line="{ch_l}" title="Source for {child}">{child}</a>')
        else:
            pills.append(f'<span class="derived-class-pill">{child}</span>')

    return f'''<div class="derived-classes-card collapsed">
  <div class="derived-classes-header" role="button" tabindex="0" title="Click to expand/collapse subclasses">
    <svg class="derived-classes-chevron" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
    <span>Direct Subclasses ({len(children)})</span>
  </div>
  <div class="derived-classes-list">{"".join(pills)}</div>
</div>'''


def render_example_callout(ex_rel: str, ex_title: str, root_rel: str) -> str:
    """
    Renders an interactive example callout box linking a UVM class to an example studio.
    """
    return f'''<div class="doc-example-callout">
  <span class="example-callout-icon">💡</span>
  <div class="example-callout-content">
    <strong>Interactive Example:</strong>
    <a href="{root_rel}examples_view/{ex_rel}" class="example-callout-link" data-example-url="{root_rel}examples_view/{ex_rel}" title="Open {ex_title}">{ex_title}</a>
  </div>
  <span class="example-callout-badge">Interactive Studio</span>
</div>'''


def render_code_block(clean_code: str, lang: Optional[str] = None) -> str:
    """
    Renders a syntax-highlighted code block with language badge and copy button.
    """
    if not lang:
        if any(clean_code.startswith(x) for x in ('prompt>', '<sim command', 'SIM_COMMAND')) or '+UVM_' in clean_code or '+uvm_' in clean_code:
            lang = "Command Line"
        elif clean_code.startswith('#') or 'extern "C"' in clean_code:
            lang = "C / DPI"
        else:
            lang = "SystemVerilog"

    highlighted = sh.highlight_doc_snippet(clean_code)

    return f'''<div class="code-block-container">
  <div class="code-block-header">
    <div class="code-block-lang">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
      <span>{lang}</span>
    </div>
    <button class="code-copy-btn" title="Copy code" aria-label="Copy code to clipboard">
      <svg class="copy-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      <span class="copy-text">Copy</span>
    </button>
  </div>
  <pre class="code-block-content"><code>{highlighted}</code></pre>
</div>'''


def render_diagram_card(src: str, title: str) -> str:
    """
    Renders an image/diagram inside a framed card with zoom lightbox support.
    """
    return f'''<figure class="doc-diagram-card">
  <div class="doc-diagram-body">
    <img src="{src}" class="doc-diagram-img" alt="{html.escape(title)}" title="Click to zoom" loading="lazy">
  </div>
  <figcaption class="doc-diagram-caption">{html.escape(title)}</figcaption>
</figure>'''


def render_html_shell(
    title: str,
    body_content: str,
    root_rel: str,
    breadcrumbs_html: str = "",
    banner_html: str = "",
    extra_html_classes: str = "",
    extra_body_classes: str = "",
    extra_scripts: Optional[List[str]] = None,
    data_payloads: Optional[Dict[str, str]] = None,
    include_toc: bool = True,
    is_full_page: bool = False
) -> str:
    """
    Renders a complete, unified HTML page shell complying with UVM modern design tokens.
    Automatically includes:
    - Inline anti-FOUC theme script
    - CSS stylesheets link
    - Breadcrumbs & Header banner
    - 2-column layout wrapper with #Content (or direct full-page layout if is_full_page is True)
    - In-page Table of Contents sidebar (if include_toc is True)
    - Data payloads (e.g. #zip-payload, #stepper-payload)
    - js/page_common.js script + any extra scripts
    """
    if is_full_page:
        html_cls = extra_html_classes.strip() if extra_html_classes else "full-page"
        body_cls = extra_body_classes.strip() if extra_body_classes else "full-body"
    else:
        html_cls = f"doc-page {extra_html_classes}".strip()
        body_cls = f"doc-body {extra_body_classes}".strip()

    # Scripts: page_common.js is always loaded
    scripts_list = [f"{root_rel}js/page_common.js"]
    if extra_scripts:
        scripts_list.extend(extra_scripts)

    scripts_markup = "\n  ".join([f'<script src="{s}"></script>' for s in scripts_list])

    # Payloads markup
    payloads_markup = ""
    if data_payloads:
        payload_elements = []
        for pid, pval in data_payloads.items():
            payload_elements.append(f'<div id="{html.escape(pid)}" style="display:none;" data-{html.escape(pid.replace("-payload", ""))}=\'{pval}\'></div>')
        payloads_markup = "\n  " + "\n  ".join(payload_elements)

    toc_markup = f"\n      {render_toc_sidebar()}" if include_toc else ""

    # Ensure #Content wrapper is only added if body_content does not already contain #Content or #Index
    if '<div id="Content"' not in body_content and '<div id=Content' not in body_content and '<div id="Index"' not in body_content and '<div id=Index' not in body_content:
        main_content_html = f'''        <div id="Content">
          {body_content}
        </div>'''
    else:
        main_content_html = f'''        {body_content}'''

    if is_full_page:
        inner_body = f"{body_content}{payloads_markup}"
    else:
        inner_body = f'''  <div class="doc-page-container">
    {breadcrumbs_html}
    {banner_html}
    <div class="doc-layout-wrapper">
      <div class="doc-main-content">
{main_content_html}
      </div>{toc_markup}
    </div>
  </div>{payloads_markup}'''

    return f'''<!DOCTYPE html>
<html lang="en" class="{html_cls}">
<head>
  <meta charset="UTF-8">
  <meta name="color-scheme" content="light dark">
  <script>
    (function () {{
      try {{
        var p = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
        var t = p || localStorage.getItem('theme');
        if (t) {{
          document.documentElement.setAttribute('data-theme', t);
          document.documentElement.style.colorScheme = t;
        }}
      }} catch (e) {{ }}
    }})();
  </script>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{root_rel}css/style.css">
</head>
<body class="{body_cls}">
{inner_body}
  {scripts_markup}
</body>
</html>'''


def render_source_viewer(
    rel_path: str,
    code: str,
    rows: List[str],
    syms: List[Dict[str, Any]],
    doc_rel: Optional[str] = None,
    root_rel: str = "../../"
) -> str:
    """
    Renders a unified, syntax-highlighted source view page (single file) for src_view/.
    Uses the unified render_html_shell, render_code_container, and render_code_pane.
    """
    line_count = len(rows)
    file_size_kb = round(len(code.encode('utf-8')) / 1024, 1)

    # Document link button
    doc_btn = ""
    if doc_rel:
        doc_href = f"{root_rel}docs_view/{doc_rel}"
        doc_btn = f'''<a href="{doc_href}" class="btn btn-outline src-to-doc-btn" data-doc-url="{doc_href}" title="View Reference Documentation for this file">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
        <span>Documentation</span>
      </a>'''

    raw_href = f"{root_rel}uvm-1.2/src/{rel_path}"

    # Symbol jump select
    sym_options = "".join([
        f'<option value="#L{s["line"]}">{html.escape(s["type"])}: {html.escape(s["name"])} (L{s["line"]})</option>'
        for s in syms if s.get("type") in ('class', 'macro')
    ])
    sym_select = f'''<select class="studio-file-select sym-jump-select" id="src-sym-select" aria-label="Jump to symbol" onchange="if(this.value) window.location.hash = this.value">
        <option value="">Jump to Symbol ({len(syms)} symbols)...</option>
        {sym_options}
      </select>''' if sym_options else ""

    # Sticky Toolbar
    toolbar_html = f'''  <div class="src-sticky-bar studio-toolbar">
    <div class="src-breadcrumbs">
      <a href="{root_rel}index.html#/src" target="_parent" class="src-nav-home" title="UVM Source Tree">src</a>
      <span class="sep">/</span>
      <span class="src-cur-file">{html.escape(rel_path)}</span>
      <span class="badge badge-info">{line_count} lines</span>
      <span class="badge badge-secondary">{file_size_kb} KB</span>
    </div>
    <div class="src-actions studio-toolbar-actions">
      {sym_select}
      {doc_btn}
      <button type="button" class="btn btn-outline studio-action-btn" id="btn-copy-code" title="Copy raw source code">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        <span>Copy Code</span>
      </button>
      <a href="{raw_href}" download class="btn btn-outline studio-action-btn" id="btn-download-raw" title="Download raw source file">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        <span>Raw</span>
      </a>
    </div>
  </div>'''

    pane_html = render_code_pane("".join(rows), pane_id="file-pane-0", is_active=True, filename=rel_path)
    container_html = render_code_container(pane_html, container_id="src-code-container", extra_classes="src-code-container")
    raw_textarea = f'  <textarea id="raw-source-text" style="display:none">{html.escape(code)}</textarea>'

    body_content = f"{toolbar_html}\n  {container_html}\n{raw_textarea}"

    return render_html_shell(
        title=f"{rel_path} | UVM 1.2 Source Code",
        body_content=body_content,
        root_rel=root_rel,
        extra_html_classes="src-page",
        extra_body_classes="src-viewer-body",
        include_toc=False,
        is_full_page=True
    )

