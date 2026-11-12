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
from functools import lru_cache
from string import Template
from typing import List, Dict, Any, Tuple, Optional, Union

# Import core syntax highlighter
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
import syntax_highlighter as sh


@lru_cache(maxsize=32)
def _load_template(rel_path: str) -> str:
    """Load an HTML/SVG template from scripts/templates with UTF-8 encoding."""
    return (TEMPLATES_DIR / rel_path).read_text(encoding="utf-8")


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
    Renders the unified code container wrapping code panes with integrated editor widgets:
    - Code Find Widget (Ctrl+F)
    - Quick Info Tooltip Popover (Hover)
    - Monaco IDE Pane (Activated on demand)
    Carries both .code-container and contextual classes (.studio-code-container, .src-code-container)
    for 100% backward compatibility.
    """
    classes = f"code-container {extra_classes}".strip()
    find_widget_html = '''    <div class="code-find-widget" id="code-find-widget" style="display:none;" role="search" aria-label="Find in file">
      <div class="find-input-wrap">
        <input type="text" id="find-input" placeholder="Find in file (Ctrl+F)..." autocomplete="off" spellcheck="false">
        <span class="find-count" id="find-count">0 of 0</span>
      </div>
      <div class="find-actions">
        <button type="button" class="find-btn" id="find-case-toggle" title="Match Case (Alt+C)">Aa</button>
        <button type="button" class="find-btn" id="find-word-toggle" title="Match Whole Word (Alt+W)">\\b</button>
        <button type="button" class="find-btn" id="find-prev" title="Previous Match (Shift+Enter)">▲</button>
        <button type="button" class="find-btn" id="find-next" title="Next Match (Enter)">▼</button>
        <button type="button" class="find-btn" id="find-close" title="Close (Esc)">✕</button>
      </div>
    </div>'''

    quick_info_html = '    <div class="code-quick-info-tooltip" id="code-quick-info" style="display:none;"></div>'
    monaco_pane_html = '    <div id="monaco-editor-pane" style="display:none;"></div>'

    return f'''<div class="{classes}" id="{container_id}">
{find_widget_html}
{quick_info_html}
{monaco_pane_html}
{panes_html}
</div>'''


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
              <button type="button" class="btn btn-sm btn-outline studio-action-btn" id="btn-toggle-find" title="Find in file (Ctrl+F)" aria-label="Find in file">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              </button>
              <button type="button" class="btn btn-sm btn-outline studio-action-btn" id="btn-toggle-wrap" title="Toggle Word Wrap (Alt+Z)" aria-label="Toggle Word Wrap">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="15" y2="12"/><polyline points="14 16 18 12 14 8"/><path d="M21 18H9a4 4 0 0 1 0-8h6"/></svg>
              </button>
              <button type="button" class="btn btn-sm btn-outline studio-action-btn btn-monaco-ide" id="btn-toggle-monaco" title="Toggle Monaco VS Code Editor" aria-label="Monaco IDE">
                <svg class="monaco-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .326 8.74L3.899 12 .326 15.26a1 1 0 0 0 .001 1.479L1.65 17.94a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352zM18 17.5l-6-5.5 6-5.5v11z"/></svg>
                <span>Monaco</span>
              </button>
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


def render_scenario_animation(anim_type: str) -> str:
    """
    Renders visual concept animations (Phase 2) for each specific test intent.
    """
    if anim_type == "fifo":
        slots_html = ''.join([f'<span class="slot" data-slot="{i}"><span class="slot-idx">{i}</span></span>' for i in range(10)])
        return Template(_load_template("animations/fifo.html")).substitute(slots_html=slots_html)

    if anim_type in ("objections", "tlm2", "ral", "phasing"):
        return _load_template(f"animations/{anim_type}.html")

    return ""


def render_flow_stepper(stepper_steps: List[Dict[str, Any]], anim_type: str = "") -> str:
    """
    Renders the Interactive Visual Flow Stepper Section (Test Scenario Walkthrough).
    """
    if not stepper_steps:
        return ""

    stepper_nodes_html = ''.join([
        f'<button type="button" role="tab" id="step-tab-{i+1}" '
        f'class="step-node {("active" if i == 0 else "")}" data-step="{i+1}" '
        f'aria-selected="{("true" if i == 0 else "false")}" '
        f'aria-current="{("step" if i == 0 else "false")}" '
        f'aria-controls="step-detail-card" '
        f'tabindex="{("0" if i == 0 else "-1")}">'
        f'<span class="step-num" aria-hidden="true">{i+1}</span>'
        f'<span class="step-title">{html.escape(s["title"].split(". ")[1] if ". " in s["title"] else s["title"])}</span>'
        f'</button>'
        for i, s in enumerate(stepper_steps)
    ])

    first = stepper_steps[0]
    initial_state = first.get("state", "")
    state_badge_html = f'<span class="scenario-state-pill" id="step-state-badge">{html.escape(initial_state)}</span>' if initial_state else '<span class="scenario-state-pill" id="step-state-badge" style="display:none;"></span>'

    anim_markup = ""
    if anim_type:
        anim_markup = f'''        <div class="scenario-anim-section" id="scenario-anim-section" data-anim="{html.escape(anim_type)}">
          {render_scenario_animation(anim_type)}
        </div>'''

    total_steps = len(stepper_steps)

    return f'''<!-- Interactive Visual Flow Stepper Section -->
<div class="CGroup" id="doc-nav-stepper" data-doc-topic="doc-nav-stepper" data-anchor="FlowStepper">
  <div class="CTopic">
    <h2 class="CTitle"><a name="FlowStepper">Test Scenario Walkthrough</a></h2>
    <div class="CBody">
      <div class="stepper-section" id="visual-flow-stepper">
        <div class="section-header-row">
          <div class="section-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>
            <span class="section-title-text">Interactive Scenario &amp; Verification Intent</span>
            {state_badge_html}
          </div>
          <div class="stepper-controls">
            <span class="stepper-progress-label" id="stepper-progress-label" aria-live="polite">1 / {total_steps}</span>
            <button type="button" class="btn btn-sm btn-outline" id="stepper-prev" aria-label="Previous step" disabled>&larr; Previous</button>
            <button type="button" class="btn btn-sm btn-outline" id="stepper-play" aria-label="Auto-play scenario">Play &#9654;</button>
            <button type="button" class="btn btn-sm btn-primary" id="stepper-next" aria-label="Next step">Next Step &rarr;</button>
          </div>
        </div>

        <div class="stepper-timeline" id="stepper-timeline" role="tablist" aria-label="Test scenario steps">
          {stepper_nodes_html}
        </div>
{anim_markup}
        <div class="step-card" id="step-detail-card" role="tabpanel" aria-live="polite" aria-labelledby="step-tab-1">
          <div class="step-card-header">
            <h4 id="step-active-title">{html.escape(first.get("title", ""))}</h4>
            <span class="step-active-comp" id="step-active-comp">Target: {html.escape(first.get("component", ""))}</span>
          </div>
          <p id="step-active-desc">{html.escape(first.get("desc", ""))}</p>
          <div class="step-log-hint">
            <strong>Expected Log Output:</strong>
            <code id="step-active-log">{html.escape(first.get("log_snippet", ""))}</code>
          </div>
          <div class="step-card-actions">
            <button type="button" class="btn btn-xs btn-outline" id="btn-jump-code" title="Scroll to code in Code Studio">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
              <span>Jump to Code</span>
            </button>
            <button type="button" class="btn btn-xs btn-outline" id="btn-jump-log" title="Scroll to log message in Terminal">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
              <span>Jump to Terminal Log</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>'''


def render_source_notes(source_notes: Dict[str, Any]) -> str:
    """
    Renders the Source Specification & Design Notes card.
    Displays extracted comments, intent, and architectural notes from the test bench files or README.
    source_notes: dict with keys:
      - 'source_file': filename where comments were extracted from (e.g. 'test.sv', 'README.txt')
      - 'notes_html': formatted HTML body
      - 'raw_text': raw extracted comment text
    """
    if not source_notes or not source_notes.get("notes_html"):
        return ""

    source_file = html.escape(source_notes.get("source_file", "source"))
    notes_html = source_notes.get("notes_html", "")

    return f'''<div class="CGroup example-source-notes" id="doc-nav-notes" data-doc-topic="doc-nav-notes" data-anchor="DesignNotes">
  <div class="CTopic">
    <h2 class="CTitle"><a name="DesignNotes">Source Specification &amp; Design Notes</a></h2>
    <div class="source-notes-header">
      <div class="notes-title-box">
        <svg class="notes-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
        <span class="notes-heading-label">Test Intent &amp; Implementation Walkthrough</span>
      </div>
      <span class="notes-file-badge" data-file="{source_file}" title="Click to view file in Code Studio">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="16 18 22 12 16 6"></polyline>
          <polyline points="8 6 2 12 8 18"></polyline>
        </svg>
        <span>Source: <strong>{source_file}</strong></span>
      </span>
    </div>
    <div class="CBody source-notes-body">
      {notes_html}
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


def render_class_hierarchy_card(
    cname: str,
    root_rel: str,
    class_to_doc_map: Optional[Dict[str, str]] = None,
    uvm_db: Optional[Dict[str, Any]] = None,
    global_anchor_maps: Optional[Dict[str, Any]] = None
) -> str:
    """
    Renders the unified, rich Class Hierarchy widget showing lineage breadcrumbs
    (ancestors -> active class) and direct subclasses with role tags.
    """
    class_to_doc_map = class_to_doc_map or {}
    uvm_db = uvm_db or {}
    global_anchor_maps = global_anchor_maps or {}
    classes = uvm_db.get('classes', {})
    c_info = classes.get(cname, {})
    if not c_info:
        return ""

    def is_descendant(sub, anc):
        c = sub
        vis = set()
        while c and c in classes and c not in vis:
            vis.add(c)
            p = classes[c].get('parent')
            if p == anc or (p and p.startswith(anc)):
                return True
            c = p
        return False

    def get_role_tag(name):
        if name == 'uvm_component' or is_descendant(name, 'uvm_component'):
            return ('component', 'Component')
        if name == 'uvm_sequence_base' or is_descendant(name, 'uvm_sequence_base') or 'sequence' in name or 'seq_item' in name:
            return ('sequence', 'Sequence')
        if name.startswith('uvm_reg') or name.startswith('uvm_vreg') or name.startswith('uvm_mem'):
            return ('reg', 'Register Model')
        if 'tlm' in name or 'port' in name or 'export' in name or 'fifo' in name:
            return ('tlm', 'TLM Channel')
        if 'phase' in name or is_descendant(name, 'uvm_phase'):
            return ('phase', 'Phasing')
        if name == 'uvm_object' or is_descendant(name, 'uvm_object'):
            return ('object', 'Object')
        return ('utility', 'Utility')

    role_key, role_label = get_role_tag(cname)

    # 1. Trace ancestors
    ancestors = []
    curr = c_info.get('parent')
    visited = set()
    while curr and curr not in visited:
        visited.add(curr)
        clean_p = re.sub(r'#\(.*?\)', '', curr).strip()
        ancestors.insert(0, (curr, clean_p))
        p_info = classes.get(clean_p, {})
        curr = p_info.get('parent') if p_info else None

    # 2. Build lineage items (each step is an indivisible unit containing node + arrow)
    arrow_svg = '<svg class="hierarchy-flow-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>'
    flow_steps = []
    for raw_p, clean_p in ancestors:
        link_href = None
        target_id = 'doc-nav-main'
        if clean_p in class_to_doc_map:
            ch_doc = class_to_doc_map[clean_p]
            target_id = global_anchor_maps.get(ch_doc, {}).get(clean_p, 'doc-nav-main')
            link_href = f"{root_rel}docs_view/{ch_doc}#{target_id}"
        elif clean_p in classes and classes[clean_p].get('file'):
            cf = classes[clean_p]['file']
            cl = classes[clean_p].get('start_line', 1)
            link_href = f"{root_rel}src_view/{cf}.html#L{cl}"

        if link_href:
            node_html = f'<a href="{link_href}" class="hierarchy-flow-node parent" data-target-id="{target_id}" title="Base class: {clean_p}">{clean_p}</a>'
        else:
            node_html = f'<span class="hierarchy-flow-node parent static">{clean_p}</span>'

        flow_steps.append(f'<span class="hierarchy-flow-step">{node_html}{arrow_svg}</span>')

    methods_count = len(c_info.get('methods', {}))
    is_virtual = c_info.get('is_virtual', False)
    current_node = f'<span class="hierarchy-flow-node current" title="Current class: {cname}">{cname}</span>'
    flow_steps.append(f'<span class="hierarchy-flow-step current-step">{current_node}</span>')

    flow_html = "".join(flow_steps)

    # 3. Children / Subclasses
    children = c_info.get('children', [])
    subclasses_html = ""
    if children:
        pills = []
        for child in sorted(children):
            if child in class_to_doc_map:
                ch_doc = class_to_doc_map[child]
                target_id = global_anchor_maps.get(ch_doc, {}).get(child, 'doc-nav-main')
                pills.append(f'<a href="{root_rel}docs_view/{ch_doc}#{target_id}" class="derived-class-pill" data-target-id="{target_id}" title="Subclass: {child}">{child}</a>')
            elif child in classes and classes[child].get('file'):
                ch_f = classes[child]['file']
                ch_l = classes[child]['start_line']
                pills.append(f'<a href="{root_rel}src_view/{ch_f}.html#L{ch_l}" class="derived-class-pill src-code-link" data-src-file="{ch_f}" data-src-line="{ch_l}" title="Source for {child}">{child}</a>')
            else:
                pills.append(f'<span class="derived-class-pill">{child}</span>')

        subclasses_html = f'''
  <div class="hierarchy-subclasses-card collapsed">
    <div class="derived-classes-header" role="button" tabindex="0" title="Click to expand/collapse subclasses">
      <svg class="derived-classes-chevron" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
      <span>Direct Subclasses ({len(children)})</span>
    </div>
    <div class="derived-classes-list">{"".join(pills)}</div>
  </div>'''

    return f'''<div class="class-hierarchy-widget" data-cname="{cname}">
  <div class="hierarchy-widget-header">
    <div class="hierarchy-widget-title">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><path d="M10 6.5h4M17.5 10v4"/></svg>
      <span>Class Hierarchy &amp; Topology</span>
    </div>
    <div class="hierarchy-widget-badges">
      <span class="hierarchy-role-tag role-{role_key}">{role_label}</span>
      {f'<span class="hierarchy-virtual-badge">virtual</span>' if is_virtual else ''}
      {f'<span class="hierarchy-method-badge">{methods_count} methods</span>' if methods_count else ''}
    </div>
  </div>
  <div class="hierarchy-lineage-flow">
    {flow_html}
  </div>
  {subclasses_html}
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

    # Scripts: uvm_symbol_quick.js (deferred) and page_common.js are always loaded
    scripts_list = [f"{root_rel}js/uvm_symbol_quick.js", f"{root_rel}js/page_common.js"]
    if extra_scripts:
        scripts_list.extend(extra_scripts)

    scripts_markup = "\n  ".join([
        f'<script src="{s}" defer></script>' if s.endswith("uvm_symbol_quick.js") else f'<script src="{s}"></script>'
        for s in scripts_list
    ])

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

    return Template(_load_template("page_shell.html")).substitute(
        html_cls=html_cls,
        title=html.escape(title),
        root_rel=root_rel,
        body_cls=body_cls,
        inner_body=inner_body,
        scripts_markup=scripts_markup,
    ).rstrip("\n")


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
        for s in syms if s.get("type") in ('class', 'macro', 'type', 'enum', 'variable', 'function', 'task', 'port')
    ])
    displayed_syms_count = sum(1 for s in syms if s.get("type") in ('class', 'macro', 'type', 'enum', 'variable', 'function', 'task', 'port'))
    sym_select = f'''<select class="studio-file-select sym-jump-select" id="src-sym-select" aria-label="Jump to symbol" onchange="if(this.value) window.location.hash = this.value">
        <option value="">Jump to Symbol ({displayed_syms_count} symbols)...</option>
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
      <button type="button" class="btn btn-outline studio-action-btn" id="btn-toggle-find" title="Find in file (Ctrl+F)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <span>Find</span>
      </button>
      <button type="button" class="btn btn-outline studio-action-btn" id="btn-toggle-wrap" title="Toggle Word Wrap (Alt+Z)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="15" y2="12"/><polyline points="14 16 18 12 14 8"/><path d="M21 18H9a4 4 0 0 1 0-8h6"/></svg>
        <span>Wrap</span>
      </button>
      <button type="button" class="btn btn-outline studio-action-btn btn-monaco-ide" id="btn-toggle-monaco" title="Toggle Monaco VS Code Editor">
        <svg class="monaco-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .326 8.74L3.899 12 .326 15.26a1 1 0 0 0 .001 1.479L1.65 17.94a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352zM18 17.5l-6-5.5 6-5.5v11z"/></svg>
        <span>Monaco IDE</span>
      </button>
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

