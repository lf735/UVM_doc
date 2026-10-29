/**
 * UVM 1.2 Interactive Documentation & Source Explorer
 * Application Logic, SPA Router, Search Engine & Split-View Controller
 * Licensed under Apache License 2.0
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const appContainer = document.getElementById('app-container');
  const docFrame = document.getElementById('doc-frame');
  const srcFrame = document.getElementById('src-frame');
  const docPane = document.getElementById('doc-pane');
  const srcPane = document.getElementById('src-pane');
  const docPaneTitle = document.getElementById('doc-pane-title');
  const srcPaneTitle = document.getElementById('src-pane-title');
  const themeToggle = document.getElementById('theme-toggle');
  const menuToggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  const sidebarContent = document.getElementById('sidebar-content');
  const sidebarFilter = document.getElementById('sidebar-filter');
  const splitDivider = document.getElementById('split-divider');

  // Search Modal Elements
  const searchModal = document.getElementById('search-modal');
  const searchTrigger = document.getElementById('search-trigger');
  const searchInput = document.getElementById('modal-search-input');
  const searchResults = document.getElementById('modal-search-results');
  const searchFilterPills = document.querySelectorAll('.filter-pill');

  // State
  let currentMode = 'docs'; // 'docs' | 'source' | 'split'
  let currentDocUrl = 'docs_view/overviews/intro-txt.html';
  let currentSrcUrl = 'src_view/comps/uvm_driver.svh.html#L44';
  let activeSidebarTab = 'docs'; // 'docs' | 'source' | 'index'
  let searchFilterType = 'all';
  let searchSelectedIndex = -1;
  let filteredSearchResults = [];

  // =========================================================================
  // URL Normalization Helpers
  // =========================================================================

  function normalizeDocUrl(url) {
    if (!url) return 'docs_view/overviews/intro-txt.html';
    let clean = url.replace(/^[./]+/, '');
    if (clean.includes('docs_view/')) {
      clean = clean.substring(clean.indexOf('docs_view/'));
    } else {
      clean = 'docs_view/' + clean;
    }
    return clean;
  }

  function normalizeSrcUrl(url) {
    if (!url) return 'src_view/comps/uvm_driver.svh.html#L44';
    let clean = url.replace(/^[./]+/, '');
    if (clean.includes('src_view/')) {
      clean = clean.substring(clean.indexOf('src_view/'));
    } else {
      clean = 'src_view/' + clean;
    }
    return clean;
  }

  function setFrameSrc(frame, relUrl) {
    if (!frame || !relUrl) return;
    try {
      const targetUrl = new URL(relUrl, window.location.href);
      const currentUrl = new URL(frame.src, window.location.href);
      if (currentUrl.pathname === targetUrl.pathname && currentUrl.hash === targetUrl.hash) {
        return;
      }
      if (currentUrl.pathname === targetUrl.pathname && targetUrl.hash) {
        if (frame.contentWindow) {
          frame.contentWindow.location.hash = targetUrl.hash;
          return;
        }
      }
    } catch (e) { }
    frame.src = relUrl;
  }

  // =========================================================================
  // Theme Management
  // =========================================================================

  const storedTheme = localStorage.getItem('theme') ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

  setTheme(storedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme') || 'light';
      const next = cur === 'dark' ? 'light' : 'dark';
      setTheme(next);
    });
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeIcon(theme);
    // Broadcast to iframes
    if (docFrame && docFrame.contentWindow) {
      docFrame.contentWindow.postMessage({ theme }, '*');
    }
    if (srcFrame && srcFrame.contentWindow) {
      srcFrame.contentWindow.postMessage({ theme }, '*');
    }
  }

  function updateThemeIcon(theme) {
    if (!themeToggle) return;
    themeToggle.innerHTML = theme === 'dark'
      ? `<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>`
      : `<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>`;
  }

  // =========================================================================
  // View Modes (Docs / Source / Split)
  // =========================================================================

  const viewBtns = document.querySelectorAll('.view-btn');
  viewBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.getAttribute('data-mode');
      if (mode === 'split') {
        if (currentMode === 'docs') {
          // Auto pair with corresponding source code if available
          const docClean = currentDocUrl.replace(/^docs_view\//, '');
          if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docToSrc && UVM_DATA.docToSrc[docClean]) {
            const pairedSrc = UVM_DATA.docToSrc[docClean];
            currentSrcUrl = pairedSrc;
            setFrameSrc(srcFrame, pairedSrc);
            updateSrcTitle(pairedSrc);
          }
        } else if (currentMode === 'source') {
          // Auto pair with corresponding doc if available
          const srcClean = currentSrcUrl.replace(/^src_view\//, '').split('#')[0];
          if (typeof UVM_DATA !== 'undefined' && UVM_DATA.srcToDoc && UVM_DATA.srcToDoc[srcClean]) {
            const pairedDoc = UVM_DATA.srcToDoc[srcClean];
            currentDocUrl = pairedDoc;
            setFrameSrc(docFrame, pairedDoc);
            updateDocTitle(pairedDoc);
          }
        }
      }
      setViewMode(mode, true);
    });
  });

  function setViewMode(mode, updateHistory = true) {
    currentMode = mode;
    appContainer.classList.remove('mode-docs', 'mode-source', 'mode-split');
    appContainer.classList.add(`mode-${mode}`);

    viewBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
    });

    if (mode !== 'split') {
      if (docPane) { docPane.style.width = ''; docPane.style.flex = ''; }
      if (srcPane) { srcPane.style.width = ''; srcPane.style.flex = ''; }
    }

    if (updateHistory) {
      updateHash();
    }
  }

  // Global handler for when a doc page requests to view source code
  window.openSourceView = function (srcUrl) {
    const fullSrc = normalizeSrcUrl(srcUrl);
    currentSrcUrl = fullSrc;
    setFrameSrc(srcFrame, fullSrc);
    updateSrcTitle(fullSrc);

    // Switch to split view so user sees both doc and source!
    if (currentMode !== 'split') {
      setViewMode('split', true);
    } else {
      updateHash();
    }
  };

  // Global handler for when a source page requests to view documentation
  window.openDocView = function (docUrl) {
    const fullDoc = normalizeDocUrl(docUrl);
    currentDocUrl = fullDoc;
    setFrameSrc(docFrame, fullDoc);
    updateDocTitle(fullDoc);

    // Switch to split view so user sees both doc and source!
    if (currentMode !== 'split') {
      setViewMode('split', true);
    } else {
      updateHash();
    }
  };

  // Cross-frame messaging listener (supports file:// and http/https)
  window.addEventListener('message', (e) => {
    if (!e.data || typeof e.data !== 'object') return;
    if (e.data.type === 'openSourceView' && e.data.url) {
      window.openSourceView(e.data.url);
    } else if (e.data.type === 'openDocView' && e.data.url) {
      window.openDocView(e.data.url);
    } else if (e.data.type === 'docNavigated' && e.data.url) {
      const fullDoc = normalizeDocUrl(e.data.url);
      currentDocUrl = fullDoc;
      updateDocTitle(fullDoc);
      highlightActiveSidebar(fullDoc);
      updateHash();
    } else if (e.data.type === 'srcNavigated' && e.data.url) {
      const fullSrc = normalizeSrcUrl(e.data.url);
      currentSrcUrl = fullSrc;
      updateSrcTitle(fullSrc);
      highlightActiveSidebar(fullSrc);
      updateHash();
    }
  });

  // =========================================================================
  // Hash Routing
  // =========================================================================

  function parseHash() {
    const hash = window.location.hash || '';
    if (!hash) {
      // Default initial view
      loadDoc(currentDocUrl, false);
      return;
    }

    if (hash.startsWith('#/split')) {
      const query = hash.split('?')[1] || '';
      const params = new URLSearchParams(query);
      const rawDoc = params.get('doc');
      const rawSrc = params.get('src');

      const fullDoc = rawDoc ? normalizeDocUrl(rawDoc) : currentDocUrl;
      const fullSrc = rawSrc ? normalizeSrcUrl(rawSrc) : currentSrcUrl;

      currentDocUrl = fullDoc;
      currentSrcUrl = fullSrc;

      setViewMode('split', false);

      setFrameSrc(docFrame, fullDoc);
      setFrameSrc(srcFrame, fullSrc);

      updateDocTitle(fullDoc);
      updateSrcTitle(fullSrc);
      highlightActiveSidebar(fullDoc);
    } else if (hash.startsWith('#/src/')) {
      const srcPath = normalizeSrcUrl(hash.substring(6));
      currentSrcUrl = srcPath;
      setViewMode('source', false);
      setFrameSrc(srcFrame, srcPath);
      updateSrcTitle(srcPath);
      highlightActiveSidebar(srcPath);
    } else if (hash.startsWith('#/doc/')) {
      const docPath = normalizeDocUrl(hash.substring(6));
      currentDocUrl = docPath;
      setViewMode('docs', false);
      setFrameSrc(docFrame, docPath);
      updateDocTitle(docPath);
      highlightActiveSidebar(docPath);
    } else {
      loadDoc(currentDocUrl, false);
    }
  }

  function updateHash() {
    if (currentMode === 'split') {
      const doc = currentDocUrl.replace(/^docs_view\//, '');
      const src = currentSrcUrl.replace(/^src_view\//, '');
      window.location.hash = `#/split?doc=${encodeURIComponent(doc)}&src=${encodeURIComponent(src)}`;
    } else if (currentMode === 'source') {
      const src = currentSrcUrl.replace(/^src_view\//, '');
      window.location.hash = `#/src/${src}`;
    } else {
      const doc = currentDocUrl.replace(/^docs_view\//, '');
      window.location.hash = `#/doc/${doc}`;
    }
  }

  window.addEventListener('hashchange', parseHash);

  function loadDoc(url, pushState = true) {
    const fullDoc = normalizeDocUrl(url);
    currentDocUrl = fullDoc;
    setFrameSrc(docFrame, fullDoc);
    updateDocTitle(fullDoc);

    if (currentMode === 'split') {
      // In split mode, check if we should pair with its source file
      const docClean = fullDoc.replace(/^docs_view\//, '');
      if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docToSrc && UVM_DATA.docToSrc[docClean]) {
        const pairedSrc = UVM_DATA.docToSrc[docClean];
        currentSrcUrl = pairedSrc;
        setFrameSrc(srcFrame, pairedSrc);
        updateSrcTitle(pairedSrc);
      }
      updateHash();
    } else if (currentMode === 'source') {
      setViewMode('docs', true);
    } else {
      updateHash();
    }
    highlightActiveSidebar(fullDoc);
  }

  function loadSource(url, pushState = true) {
    const fullSrc = normalizeSrcUrl(url);
    currentSrcUrl = fullSrc;
    setFrameSrc(srcFrame, fullSrc);
    updateSrcTitle(fullSrc);

    if (currentMode === 'split') {
      // In split mode, check if we should pair with its doc file
      const srcClean = fullSrc.replace(/^src_view\//, '').split('#')[0];
      if (typeof UVM_DATA !== 'undefined' && UVM_DATA.srcToDoc && UVM_DATA.srcToDoc[srcClean]) {
        const pairedDoc = UVM_DATA.srcToDoc[srcClean];
        currentDocUrl = pairedDoc;
        setFrameSrc(docFrame, pairedDoc);
        updateDocTitle(pairedDoc);
      }
      updateHash();
    } else if (currentMode === 'docs') {
      setViewMode('source', true);
    } else {
      updateHash();
    }
    highlightActiveSidebar(fullSrc);
  }

  function updateDocTitle(url) {
    if (!docPaneTitle) return;
    const clean = url.replace('docs_view/', '').replace('.html', '');
    docPaneTitle.textContent = clean;
  }

  function updateSrcTitle(url) {
    if (!srcPaneTitle) return;
    const clean = url.replace('src_view/', '').replace('.html', '');
    srcPaneTitle.textContent = clean;
  }

  // =========================================================================
  // Sidebar Tabs & Navigation Rendering
  // =========================================================================

  const tabBtns = document.querySelectorAll('.sidebar-tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeSidebarTab = btn.getAttribute('data-tab');
      renderSidebar();
    });
  });

  if (sidebarFilter) {
    sidebarFilter.addEventListener('input', () => {
      renderSidebar();
    });
  }

  function renderSidebar() {
    if (!sidebarContent || typeof UVM_DATA === 'undefined') return;
    const query = (sidebarFilter ? sidebarFilter.value : '').toLowerCase().trim();

    if (activeSidebarTab === 'docs') {
      renderDocsMenu(query);
    } else if (activeSidebarTab === 'source') {
      renderSourceTree(query);
    } else if (activeSidebarTab === 'index') {
      renderAlphabeticalIndex(query);
    }
  }

  function renderDocsMenu(query) {
    const categories = UVM_DATA.categories || [];
    let html = '';

    categories.forEach(cat => {
      if (cat.type === 'file' || cat.type === 'index') {
        const matches = !query || cat.title.toLowerCase().includes(query);
        if (matches) {
          const isActive = currentDocUrl.includes(cat.href);
          html += `<div class="nav-single-item">
            <a href="#" data-doc-href="${cat.href}" class="nav-item-link ${isActive ? 'active' : ''}">
              ${cat.title}
            </a>
          </div>`;
        }
      } else if (cat.type === 'group') {
        const subItems = filterGroupItems(cat.children || [], query);
        if (subItems.length > 0 || cat.title.toLowerCase().includes(query)) {
          html += `<div class="nav-group">
            <div class="nav-group-header">
              <span>${cat.title}</span>
              <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            <ul class="nav-group-items">
              ${renderGroupItemsHtml(subItems)}
            </ul>
          </div>`;
        }
      }
    });

    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching topics</div>';
    attachSidebarListeners();
  }

  function filterGroupItems(items, query) {
    if (!query) return items;
    const res = [];
    items.forEach(item => {
      if (item.type === 'file' || item.type === 'index') {
        if (item.title.toLowerCase().includes(query)) {
          res.push(item);
        }
      } else if (item.type === 'group') {
        const subs = filterGroupItems(item.children || [], query);
        if (subs.length > 0 || item.title.toLowerCase().includes(query)) {
          res.push({ ...item, children: subs });
        }
      }
    });
    return res;
  }

  function renderGroupItemsHtml(items) {
    let out = '';
    items.forEach(item => {
      if (item.type === 'file' || item.type === 'index') {
        const isActive = currentDocUrl.includes(item.href);
        out += `<li>
          <a href="#" data-doc-href="${item.href}" class="nav-item-link ${isActive ? 'active' : ''}">
            ${item.title}
          </a>
        </li>`;
      } else if (item.type === 'group') {
        out += `<div class="nav-group" style="margin-left: 0.5rem">
          <div class="nav-group-header" style="font-size:0.775rem;">
            <span>${item.title}</span>
            <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
          <ul class="nav-group-items">
            ${renderGroupItemsHtml(item.children || [])}
          </ul>
        </div>`;
      }
    });
    return out;
  }

  function renderSourceTree(query) {
    const root = UVM_DATA.sourceTree || {};
    let html = '';

    function renderNode(node, depth) {
      if (node.type === 'file') {
        if (!query || node.name.toLowerCase().includes(query) || node.path.toLowerCase().includes(query)) {
          const isActive = currentSrcUrl.includes(node.url);
          html += `<div class="file-tree-item ${isActive ? 'active' : ''}" data-src-href="${node.url}" style="padding-left: ${depth * 14 + 10}px">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span>${node.name}</span>
          </div>`;
        }
      } else if (node.type === 'dir') {
        const hasMatchingChild = hasMatch(node, query);
        if (hasMatchingChild) {
          html += `<div class="nav-group">
            <div class="nav-group-header" style="padding-left: ${depth * 14 + 10}px">
              <span style="font-family:var(--font-mono)">📁 ${node.name}</span>
              <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            <div class="nav-group-items" style="padding:0">
              ${(node.children || []).map(child => renderNode(child, depth + 1)).join('')}
            </div>
          </div>`;
        }
      }
      return '';
    }

    function hasMatch(node, q) {
      if (!q) return true;
      if (node.name.toLowerCase().includes(q)) return true;
      if (node.children) {
        return node.children.some(c => hasMatch(c, q));
      }
      return false;
    }

    (root.children || []).forEach(child => renderNode(child, 0));
    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching files</div>';
    attachSidebarListeners();
  }

  function renderAlphabeticalIndex(query) {
    const items = UVM_DATA.searchIndex || [];
    const classesAndMacros = items.filter(x => x.type === 'class' || x.type === 'macro');
    let html = '';

    classesAndMacros
      .filter(x => !query || x.name.toLowerCase().includes(query))
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach(item => {
        const badgeClass = item.type === 'class' ? 'badge-class' : 'badge-macro';
        html += `<div class="nav-single-item" style="padding: 0.2rem 0.5rem">
          <a href="#" data-doc-href="${item.doc || ''}" data-src-href="${item.src || ''}" class="nav-item-link" style="justify-content:space-between">
            <span style="font-family:var(--font-mono)">${item.name}</span>
            <span class="res-badge ${badgeClass}">${item.type}</span>
          </a>
        </div>`;
      });

    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching symbols</div>';
    attachSidebarListeners();
  }

  function attachSidebarListeners() {
    // Collapsible group headers
    sidebarContent.querySelectorAll('.nav-group-header').forEach(header => {
      header.addEventListener('click', () => {
        header.closest('.nav-group').classList.toggle('collapsed');
      });
    });

    // Doc links
    sidebarContent.querySelectorAll('[data-doc-href]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const docHref = link.getAttribute('data-doc-href');
        const srcHref = link.getAttribute('data-src-href');
        if (docHref) {
          loadDoc(docHref);
        } else if (srcHref) {
          loadSource(srcHref);
        }
        if (window.innerWidth <= 860 && sidebar) {
          sidebar.classList.remove('open');
        }
      });
    });

    // Source links
    sidebarContent.querySelectorAll('[data-src-href]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const srcHref = link.getAttribute('data-src-href');
        if (srcHref) {
          loadSource(srcHref);
        }
        if (window.innerWidth <= 860 && sidebar) {
          sidebar.classList.remove('open');
        }
      });
    });
  }

  function highlightActiveSidebar(url) {
    sidebarContent.querySelectorAll('.nav-item-link, .file-tree-item').forEach(el => {
      el.classList.remove('active');
      const docHref = el.getAttribute('data-doc-href');
      const srcHref = el.getAttribute('data-src-href');
      if ((docHref && url.includes(docHref)) || (srcHref && url.includes(srcHref))) {
        el.classList.add('active');
      }
    });
  }

  // =========================================================================
  // Resizable Split View Divider
  // =========================================================================

  if (splitDivider) {
    let isDragging = false;
    const viewport = document.getElementById('app-viewport');

    splitDivider.addEventListener('mousedown', (e) => {
      isDragging = true;
      splitDivider.classList.add('active');
      document.body.classList.add('is-resizing');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging || !viewport || !docPane || !srcPane) return;
      const rect = viewport.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const totalWidth = rect.width;
      const pct = Math.max(15, Math.min(85, (x / totalWidth) * 100));
      docPane.style.flex = `0 0 ${pct}%`;
      docPane.style.width = `${pct}%`;
      srcPane.style.flex = `0 0 calc(${100 - pct}% - 6px)`;
      srcPane.style.width = `calc(${100 - pct}% - 6px)`;
    });

    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        splitDivider.classList.remove('active');
        document.body.classList.remove('is-resizing');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    });

    // Double-click to reset 50/50
    splitDivider.addEventListener('dblclick', () => {
      if (docPane) { docPane.style.width = ''; docPane.style.flex = ''; }
      if (srcPane) { srcPane.style.width = ''; srcPane.style.flex = ''; }
    });
  }

  // Pane actions: Open Full View & Copy Link
  const openFullDoc = document.getElementById('open-full-doc');
  if (openFullDoc) {
    openFullDoc.addEventListener('click', () => setViewMode('docs', true));
  }
  const openFullSrc = document.getElementById('open-full-src');
  if (openFullSrc) {
    openFullSrc.addEventListener('click', () => setViewMode('source', true));
  }

  // =========================================================================
  // Instant Search Engine & Modal
  // =========================================================================

  function openSearchModal() {
    if (!searchModal) return;
    searchModal.classList.add('open');
    searchInput.value = '';
    searchInput.focus();
    searchSelectedIndex = -1;
    executeSearch('');
  }

  function closeSearchModal() {
    if (!searchModal) return;
    searchModal.classList.remove('open');
  }

  if (searchTrigger) {
    searchTrigger.addEventListener('click', openSearchModal);
  }

  window.addEventListener('keydown', (e) => {
    // Open on '/' or 'Ctrl+K' / 'Cmd+K'
    if ((e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') ||
      (e.key === 'k' && (e.ctrlKey || e.metaKey))) {
      e.preventDefault();
      openSearchModal();
    } else if (e.key === 'Escape' && searchModal && searchModal.classList.contains('open')) {
      closeSearchModal();
    }
  });

  if (searchModal) {
    searchModal.addEventListener('click', (e) => {
      if (e.target === searchModal) {
        closeSearchModal();
      }
    });
  }

  searchFilterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      searchFilterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      searchFilterType = pill.getAttribute('data-type');
      executeSearch(searchInput ? searchInput.value : '');
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      executeSearch(e.target.value);
    });

    searchInput.addEventListener('keydown', (e) => {
      const items = searchResults.querySelectorAll('.search-result-item');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        searchSelectedIndex = (searchSelectedIndex + 1) % items.length;
        updateSelectedSearchItem(items);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        searchSelectedIndex = (searchSelectedIndex - 1 + items.length) % items.length;
        updateSelectedSearchItem(items);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (searchSelectedIndex >= 0 && searchSelectedIndex < filteredSearchResults.length) {
          selectSearchResult(filteredSearchResults[searchSelectedIndex]);
        }
      }
    });
  }

  function updateSelectedSearchItem(items) {
    items.forEach((item, idx) => {
      item.classList.toggle('selected', idx === searchSelectedIndex);
      if (idx === searchSelectedIndex) {
        item.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  function executeSearch(query) {
    if (!searchResults || typeof UVM_DATA === 'undefined') return;
    const items = UVM_DATA.searchIndex || [];
    const q = query.toLowerCase().trim();

    filteredSearchResults = items.filter(item => {
      if (searchFilterType !== 'all' && item.type !== searchFilterType) {
        return false;
      }
      if (!q) return true;
      return item.name.toLowerCase().includes(q) ||
        (item.desc && item.desc.toLowerCase().includes(q)) ||
        (item.category && item.category.toLowerCase().includes(q));
    }).slice(0, 50); // limit to top 50 matches for performance

    searchSelectedIndex = filteredSearchResults.length > 0 ? 0 : -1;

    let html = '';
    filteredSearchResults.forEach((item, idx) => {
      const badgeClass = item.type === 'class' ? 'badge-class' : (item.type === 'macro' ? 'badge-macro' : 'badge-file');
      html += `<li class="search-result-item ${idx === 0 ? 'selected' : ''}" data-index="${idx}">
        <div class="res-main">
          <span class="res-name">${highlightMatch(item.name, q)}</span>
          <span class="res-desc">${item.desc || ''}</span>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem">
          <span class="res-badge ${badgeClass}">${item.type}</span>
          ${item.src ? '<span style="color:var(--text-muted); font-size:0.75rem;">Source ↗</span>' : ''}
        </div>
      </li>`;
    });

    searchResults.innerHTML = html || '<li style="padding:2rem; text-align:center; color:var(--text-muted); font-size:0.875rem">No matching items found</li>';

    searchResults.querySelectorAll('.search-result-item').forEach(item => {
      item.addEventListener('click', () => {
        const idx = parseInt(item.getAttribute('data-index'), 10);
        selectSearchResult(filteredSearchResults[idx]);
      });
    });
  }

  function highlightMatch(text, query) {
    if (!query) return text;
    const idx = text.toLowerCase().indexOf(query);
    if (idx === -1) return text;
    return text.substring(0, idx) +
      `<strong style="color:var(--primary); text-decoration:underline">${text.substring(idx, idx + query.length)}</strong>` +
      text.substring(idx + query.length);
  }

  function selectSearchResult(item) {
    if (!item) return;
    closeSearchModal();

    if (currentMode === 'split') {
      if (item.doc) {
        currentDocUrl = normalizeDocUrl(item.doc);
        setFrameSrc(docFrame, currentDocUrl);
        updateDocTitle(currentDocUrl);
      }
      if (item.src) {
        currentSrcUrl = normalizeSrcUrl(item.src);
        setFrameSrc(srcFrame, currentSrcUrl);
        updateSrcTitle(currentSrcUrl);
      } else if (item.doc) {
        const docClean = currentDocUrl.replace(/^docs_view\//, '');
        if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docToSrc && UVM_DATA.docToSrc[docClean]) {
          currentSrcUrl = UVM_DATA.docToSrc[docClean];
          setFrameSrc(srcFrame, currentSrcUrl);
          updateSrcTitle(currentSrcUrl);
        }
      }
      updateHash();
      highlightActiveSidebar(item.doc || item.src);
    } else {
      if (item.doc) {
        loadDoc(item.doc);
        if (item.src) {
          currentSrcUrl = normalizeSrcUrl(item.src);
          setFrameSrc(srcFrame, currentSrcUrl);
          updateSrcTitle(currentSrcUrl);
        }
      } else if (item.src) {
        loadSource(item.src);
      }
    }
  }

  // =========================================================================
  // Mobile Drawer Toggle
  // =========================================================================

  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }

  // Initialize
  renderSidebar();
  parseHash();
});

