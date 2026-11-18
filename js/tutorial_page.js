/**
 * UVM 1.2 Step-by-Step Interactive Tutorial Controller
 * Uses third-party libraries (Cytoscape.js, Mermaid.js, diff2html, JSZip)
 * alongside PageCommon & ExamplePage controllers.
 */
(function initTutorialPage(global) {
  'use strict';

  const PROGRESS_KEY = 'uvm_tutorial_progress';

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function getTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function getTutorialContext() {
    try {
      const m = window.location.pathname.replace(/\\/g, '/').match(/(tutorial_view\/[^/]+\.html)$/);
      if (m) {
        return { url: m[1], title: document.title.split('|')[0].trim() };
      }
    } catch (e) { }
    return null;
  }

  function openDocFromTutorial(docUrl) {
    if (!docUrl) return;
    const fromTut = getTutorialContext();
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({
        type: 'openDocView',
        url: docUrl,
        fromTutorial: fromTut || undefined
      }, '*');
    } else {
      window.location.href = '../' + docUrl.replace(/^(\.\.\/)+/, '');
    }
  }

  function openTutorialChapter(tutUrl) {
    if (!tutUrl) return;
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({ type: 'openTutorialView', url: tutUrl }, '*');
    } else {
      window.location.href = '../' + tutUrl.replace(/^(\.\.\/)+/, '');
    }
  }

  function focusStudioFile(fileName) {
    if (!fileName) return;
    const tabs = document.querySelectorAll('.studio-tab');
    let targetIdx = -1;
    tabs.forEach(function (tab, idx) {
      const tName = tab.getAttribute('title') || (tab.querySelector('.tab-name') ? tab.querySelector('.tab-name').textContent.trim() : '');
      if (tName === fileName) {
        targetIdx = idx;
      }
    });
    if (targetIdx >= 0) {
      tabs[targetIdx].click();
      const studioEl = document.getElementById('doc-nav-studio');
      if (studioEl) {
        studioEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }

  // =========================================================================
  // 1. Progress Persistence (localStorage)
  // =========================================================================

  function readProgress() {
    try {
      const raw = localStorage.getItem(PROGRESS_KEY);
      if (!raw) return { completed: {}, quizScores: {} };
      const parsed = JSON.parse(raw);
      return {
        completed: (parsed && parsed.completed) || {},
        quizScores: (parsed && parsed.quizScores) || {}
      };
    } catch (e) {
      return { completed: {}, quizScores: {} };
    }
  }

  function writeProgress(state) {
    try {
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(state));
    } catch (e) { }
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({ type: 'tutorialProgressUpdated', progress: state }, '*');
    }
  }

  function initCompletionControls() {
    const pill = document.getElementById('tut-completion-pill');
    const btn = document.getElementById('tut-mark-complete-btn');
    const slug = (pill && pill.getAttribute('data-chapter-slug')) || (btn && btn.getAttribute('data-chapter-slug'));
    if (!slug) return;

    function syncUI() {
      const prog = readProgress();
      const isDone = !!prog.completed[slug];
      if (pill) {
        pill.textContent = isDone ? 'Completed' : 'In Progress';
        pill.classList.toggle('is-completed', isDone);
      }
      if (btn) {
        btn.textContent = isDone ? 'Completed (Click to Undo)' : 'Mark Chapter Complete';
        btn.classList.toggle('is-completed', isDone);
      }
    }

    if (btn) {
      btn.addEventListener('click', function () {
        const prog = readProgress();
        if (prog.completed[slug]) {
          delete prog.completed[slug];
        } else {
          prog.completed[slug] = true;
        }
        writeProgress(prog);
        syncUI();
      });
    }
    syncUI();
  }

  // =========================================================================
  // 2. Mermaid.js Diagrams with Dynamic Theme Re-Rendering
  // =========================================================================

  function renderMermaidAll() {
    if (!global.mermaid) return;
    const blocks = document.querySelectorAll('pre.mermaid');
    if (!blocks.length) return;

    blocks.forEach(function (el) {
      if (!el.dataset.mermaidSrc) {
        el.dataset.mermaidSrc = el.textContent;
      } else {
        el.textContent = el.dataset.mermaidSrc;
        el.removeAttribute('data-processed');
      }
    });

    try {
      global.mermaid.initialize({
        startOnLoad: false,
        theme: getTheme() === 'dark' ? 'dark' : 'default',
        securityLevel: 'loose',
        flowchart: { curve: 'basis' }
      });
      global.mermaid.run({ nodes: Array.from(blocks) }).then(function () {
        document.querySelectorAll('.tut-mermaid-wrap').forEach(function (wrap) {
          if (!wrap.querySelector('.tut-svg-zoom-btn')) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'doc-img-zoom-btn tut-svg-zoom-btn';
            btn.title = 'Open diagram in image viewer';
            btn.innerHTML = '<svg class="zoom-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>';
            wrap.appendChild(btn);
          }
        });
      }).catch(function () { });
    } catch (e) {
      console.warn('[Tutorial] Mermaid render warning:', e);
    }
  }

  // =========================================================================
  // 3. Chapter 2 Interactive Stimuli / Checks / Metrics Matrix
  // =========================================================================

  function initScmMatrix() {
    const detailEl = document.getElementById('tut-scm-detail');
    const tabs = document.querySelectorAll('.tut-scm-tab');
    if (!detailEl || !tabs.length) return;

    const PILLARS = {
      stimuli: {
        badge: 'Pillar 1 · Stimuli Generation',
        title: 'What We Inject Into the DUT',
        summary: 'Sequences and drivers create randomized, legal, and stress transactions without ever deciding PASS or FAIL.',
        classes: ['uvm_sequence_item', 'uvm_sequence', 'uvm_sequencer', 'uvm_driver'],
        rules: [
          'Generate abstract transactions (alu_item) with SystemVerilog constraints.',
          'Keep pin timing strictly inside uvm_driver via virtual interface clocking blocks.',
          'Never inspect DUT outputs inside sequences except for protocol handshaking (rsp).'
        ],
        docUrl: 'docs_view/overviews/sequences-txt.html',
        docLabel: 'Read Sequences Overview'
      },
      checks: {
        badge: 'Pillar 2 · Functional & Protocol Checking',
        title: 'How We Prove the DUT Behaved Correctly',
        summary: 'Passive monitors, SVA interface assertions, Reference Models, and Scoreboards observe real bus pins independently.',
        classes: ['uvm_monitor', 'uvm_scoreboard', 'uvm_tlm_analysis_fifo'],
        rules: [
          'Use concurrent SVA assertions inside alu_if for cycle-accurate pin protocol checks.',
          'Use passive uvm_monitor -> uvm_analysis_port -> uvm_scoreboard for data integrity.',
          'Checkers remain active even when block drivers are disabled (UVM_PASSIVE reuse).'
        ],
        docUrl: 'docs_view/comps/uvm_scoreboard-svh.html#uvm_scoreboard',
        docLabel: 'Read uvm_scoreboard Docs'
      },
      metrics: {
        badge: 'Pillar 3 · Verification Closure Metrics',
        title: 'How We Know We Tested Enough',
        summary: 'Functional coverage subscribers sample what actually crossed the DUT pins and map directly back to vPlan targets.',
        classes: ['uvm_subscriber', 'uvm_analysis_export'],
        rules: [
          'Connect alu_cov_subscriber to monitor req_ap—never sample inside sequences.',
          'Combine single-field bins with cross coverage and filter impossible combinations via ignore_bins.',
          'Use coverage holes to refine sequence distributions (`dist`) until 100% vPlan closure.'
        ],
        docUrl: 'docs_view/comps/uvm_subscriber-svh.html#uvm_subscriber',
        docLabel: 'Read uvm_subscriber Docs'
      },
      antipattern: {
        badge: 'Anti-Pattern Simulator',
        title: 'What Breaks If You Mix Stimuli, Checks & Metrics?',
        summary: 'Imagine integrating pkt_alu into an SoC where an embedded CPU replaces our alu_driver:',
        classes: ['UVM_PASSIVE', 'uvm_agent'],
        rules: [
          'FAIL: Checks placed inside alu_driver vanish completely when is_active = UVM_PASSIVE.',
          'FAIL: Covergroups sampled in alu_seq record software CPU traffic inaccurately or miss stalled transfers.',
          'PASS: With decoupled Monitor -> Scoreboard + Subscriber, 100% of checking & coverage works at SoC level unchanged!'
        ],
        docUrl: 'docs_view/comps/uvm_agent-svh.html#uvm_agent',
        docLabel: 'Read uvm_agent Docs'
      }
    };

    function renderPillar(key) {
      const p = PILLARS[key] || PILLARS.stimuli;
      tabs.forEach(function (t) {
        const active = t.getAttribute('data-pillar') === key;
        t.classList.toggle('active', active);
        t.setAttribute('aria-selected', active ? 'true' : 'false');
      });
      detailEl.innerHTML =
        `<div class="tut-scm-header">
          <span class="tut-insp-badge">${escapeHtml(p.badge)}</span>
          <h3>${escapeHtml(p.title)}</h3>
          <p>${escapeHtml(p.summary)}</p>
        </div>
        <ul class="tut-scm-rules">${p.rules.map(function (r) { return `<li>${escapeHtml(r)}</li>`; }).join('')}</ul>
        <div class="tut-scm-footer">
          <div class="tut-scm-apis">${p.classes.map(function (c) { return `<span class="tut-mini-chip">${escapeHtml(c)}</span>`; }).join('')}</div>
          <button type="button" class="btn btn-sm btn-primary tut-open-doc-btn" data-doc="${escapeHtml(p.docUrl)}">${escapeHtml(p.docLabel)} &rarr;</button>
        </div>`;

      const docBtn = detailEl.querySelector('.tut-open-doc-btn');
      if (docBtn) {
        docBtn.addEventListener('click', function () {
          openDocFromTutorial(docBtn.getAttribute('data-doc'));
        });
      }
    }

    tabs.forEach(function (t) {
      t.addEventListener('click', function () {
        renderPillar(t.getAttribute('data-pillar'));
      });
    });
    renderPillar('stimuli');
  }

  // =========================================================================
  // 4. Cytoscape.js Interactive Graphs (V-Cycle, Arch Diff & 4-in-1 Capstone)
  // =========================================================================

  let cyInstance = null;

  function buildCytoscapeStyles(isDark) {
    const textCol = isDark ? '#e8eaed' : '#1f2937';
    const nodeBg = isDark ? '#2a2d34' : '#ffffff';
    const nodeBorder = isDark ? '#4a505c' : '#cbd5e1';
    const containerBg = isDark ? 'rgba(30, 41, 59, 0.45)' : 'rgba(241, 245, 249, 0.75)';
    const edgeCol = isDark ? '#64748b' : '#94a3b8';

    return [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'text-wrap': 'wrap',
          'text-max-width': '135px',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-family': 'Google Sans, Roboto, sans-serif',
          'font-size': '11px',
          'font-weight': '600',
          'color': textCol,
          'background-color': nodeBg,
          'border-color': nodeBorder,
          'border-width': 2,
          'shape': 'round-rectangle',
          'width': 'label',
          'height': 'label',
          'padding': '10px',
          'transition-property': 'background-color, border-color, opacity',
          'transition-duration': '0.2s'
        }
      },
      {
        selector: 'node[kind="container"]',
        style: {
          'text-valign': 'top',
          'text-halign': 'left',
          'text-margin-y': -6,
          'text-margin-x': 8,
          'font-size': '11px',
          'background-color': containerBg,
          'border-style': 'dashed',
          'border-color': isDark ? '#60a5fa' : '#3b82f6',
          'padding': '18px'
        }
      },
      { selector: 'node[role="architect"], node[kind="test"]', style: { 'border-color': '#3b82f6', 'background-color': isDark ? '#1e3a5f' : '#eff6ff' } },
      { selector: 'node[role="designer"], node[kind="dut"]', style: { 'border-color': '#f59e0b', 'background-color': isDark ? '#452c0b' : '#fffbeb' } },
      { selector: 'node[role="verifier"], node[kind="check"]', style: { 'border-color': '#10b981', 'background-color': isDark ? '#0f3d2e' : '#ecfdf5' } },
      { selector: 'node[kind="seq"], node[kind="driver"]', style: { 'border-color': '#6366f1', 'background-color': isDark ? '#272952' : '#eef2ff' } },
      { selector: 'node[kind="monitor"], node[kind="metric"]', style: { 'border-color': '#0ea5e9', 'background-color': isDark ? '#0c3547' : '#f0f9ff' } },
      { selector: 'node[kind="ral"]', style: { 'border-color': '#ec4899', 'background-color': isDark ? '#4a1834' : '#fdf2f8' } },
      { selector: 'node[kind="tlm"], node[kind="external"]', style: { 'border-color': '#8b5cf6', 'background-color': isDark ? '#321c54' : '#f5f3ff' } },
      { selector: 'node[kind="hook"]', style: { 'border-color': '#ef4444', 'background-color': isDark ? '#4c181d' : '#fef2f2' } },
      {
        selector: 'node[?isNew]',
        style: {
          'border-width': 3,
          'border-color': '#10b981',
          'background-color': isDark ? '#064e3b' : '#d1fae5'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 1.8,
          'line-color': edgeCol,
          'target-arrow-color': edgeCol,
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'font-size': '9px',
          'color': isDark ? '#cbd5e1' : '#475569',
          'text-background-color': isDark ? '#1f2023' : '#ffffff',
          'text-background-opacity': 0.85,
          'text-background-padding': '2px',
          'text-rotation': 'autorotate'
        }
      },
      {
        selector: 'edge[style="dashed"]',
        style: { 'line-style': 'dashed' }
      },
      {
        selector: '.dimmed',
        style: { 'opacity': 0.16 }
      },
      {
        selector: '.highlighted',
        style: {
          'border-width': 3.5,
          'border-color': '#1a73e8',
          'opacity': 1
        }
      },
      {
        selector: 'edge.highlighted',
        style: {
          'width': 3,
          'line-color': '#1a73e8',
          'target-arrow-color': '#1a73e8',
          'opacity': 1
        }
      },
      {
        selector: 'node.stepper-active',
        style: {
          'border-width': 4,
          'border-color': '#f59e0b',
          'opacity': 1
        }
      }
    ];
  }

  function initCytoscapeGraph() {
    const graphEl = document.getElementById('tut-cy-graph');
    const payloadEl = document.getElementById('tut-graph-payload');
    if (!graphEl || !payloadEl || !global.cytoscape) return;

    let payload = null;
    try {
      payload = JSON.parse(payloadEl.getAttribute('data-tut-graph') || '{}');
    } catch (e) {
      console.warn('[Tutorial] Invalid graph payload', e);
      return;
    }

    const elements = [];
    (payload.nodes || []).forEach(function (n) {
      const nodeObj = { data: Object.assign({}, n) };
      if (typeof n.x === 'number' && typeof n.y === 'number') {
        nodeObj.position = { x: n.x, y: n.y };
      }
      elements.push(nodeObj);
    });
    (payload.edges || []).forEach(function (e, idx) {
      elements.push({ data: Object.assign({ id: 'edge_' + idx }, e) });
    });

    cyInstance = global.cytoscape({
      container: graphEl,
      elements: elements,
      style: buildCytoscapeStyles(getTheme() === 'dark'),
      layout: { name: 'preset', padding: 34 },
      wheelSensitivity: 0.25,
      minZoom: 0.25,
      maxZoom: 2.2
    });
    cyInstance.fit(undefined, 34);
    window.addEventListener('resize', function () {
      if (cyInstance) {
        cyInstance.resize();
        cyInstance.fit(undefined, 34);
      }
    });

    const fitBtn = document.getElementById('tut-cy-fit');
    if (fitBtn) {
      fitBtn.addEventListener('click', function () {
        if (cyInstance) cyInstance.fit(undefined, 34);
      });
    }

    // Full-Page Toggle for Interactive Panel / Capstone Explorer
    const fsBtn = document.getElementById('tut-cy-fullscreen');
    const panelEl = graphEl.closest('.tut-interactive-panel, .capstone-explorer');
    function setPanelFullscreen(expand) {
      if (!panelEl || !fsBtn) return;
      panelEl.classList.toggle('tut-panel-fullscreen', expand);
      fsBtn.innerHTML = expand
        ? '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="4 14 10 14 10 20"></polyline><polyline points="20 10 14 10 14 4"></polyline><line x1="14" y1="10" x2="21" y2="3"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg><span>Exit</span>'
        : '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg><span>Fullscreen</span>';
      fsBtn.classList.toggle('active', expand);
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({ type: 'setTutorialPanelFullscreen', active: expand }, '*');
      }
      if (cyInstance) {
        setTimeout(function () {
          cyInstance.resize();
          cyInstance.fit(undefined, 34);
        }, 60);
      }
    }
    if (fsBtn && panelEl) {
      fsBtn.addEventListener('click', function () {
        setPanelFullscreen(!panelEl.classList.contains('tut-panel-fullscreen'));
      });
      window.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && panelEl.classList.contains('tut-panel-fullscreen')) {
          setPanelFullscreen(false);
        }
      });
      window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'exitTutorialPanelFullscreen' && panelEl.classList.contains('tut-panel-fullscreen')) {
          setPanelFullscreen(false);
        }
      });
    }

    // Retractable / Collapsible Inspector Panel
    const inspToggleBtn = document.getElementById('tut-insp-toggle');
    const splitEl = graphEl.closest('.tut-cy-split');
    function setInspectorCollapsed(collapsed) {
      if (!splitEl || !inspToggleBtn) return;
      splitEl.classList.toggle('is-inspector-collapsed', collapsed);
      inspToggleBtn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      const isCapstone = splitEl.classList.contains('capstone-cy-split');
      if (isCapstone) {
        inspToggleBtn.innerHTML = collapsed
          ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="15" x2="21" y2="15"></line><polyline points="9 13 12 10 15 13"></polyline></svg>'
          : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="15" x2="21" y2="15"></line><polyline points="9 10 12 13 15 10"></polyline></svg>';
      } else {
        inspToggleBtn.innerHTML = collapsed
          ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="15" y1="3" x2="15" y2="21"></line><polyline points="13 9 10 12 13 15"></polyline></svg>'
          : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="15" y1="3" x2="15" y2="21"></line><polyline points="10 9 13 12 10 15"></polyline></svg>';
      }
      inspToggleBtn.title = collapsed ? 'Show Inspector' : 'Hide Inspector';
      inspToggleBtn.setAttribute('aria-label', inspToggleBtn.title);
      if (cyInstance) {
        setTimeout(function () {
          cyInstance.resize();
          cyInstance.fit(undefined, 34);
        }, 50);
      }
    }
    if (inspToggleBtn && splitEl) {
      inspToggleBtn.addEventListener('click', function () {
        setInspectorCollapsed(!splitEl.classList.contains('is-inspector-collapsed'));
      });
    }

    function updateInspector(data) {
      const roleEl = document.getElementById('tut-insp-role');
      const titleEl = document.getElementById('tut-insp-title');
      const descEl = document.getElementById('tut-insp-desc');
      const extraEl = document.getElementById('tut-insp-extra');
      const actionsEl = document.getElementById('tut-insp-actions');
      if (!titleEl || !descEl) return;

      if (payload.mode === 'vcycle') {
        if (roleEl) roleEl.textContent = data.owner || 'Stage';
        titleEl.textContent = data.label || '';
        descEl.textContent = data.deliverables || '';
        if (extraEl) {
          extraEl.innerHTML = data.handoff
            ? `<div class="tut-insp-kv"><strong>Handoff:</strong> ${escapeHtml(data.handoff)}</div>`
            : '';
        }
        if (actionsEl) {
          actionsEl.innerHTML = data.docUrl
            ? `<button type="button" class="btn btn-sm btn-primary tut-icon-btn" data-insp-doc="${escapeHtml(data.docUrl)}" title="Open UVM 1.2 Reference"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg><span>UVM Doc</span></button>`
            : '';
        }
      } else {
        const layerTxt = data.layer ? `Ch. ${String(data.layer).padStart(2, '0')}` : 'Component';
        if (roleEl) roleEl.textContent = `${data.role || 'UVM Block'} · ${layerTxt}`;
        titleEl.textContent = (data.label || data.id || '').replace(/\n/g, ' ');
        descEl.textContent = data.summary || '';
        if (extraEl) {
          const ports = Array.isArray(data.ports) ? data.ports : [];
          extraEl.innerHTML = ports.length
            ? `<div class="tut-insp-kv"><strong>Interfaces / Ports:</strong><div class="tut-insp-ports">${ports.map(function (p) { return `<span class="tut-mini-chip">${escapeHtml(p)}</span>`; }).join('')}</div></div>`
            : '';
        }
        if (actionsEl) {
          const btns = [];
          if (payload.mode === 'capstone' && data.chapterUrl) {
            const chNumStr = String(data.chapterNum || data.layer).padStart(2, '0');
            btns.push(`<button type="button" class="btn btn-sm btn-primary tut-icon-btn" data-insp-tut="${escapeHtml(data.chapterUrl)}" title="Review Chapter ${chNumStr}"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="15 18 9 12 15 6"></polyline></svg><span>Ch. ${chNumStr}</span></button>`);
          }
          if (data.studioFile) {
            btns.push(`<button type="button" class="btn btn-sm btn-outline tut-icon-btn" data-insp-file="${escapeHtml(data.studioFile)}" title="Inspect ${escapeHtml(data.studioFile)}"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg><span>${escapeHtml(data.studioFile)}</span></button>`);
          }
          if (data.docUrl) {
            btns.push(`<button type="button" class="btn btn-sm btn-outline tut-icon-btn" data-insp-doc="${escapeHtml(data.docUrl)}" title="Open UVM 1.2 Reference"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg><span>UVM Doc</span></button>`);
          }
          actionsEl.innerHTML = btns.join('');
        }
      }

      if (actionsEl) {
        const docBtn = actionsEl.querySelector('[data-insp-doc]');
        if (docBtn) docBtn.addEventListener('click', function () { openDocFromTutorial(docBtn.getAttribute('data-insp-doc')); });
        const tutBtn = actionsEl.querySelector('[data-insp-tut]');
        if (tutBtn) tutBtn.addEventListener('click', function () { openTutorialChapter(tutBtn.getAttribute('data-insp-tut')); });
        const fileBtn = actionsEl.querySelector('[data-insp-file]');
        if (fileBtn) fileBtn.addEventListener('click', function () { focusStudioFile(fileBtn.getAttribute('data-insp-file')); });
      }
    }

    cyInstance.on('tap', 'node', function (evt) {
      const node = evt.target;
      cyInstance.elements().removeClass('highlighted');
      node.addClass('highlighted');
      node.connectedEdges().addClass('highlighted');
      node.connectedEdges().connectedNodes().addClass('highlighted');
      if (splitEl && splitEl.classList.contains('is-inspector-collapsed')) {
        setInspectorCollapsed(false);
      }
      updateInspector(node.data());
    });

    // V-Cycle Role Filter Buttons
    if (payload.mode === 'vcycle') {
      const roleBtns = document.querySelectorAll('.tut-role-filters .tut-filter-btn');
      roleBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
          roleBtns.forEach(function (b) { b.classList.remove('active'); });
          btn.classList.add('active');
          const role = btn.getAttribute('data-role');
          cyInstance.elements().removeClass('dimmed highlighted');
          if (role && role !== 'all') {
            cyInstance.nodes().forEach(function (n) {
              if (n.data('role') !== role) n.addClass('dimmed');
              else n.addClass('highlighted');
            });
          }
        });
      });
    }

    // Capstone Progressive Layer Slider + Stepper Node Sync
    if (payload.mode === 'capstone') {
      const slider = document.getElementById('tut-layer-slider');
      const labelEl = document.getElementById('capstone-layer-label');
      const pillsEl = document.getElementById('capstone-layer-pills');
      const resetBtn = document.getElementById('capstone-layer-reset');
      const layersMeta = payload.layers || [];
      const minLayerNum = layersMeta.length ? Math.min.apply(null, layersMeta.map(function (l) { return l.layer; })) : 1;
      const maxLayerNum = layersMeta.length ? Math.max.apply(null, layersMeta.map(function (l) { return l.layer; })) : (payload.chapterNum || 13);

      if (slider) {
        slider.min = String(minLayerNum);
        slider.max = String(maxLayerNum);
      }

      function applyLayer(maxLayer) {
        const mLayer = parseInt(maxLayer, 10) || maxLayerNum;
        if (slider) slider.value = String(mLayer);
        const found = layersMeta.find(function (l) { return l.layer === mLayer; });
        if (labelEl) {
          labelEl.textContent = found ? found.label : `Layer Ch.${String(mLayer).padStart(2, '0')}`;
        }
        cyInstance.elements().removeClass('dimmed');
        cyInstance.nodes().forEach(function (n) {
          if ((n.data('layer') || minLayerNum) > mLayer) n.addClass('dimmed');
        });
        cyInstance.edges().forEach(function (e) {
          if ((e.data('layer') || minLayerNum) > mLayer) e.addClass('dimmed');
        });
        if (pillsEl) {
          pillsEl.querySelectorAll('.capstone-layer-pill').forEach(function (p) {
            const l = parseInt(p.getAttribute('data-layer'), 10);
            p.classList.toggle('active', l === mLayer);
            p.classList.toggle('included', l <= mLayer);
          });
        }
      }

      if (pillsEl && layersMeta.length) {
        pillsEl.innerHTML = layersMeta.map(function (l) {
          return `<button type="button" class="capstone-layer-pill" data-layer="${l.layer}" title="${escapeHtml(l.label)}">Ch.${String(l.layer).padStart(2, '0')}</button>`;
        }).join('');
        pillsEl.querySelectorAll('.capstone-layer-pill').forEach(function (btn) {
          btn.addEventListener('click', function () {
            applyLayer(btn.getAttribute('data-layer'));
          });
        });
      }

      if (slider) {
        slider.addEventListener('input', function () { applyLayer(slider.value); });
      }
      if (resetBtn) {
        resetBtn.addEventListener('click', function () { applyLayer(maxLayerNum); });
      }
      applyLayer(maxLayerNum);

      // Sync Flow Stepper -> Cytoscape active node pulse
      const stepperPayloadEl = document.getElementById('stepper-payload');
      const stepTitleEl = document.getElementById('step-active-title');
      if (stepperPayloadEl && stepTitleEl) {
        let steps = [];
        try { steps = JSON.parse(stepperPayloadEl.getAttribute('data-stepper') || '[]'); } catch (e) { }
        function syncStepperToCy() {
          const curTitle = stepTitleEl.textContent.trim();
          const st = steps.find(function (s) { return s.title === curTitle; });
          cyInstance.nodes().removeClass('stepper-active');
          if (st && st.cyNode) {
            const targetNode = cyInstance.getElementById(st.cyNode);
            if (targetNode && targetNode.length) {
              targetNode.addClass('stepper-active');
            }
          }
        }
        const obs = new MutationObserver(syncStepperToCy);
        obs.observe(stepTitleEl, { childList: true, characterData: true, subtree: true });
        syncStepperToCy();
      }
    }
  }

  // =========================================================================
  // 5. Incremental Diff Viewer (diff2html) & Tab Badges
  // =========================================================================

  function initDiffAndCodeBadges() {
    const metaEl = document.getElementById('tut-diff-meta-payload');
    if (metaEl) {
      let meta = {};
      try { meta = JSON.parse(metaEl.getAttribute('data-tut-diff-meta') || '{}'); } catch (e) { }
      document.querySelectorAll('.studio-tab').forEach(function (tab) {
        const fname = tab.getAttribute('title') || '';
        const info = meta[fname];
        if (!info) return;
        if (info.status === 'new' || info.status === 'mod') {
          const badge = document.createElement('span');
          badge.className = 'tut-tab-badge tut-tab-' + info.status;
          badge.textContent = info.status === 'new' ? 'NEW' : 'MOD';
          tab.appendChild(badge);
        }
        if (Array.isArray(info.added_lines) && info.added_lines.length) {
          const pane = document.querySelector(`.file-code-pane[data-filename="${CSS.escape(fname)}"]`);
          if (pane) {
            const rows = pane.querySelectorAll('.sv-code-table tr');
            info.added_lines.forEach(function (ln) {
              if (rows[ln - 1]) rows[ln - 1].classList.add('tut-line-added');
            });
          }
        }
      });
    }

    const diffPayloadEl = document.getElementById('tut-diff-payload');
    const diffContainer = document.getElementById('tut-diff-container');
    const toggleBtn = document.getElementById('tut-toggle-diff-panel');
    if (!diffPayloadEl || !diffContainer) return;

    let diffText = '';
    try {
      const parsed = JSON.parse(diffPayloadEl.getAttribute('data-tut-diff') || '{}');
      diffText = parsed.diff || '';
    } catch (e) { }

    let currentFormat = 'line-by-line';
    function bindInteractiveFileList() {
      const wrappers = Array.from(diffContainer.querySelectorAll('.d2h-file-wrapper'));
      const listItems = Array.from(diffContainer.querySelectorAll('.d2h-file-list li'));
      const titleEl = diffContainer.querySelector('.d2h-file-list-title');
      if (titleEl && !titleEl.dataset.hintAdded) {
        titleEl.dataset.hintAdded = '1';
        titleEl.innerHTML += ' <span class="tut-diff-hint">(Click a file to inspect diff)</span>';
      }
      const toggleShowLink = diffContainer.querySelector('.d2h-file-list-wrapper .d2h-show, .d2h-file-list-wrapper .d2h-hide');
      if (toggleShowLink) {
        toggleShowLink.style.display = 'none';
      }

      function setWrapperOpen(wrapper, li, open) {
        if (!wrapper) return;
        wrapper.classList.toggle('is-diff-open', open);
        if (li) li.classList.toggle('is-diff-active', open);
      }

      listItems.forEach(function (li, idx) {
        const link = li.querySelector('a[href^="#"]');
        const href = link ? link.getAttribute('href') : '';
        const targetId = href && href.startsWith('#') ? href.slice(1) : '';
        const wrapper = (targetId && document.getElementById(targetId)) || wrappers[idx];
        if (!wrapper) return;

        // Embed the diff wrapper directly inside its corresponding file list item
        wrapper.addEventListener('click', function (e) {
          e.stopPropagation();
        });
        li.appendChild(wrapper);

        li.style.cursor = 'pointer';
        li.addEventListener('click', function (e) {
          if (e.target.closest('.d2h-file-wrapper')) return;
          e.preventDefault();
          const nextOpen = !wrapper.classList.contains('is-diff-open');
          setWrapperOpen(wrapper, li, nextOpen);
          if (nextOpen) {
            li.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        });
      });
    }

    function renderDiff() {
      if (!diffText) return;
      if (typeof global.Diff2HtmlUI === 'function') {
        const ui = new global.Diff2HtmlUI(diffContainer, diffText, {
          drawFileList: true,
          fileListToggle: false,
          fileListStartVisible: true,
          matching: 'lines',
          outputFormat: currentFormat,
          colorScheme: getTheme()
        });
        ui.draw();
        bindInteractiveFileList();
      } else {
        diffContainer.innerHTML = `<pre class="tut-diff-fallback">${escapeHtml(diffText)}</pre>`;
      }
    }

    // Render collapsed file list immediately so modified files are listed without diffs shown
    if (diffText) {
      diffContainer.style.display = 'block';
      renderDiff();
      diffContainer.dataset.rendered = '1';
    }

    if (toggleBtn) {
      toggleBtn.addEventListener('click', function () {
        const isHidden = diffContainer.style.display === 'none';
        diffContainer.style.display = isHidden ? 'block' : 'none';
        if (isHidden && !diffContainer.dataset.rendered) {
          renderDiff();
          diffContainer.dataset.rendered = '1';
        }
      });
    }

    document.querySelectorAll('[data-diff-format]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.querySelectorAll('[data-diff-format]').forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        currentFormat = btn.getAttribute('data-diff-format');
        diffContainer.style.display = 'block';
        renderDiff();
        diffContainer.dataset.rendered = '1';
      });
    });
  }

  // =========================================================================
  // 6. Self-Check Knowledge Quiz
  // =========================================================================

  function initQuiz() {
    const container = document.getElementById('tut-quiz-container');
    const payloadEl = document.getElementById('tut-quiz-payload');
    if (!container || !payloadEl) return;

    let questions = [];
    try { questions = JSON.parse(payloadEl.getAttribute('data-tut-quiz') || '[]'); } catch (e) { }
    if (!questions.length) return;

    const slug = container.getAttribute('data-chapter-slug') || 'unknown';
    container.innerHTML = questions.map(function (q, qIdx) {
      const optsHtml = (q.options || []).map(function (opt, oIdx) {
        return `<button type="button" class="tut-quiz-opt" data-q="${qIdx}" data-o="${oIdx}">
          <span class="tut-quiz-letter">${String.fromCharCode(65 + oIdx)}</span>
          <span>${escapeHtml(opt)}</span>
        </button>`;
      }).join('');
      return `<div class="tut-quiz-card" data-q-card="${qIdx}">
        <div class="tut-quiz-q">Q${qIdx + 1}. ${escapeHtml(q.q)}</div>
        <div class="tut-quiz-options">${optsHtml}</div>
        <div class="tut-quiz-feedback" id="tut-qfb-${qIdx}" style="display:none;"></div>
      </div>`;
    }).join('');

    const answered = {};
    container.querySelectorAll('.tut-quiz-opt').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const qIdx = parseInt(btn.getAttribute('data-q'), 10);
        const oIdx = parseInt(btn.getAttribute('data-o'), 10);
        const q = questions[qIdx];
        if (!q) return;

        const card = container.querySelector(`[data-q-card="${qIdx}"]`);
        card.querySelectorAll('.tut-quiz-opt').forEach(function (b, idx) {
          b.classList.remove('is-correct', 'is-wrong', 'is-picked');
          if (idx === q.answer) b.classList.add('is-correct');
          if (idx === oIdx) b.classList.add('is-picked');
          if (idx === oIdx && oIdx !== q.answer) b.classList.add('is-wrong');
        });

        const fbEl = document.getElementById(`tut-qfb-${qIdx}`);
        const isCorrect = oIdx === q.answer;
        answered[qIdx] = isCorrect;
        if (fbEl) {
          fbEl.style.display = 'block';
          fbEl.className = 'tut-quiz-feedback ' + (isCorrect ? 'is-ok' : 'is-err');
          fbEl.innerHTML = `<strong>${isCorrect ? 'Correct!' : 'Not quite.'}</strong> ${escapeHtml(q.explanation || '')}`;
        }

        const prog = readProgress();
        const correctCount = Object.values(answered).filter(Boolean).length;
        prog.quizScores[slug] = { score: correctCount, total: questions.length };
        writeProgress(prog);
      });
    });
  }

  // =========================================================================
  // Bootstrap & Theme Sync
  // =========================================================================

  function initAll() {
    initCompletionControls();
    initScmMatrix();
    initCytoscapeGraph();
    initDiffAndCodeBadges();
    initQuiz();
    renderMermaidAll();
  }

  window.addEventListener('message', function (e) {
    if (!e.data || typeof e.data !== 'object') return;
    if (e.data.theme) {
      setTimeout(function () {
        renderMermaidAll();
        if (cyInstance) {
          cyInstance.style(buildCytoscapeStyles(getTheme() === 'dark'));
        }
      }, 20);
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  global.TutorialPage = {
    initAll: initAll,
    focusStudioFile: focusStudioFile
  };
})(window);
