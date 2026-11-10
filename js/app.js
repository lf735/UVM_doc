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
  const sidebarFilterClear = document.getElementById('sidebar-filter-clear');
  const sidebarFilterRegex = document.getElementById('sidebar-filter-regex');
  const sidebarPillsContainer = document.getElementById('sidebar-filter-pills');
  let sidebarPills = document.querySelectorAll('.sidebar-pill');
  const sidebarToggleAll = document.getElementById('sidebar-toggle-all');
  const splitDivider = document.getElementById('split-divider');

  // Search Modal Elements
  const searchModal = document.getElementById('search-modal');
  const searchTrigger = document.getElementById('search-trigger');
  const searchInput = document.getElementById('modal-search-input');
  const searchResults = document.getElementById('modal-search-results');
  const searchFilterPills = document.querySelectorAll('.filter-pill');
  const modalSearchClear = document.getElementById('modal-search-clear');
  const modalSearchCase = document.getElementById('modal-search-case');
  const modalSearchRegex = document.getElementById('modal-search-regex');
  const modalSearchAi = document.getElementById('modal-search-ai');
  const modalSearchSettings = document.getElementById('modal-search-settings');
  const modalSearchHeader = document.querySelector('.modal-search-header');

  const modalAiLoading = document.getElementById('modal-ai-loading');
  const aiLoadingText = document.getElementById('ai-loading-text');
  const aiLoadingPct = document.getElementById('ai-loading-pct');
  const aiLoadingBarFill = document.getElementById('ai-loading-bar-fill');
  const modalSearchPrompts = document.getElementById('modal-search-prompts');
  const promptsChips = document.getElementById('prompts-chips');

  const aiConsentModal = document.getElementById('ai-consent-modal');
  const aiConsentClose = document.getElementById('ai-consent-close');
  const aiConsentCancel = document.getElementById('ai-consent-cancel');
  const aiConsentConfirm = document.getElementById('ai-consent-confirm');
  const aiConsentModelList = document.getElementById('ai-consent-model-list');

  const searchSettingsModal = document.getElementById('search-settings-modal');
  const searchSettingsClose = document.getElementById('search-settings-close');
  const searchSettingsDone = document.getElementById('search-settings-done');
  const settingsModelList = document.getElementById('settings-model-list');
  const settingsToggleHybrid = document.getElementById('settings-toggle-hybrid');
  const settingsToggleAutoSemantic = document.getElementById('settings-toggle-auto-semantic');
  const settingsModeConsolidated = document.getElementById('settings-mode-consolidated');
  const settingsModeMixed = document.getElementById('settings-mode-mixed');
  const settingsCacheStatus = document.getElementById('settings-cache-status');
  const settingsClearCache = document.getElementById('settings-clear-cache');

  // Search History & Navigation Elements (Search Pilot)
  const modalRecentSearches = document.getElementById('modal-recent-searches');
  const recentSearchesChips = document.getElementById('recent-searches-chips');
  const recentSearchesClear = document.getElementById('recent-searches-clear');

  const searchNavBar = document.getElementById('search-nav-bar');
  const searchNavReopenBtn = document.getElementById('search-nav-reopen-btn');
  const searchNavQuery = document.getElementById('search-nav-query');
  const searchNavBadge = document.getElementById('search-nav-badge');
  const searchNavPrev = document.getElementById('search-nav-prev');
  const searchNavNext = document.getElementById('search-nav-next');
  const searchNavList = document.getElementById('search-nav-list');
  const searchNavClose = document.getElementById('search-nav-close');

  // Image Zoom Modal Elements
  const imageZoomModal = document.getElementById('image-zoom-modal');
  const imageModalTitle = document.getElementById('image-modal-title');
  const imageModalImg = document.getElementById('image-modal-img');
  const imageModalViewport = document.getElementById('image-modal-viewport');
  const imageModalStage = document.getElementById('image-modal-stage');
  const imageZoomLevel = document.getElementById('image-zoom-level');
  const imageZoomInBtn = document.getElementById('image-zoom-in');
  const imageZoomOutBtn = document.getElementById('image-zoom-out');
  const imageZoomFitBtn = document.getElementById('image-zoom-fit');
  const imageZoomActualBtn = document.getElementById('image-zoom-actual');
  const imageModalCloseBtn = document.getElementById('image-modal-close');

  // State
  let currentMode = 'docs'; // 'docs' | 'source' | 'split'
  let currentDocUrl = 'docs_view/overviews/intro-txt.html';
  let currentSrcUrl = 'src_view/comps/uvm_driver.svh.html#L44';
  let activeSidebarTab = 'docs'; // 'docs' | 'source' | 'index'
  let searchFilterTypes = new Set(['all']);
  let sidebarFilterTypes = new Set(['all']);
  let modalRegexEnabled = false;
  let modalCaseSensitive = false;
  let sidebarRegexEnabled = false;
  let searchSelectedIndex = -1;
  let filteredSearchResults = [];

  // Image Zoom & Pan State
  let currentZoom = 1.0;
  let fitZoom = 1.0;
  let panX = 0;
  let panY = 0;
  let isPanning = false;
  let panStartX = 0;
  let panStartY = 0;

  // =========================================================================
  // URL Normalization Helpers
  // =========================================================================

  function normalizeDocUrl(url) {
    if (!url) return 'docs_view/overviews/intro-txt.html';
    const hashIdx = url.indexOf('#');
    let pathPart = hashIdx !== -1 ? url.substring(0, hashIdx) : url;
    let hashPart = hashIdx !== -1 ? url.substring(hashIdx) : '';
    let clean = pathPart.replace(/^[./]+/, '');
    if (clean.includes('examples_view/')) {
      clean = clean.substring(clean.indexOf('examples_view/'));
    } else if (clean.includes('docs_view/')) {
      clean = clean.substring(clean.indexOf('docs_view/'));
    } else {
      clean = 'docs_view/' + clean;
    }
    return clean + hashPart;
  }

  function normalizeExampleUrl(url) {
    if (!url) return 'examples_view/basics/hello_world.html';
    const hashIdx = url.indexOf('#');
    let pathPart = hashIdx !== -1 ? url.substring(0, hashIdx) : url;
    let hashPart = hashIdx !== -1 ? url.substring(hashIdx) : '';
    let clean = pathPart.replace(/^[./]+/, '');
    if (clean.includes('examples_view/')) {
      clean = clean.substring(clean.indexOf('examples_view/'));
    } else {
      clean = 'examples_view/' + clean;
    }
    return clean + hashPart;
  }

  function normalizeSrcUrl(url) {
    if (!url) return 'src_view/comps/uvm_driver.svh.html#L44';
    const hashIdx = url.indexOf('#');
    let pathPart = hashIdx !== -1 ? url.substring(0, hashIdx) : url;
    let hashPart = hashIdx !== -1 ? url.substring(hashIdx) : '';
    let clean = pathPart.replace(/^[./]+/, '');
    if (clean.includes('src_view/')) {
      clean = clean.substring(clean.indexOf('src_view/'));
    } else {
      clean = 'src_view/' + clean;
    }
    return clean + hashPart;
  }

  function normalizePathForCompare(p) {
    if (!p) return '';
    return p.split('#')[0].split('?')[0].replace(/^[./]+/, '').toLowerCase();
  }

  function urlsMatch(url1, url2) {
    if (!url1 || !url2) return false;
    const clean1 = normalizePathForCompare(url1);
    const clean2 = normalizePathForCompare(url2);
    if (!clean1 || !clean2) return false;
    if (clean1 === clean2) return true;
    if (clean1.endsWith('/' + clean2) || clean2.endsWith('/' + clean1)) return true;
    const bare1 = clean1.replace(/^(docs_view|src_view|examples_view)\//, '');
    const bare2 = clean2.replace(/^(docs_view|src_view|examples_view)\//, '');
    return bare1 === bare2 || bare1.endsWith('/' + bare2) || bare2.endsWith('/' + bare1);
  }

  function setFrameSrc(frame, relUrl) {
    if (!frame || !relUrl) return;
    try {
      const targetUrl = new URL(relUrl, window.location.href);
      let currentPath = '';
      try {
        if (frame.contentWindow && frame.contentWindow.location) {
          currentPath = frame.contentWindow.location.pathname;
        }
      } catch (e) { }
      if (!currentPath && frame.src) {
        currentPath = new URL(frame.src, window.location.href).pathname;
      }
      const rawAnchor = targetUrl.hash ? targetUrl.hash.replace(/^#/, '') : '';

      // If already on the same page, do not reload the iframe; scroll only if anchor specified
      if (currentPath === targetUrl.pathname) {
        if (targetUrl.hash) {
          try {
            frame.contentWindow.location.hash = targetUrl.hash;
          } catch (e) { }
          if (frame.contentWindow && rawAnchor) {
            frame.contentWindow.postMessage({
              type: 'scrollToSection',
              anchor: rawAnchor,
              id: rawAnchor
            }, '*');
          }
        }
        return;
      }
    } catch (e) { }

    // When loading a new document, ensure cross-frame scroll executes once frame is loaded
    try {
      const targetUrl = new URL(relUrl, window.location.href);
      const rawAnchor = targetUrl.hash ? targetUrl.hash.replace(/^#/, '') : '';
      if (rawAnchor) {
        const onFrameLoaded = function () {
          frame.removeEventListener('load', onFrameLoaded);
          setTimeout(() => {
            try {
              if (frame.contentWindow) {
                frame.contentWindow.postMessage({
                  type: 'scrollToSection',
                  anchor: rawAnchor,
                  id: rawAnchor
                }, '*');
              }
            } catch (err) { }
          }, 180);
        };
        frame.addEventListener('load', onFrameLoaded);
      }
    } catch (e) { }

    // Ensure new page adheres to current theme as soon as it loads
    const onFrameThemeLoaded = function () {
      frame.removeEventListener('load', onFrameThemeLoaded);
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      try {
        if (frame.contentDocument && frame.contentDocument.documentElement) {
          frame.contentDocument.documentElement.setAttribute('data-theme', currentTheme);
        }
      } catch (e) { }
      try {
        if (frame.contentWindow) {
          frame.contentWindow.postMessage({ theme: currentTheme }, '*');
        }
      } catch (e) { }
    };
    frame.addEventListener('load', onFrameThemeLoaded);

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
    // Freeze transitions across main document and iframes to eliminate staggered lag
    const docs = [document];
    [docFrame, srcFrame].forEach(frame => {
      try {
        if (frame && frame.contentDocument) docs.push(frame.contentDocument);
      } catch (e) { }
    });

    docs.forEach(doc => {
      if (doc && doc.documentElement) {
        doc.documentElement.classList.add('theme-transitioning');
        doc.documentElement.setAttribute('data-theme', theme);
      }
    });

    localStorage.setItem('theme', theme);
    updateThemeIcon(theme);
    updateFaviconAndLogo(theme);

    // Broadcast via postMessage for cross-frame listeners
    [docFrame, srcFrame].forEach(frame => {
      if (!frame) return;
      try {
        if (frame.contentWindow) {
          frame.contentWindow.postMessage({ theme }, '*');
        }
      } catch (e) { }
    });

    // Re-enable interactive hover transitions on next paint
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        docs.forEach(doc => {
          try {
            if (doc && doc.documentElement) {
              doc.documentElement.classList.remove('theme-transitioning');
            }
          } catch (e) { }
        });
      });
    });
  }

  function updateFaviconAndLogo(theme) {
    const isDark = theme === 'dark';
    const faviconFile = isDark ? 'images/favicon_dark.svg' : 'images/favicon_light.svg';

    // Update browser favicon <link rel="icon">
    let faviconLink = document.querySelector('link[rel="icon"]');
    if (faviconLink) {
      faviconLink.href = faviconFile;
    }

    // Update brand logo in header
    const brandLogo = document.getElementById('brand-logo');
    if (brandLogo) {
      brandLogo.src = faviconFile;
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


  // Debounce utility
  function debounce(func, wait) {
    let timeout;
    const debounced = function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
    debounced.cancel = function () {
      clearTimeout(timeout);
    };
    return debounced;
  }

  const viewBtns = document.querySelectorAll('.view-btn');
  viewBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.getAttribute('data-mode');
      if (mode === 'split') {
        if (currentMode === 'docs') {
          if (currentDocUrl.includes('examples_view/')) {
            // Auto pair example with corresponding UVM source code
            const exClean = currentDocUrl.replace(/^examples_view\//, '');
            if (typeof UVM_DATA !== 'undefined' && UVM_DATA.exampleToSrc && UVM_DATA.exampleToSrc[exClean]) {
              const pairedSrc = UVM_DATA.exampleToSrc[exClean];
              currentSrcUrl = pairedSrc;
              setFrameSrc(srcFrame, pairedSrc);
              updateSrcTitle(pairedSrc);
            }
          } else {
            // Auto pair with corresponding source code if available
            const docClean = currentDocUrl.replace(/^docs_view\//, '');
            if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docToSrc && UVM_DATA.docToSrc[docClean]) {
              const pairedSrc = UVM_DATA.docToSrc[docClean];
              currentSrcUrl = pairedSrc;
              setFrameSrc(srcFrame, pairedSrc);
              updateSrcTitle(pairedSrc);
            }
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
      } else if (mode === 'source') {
        switchSidebarTab('source');
      } else if (mode === 'docs') {
        switchSidebarTab('docs');
      }
      setViewMode(mode, true);
    });
  });

  function switchSidebarTab(tabName) {
    if (activeSidebarTab === tabName) return;
    activeSidebarTab = tabName;
    tabBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
    });
    if (typeof updateSidebarPillsForTab === 'function') {
      updateSidebarPillsForTab();
    }
    renderSidebar();
    highlightActiveSidebar();
  }

  function setViewMode(mode, updateHistory = true) {
    if (currentMode === mode && !updateHistory) return;

    // Preserve the exact scroll reading level of the active doc frame before mode class switch
    try {
      if (docFrame && docFrame.contentWindow) {
        if (docFrame.contentWindow.PageCommon && docFrame.contentWindow.PageCommon.saveScrollAnchor) {
          docFrame.contentWindow.PageCommon.saveScrollAnchor();
        } else {
          docFrame.contentWindow.postMessage({ type: 'saveScrollAnchor' }, '*');
        }
      }
    } catch (e) { }

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

    // Restore the exact reading level synchronously and on next frame to eliminate visual lag
    try {
      if (docFrame && docFrame.contentWindow) {
        if (docFrame.contentWindow.PageCommon && docFrame.contentWindow.PageCommon.restoreScrollAnchor) {
          docFrame.contentWindow.PageCommon.restoreScrollAnchor();
        } else {
          docFrame.contentWindow.postMessage({ type: 'restoreScrollAnchor' }, '*');
        }
      }
    } catch (e) { }

    requestAnimationFrame(() => {
      try {
        if (docFrame && docFrame.contentWindow) {
          if (docFrame.contentWindow.PageCommon && docFrame.contentWindow.PageCommon.restoreScrollAnchor) {
            docFrame.contentWindow.PageCommon.restoreScrollAnchor();
          } else {
            docFrame.contentWindow.postMessage({ type: 'restoreScrollAnchor' }, '*');
          }
        }
      } catch (e) { }
    });

    if (updateHistory) {
      updateHash();
    }
  }

  // Global handler for when a doc page requests to view source code
  let lastOpenSource = { url: '', time: 0 };
  window.openSourceView = function (srcUrl) {
    const now = Date.now();
    if (lastOpenSource.url === srcUrl && (now - lastOpenSource.time) < 150) return;
    lastOpenSource = { url: srcUrl, time: now };

    const fullSrc = normalizeSrcUrl(srcUrl);
    currentSrcUrl = fullSrc;
    setFrameSrc(srcFrame, fullSrc);
    updateSrcTitle(fullSrc);

    // Switch to split view so user sees both doc and source without resetting reading position
    if (currentMode !== 'split') {
      setViewMode('split', true);
    } else {
      updateHash();
    }
  };

  // Global handler for when a page requests to view an example
  window.openExampleView = function (exUrl) {
    const fullEx = normalizeExampleUrl(exUrl);
    currentDocUrl = fullEx;
    setFrameSrc(docFrame, fullEx);
    updateDocTitle(fullEx);

    if (currentMode === 'source') {
      setViewMode('docs', true);
    } else {
      updateHash();
    }
    switchSidebarTab('examples');
    highlightActiveSidebar(fullEx);
  };

  // Global handler for when a source page requests to view documentation
  window.openDocView = function (docUrl, symbol) {
    let fullDoc = null;
    if (symbol && typeof UVM_DATA !== 'undefined' && UVM_DATA.searchIndex) {
      const symClean = symbol.replace(/^`/, '');
      const symLower = symbol.toLowerCase();
      const cleanLower = symClean.toLowerCase();

      // 1. Exact match
      let match = UVM_DATA.searchIndex.find(s => s.name === symbol && s.doc);
      // 2. Exact match with or without macro backtick
      if (!match) {
        match = UVM_DATA.searchIndex.find(s => (s.name === '`' + symClean || s.name === symClean) && s.doc);
      }
      // 3. Case-insensitive exact match
      if (!match) {
        match = UVM_DATA.searchIndex.find(s => {
          if (!s.name || !s.doc) return false;
          const sClean = s.name.replace(/^`/, '').toLowerCase();
          return sClean === cleanLower || s.name.toLowerCase() === symLower;
        });
      }
      // 4. Suffix match (methods or nested types, e.g. class::method or class.method)
      if (!match) {
        match = UVM_DATA.searchIndex.find(s => {
          if (!s.name || !s.doc) return false;
          return s.name.endsWith('::' + symClean) || s.name.endsWith('.' + symClean);
        });
      }
      // 5. Broad substring match for classes and macros
      if (!match) {
        match = UVM_DATA.searchIndex.find(s => {
          if (!s.name || !s.doc) return false;
          const sLower = s.name.toLowerCase();
          return (s.type === 'class' || s.type === 'macro') && (sLower.includes(cleanLower) || cleanLower.includes(sLower));
        });
      }

      if (match && match.doc) {
        fullDoc = normalizeDocUrl(match.doc);
      }
    }

    if (!fullDoc && docUrl) {
      fullDoc = normalizeDocUrl(docUrl);
    }
    if (!fullDoc) {
      fullDoc = 'docs_view/overviews/intro-txt.html';
    }

    currentDocUrl = fullDoc;
    setFrameSrc(docFrame, fullDoc);
    updateDocTitle(fullDoc);

    // Preserve doc mode if user is already in doc mode; switch to split only if in source mode
    if (currentMode === 'source') {
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
    } else if (e.data.type === 'openDocView' && (e.data.url || e.data.symbol)) {
      window.openDocView(e.data.url, e.data.symbol);
    } else if (e.data.type === 'openExampleView' && e.data.url) {
      window.openExampleView(e.data.url);
    } else if (e.data.type === 'exampleNavigated' && e.data.url) {
      const fullEx = normalizeExampleUrl(e.data.url);
      currentDocUrl = fullEx;
      updateDocTitle(fullEx);
      highlightActiveSidebar(fullEx);
      updateHash();
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
    } else if (e.data.type === 'openImageModal') {
      openImageZoomModal(e.data.src, e.data.title);
    } else if (e.data.type === 'closeImageModal') {
      closeImageZoomModal();
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

      const exampleCategories = ['basics/', 'infrastructure/', 'phasing/', 'sequences/', 'tlm-1/', 'tlm-2/', 'registers/', 'integrated/'];
      const isEx = rawDoc && (rawDoc.includes('examples_view/') || exampleCategories.some(cat => rawDoc.startsWith(cat) || rawDoc.includes('/' + cat)));

      const fullDoc = rawDoc ? (isEx ? normalizeExampleUrl(rawDoc) : normalizeDocUrl(rawDoc)) : currentDocUrl;
      const fullSrc = rawSrc ? normalizeSrcUrl(rawSrc) : currentSrcUrl;

      const docChanged = currentDocUrl !== fullDoc;
      const srcChanged = currentSrcUrl !== fullSrc;

      currentDocUrl = fullDoc;
      currentSrcUrl = fullSrc;

      if (currentMode !== 'split') {
        setViewMode('split', false);
      }

      if (docChanged) {
        setFrameSrc(docFrame, fullDoc);
      }
      if (srcChanged) {
        setFrameSrc(srcFrame, fullSrc);
      }

      updateDocTitle(fullDoc);
      updateSrcTitle(fullSrc);
      highlightActiveSidebar(fullDoc);
      if (isEx || fullDoc.includes('examples_view/')) {
        switchSidebarTab('examples');
      }
    } else if (hash.startsWith('#/src/')) {
      const srcPath = normalizeSrcUrl(hash.substring(6));
      currentSrcUrl = srcPath;
      setViewMode('source', false);
      setFrameSrc(srcFrame, srcPath);
      updateSrcTitle(srcPath);
      highlightActiveSidebar(srcPath);
    } else if (hash.startsWith('#/example/')) {
      const exPath = normalizeExampleUrl(hash.substring(10));
      currentDocUrl = exPath;
      setViewMode('docs', false);
      setFrameSrc(docFrame, exPath);
      updateDocTitle(exPath);
      switchSidebarTab('examples');
      highlightActiveSidebar(exPath);
    } else if (hash === '#/examples') {
      switchSidebarTab('examples');
      const defaultEx = 'examples_view/basics/hello_world.html';
      currentDocUrl = defaultEx;
      setViewMode('docs', false);
      setFrameSrc(docFrame, defaultEx);
      updateDocTitle(defaultEx);
      highlightActiveSidebar(defaultEx);
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
      const isExample = currentDocUrl.includes('examples_view/');
      const doc = isExample
        ? 'examples_view/' + currentDocUrl.replace(/^examples_view\//, '')
        : currentDocUrl.replace(/^docs_view\//, '');
      const src = currentSrcUrl.replace(/^src_view\//, '');
      window.location.hash = `#/split?doc=${encodeURIComponent(doc)}&src=${encodeURIComponent(src)}`;
    } else if (currentMode === 'source') {
      const src = currentSrcUrl.replace(/^src_view\//, '');
      window.location.hash = `#/src/${src}`;
    } else {
      if (currentDocUrl.includes('examples_view/')) {
        const ex = currentDocUrl.replace(/^examples_view\//, '');
        window.location.hash = `#/example/${ex}`;
      } else {
        const doc = currentDocUrl.replace(/^docs_view\//, '');
        window.location.hash = `#/doc/${doc}`;
      }
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
    if (url.includes('examples_view/')) {
      const clean = url.replace('examples_view/', '').replace('.html', '').split('#')[0];
      docPaneTitle.textContent = `Example: ${clean}`;
    } else {
      const clean = url.replace('docs_view/', '').replace('.html', '').split('#')[0];
      docPaneTitle.textContent = clean;
    }
  }

  function updateSrcTitle(url) {
    if (!srcPaneTitle) return;
    const clean = url.replace('src_view/', '').replace('.html', '').split('#')[0];
    srcPaneTitle.textContent = clean;
  }

  // =========================================================================
  // Matcher & Multi-word / Regex Search Utilities
  // =========================================================================

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function getQueryMatcher(rawQuery, isRegex, isCaseSensitive, errorTargetEl) {
    if (!rawQuery) {
      if (errorTargetEl) errorTargetEl.classList.remove('regex-error');
      return null;
    }
    if (isRegex) {
      try {
        const flags = isCaseSensitive ? '' : 'i';
        const re = new RegExp(rawQuery, flags);
        if (errorTargetEl) errorTargetEl.classList.remove('regex-error');
        return { type: 'regex', regex: re, valid: true, raw: rawQuery, isCaseSensitive };
      } catch (err) {
        if (errorTargetEl) errorTargetEl.classList.add('regex-error');
        return { type: 'regex', regex: null, valid: false, error: err.message, raw: rawQuery, isCaseSensitive };
      }
    }
    if (errorTargetEl) errorTargetEl.classList.remove('regex-error');
    const clean = isCaseSensitive ? rawQuery.trim() : rawQuery.toLowerCase().trim();
    const words = clean.split(/[\s:.]+/).filter(Boolean);
    return { type: 'words', words, clean, isCaseSensitive, raw: rawQuery, valid: true };
  }

  function matchSymbolItem(item, matcher) {
    if (!matcher) return { match: true, score: 0 };
    const name = item.name || '';
    const cat = item.category || '';
    const desc = item.desc || '';

    if (matcher.type === 'regex') {
      if (!matcher.valid || !matcher.regex) return { match: false, score: 0 };
      const re = matcher.regex;
      const fullColon = cat ? `${cat}::${name}` : name;
      const fullDot = cat ? `${cat}.${name}` : name;
      const fullSpace = cat ? `${cat} ${name}` : name;

      if (re.test(name)) return { match: true, score: 1000 };
      if (re.test(fullColon) || re.test(fullDot)) return { match: true, score: 900 };
      if (re.test(fullSpace)) return { match: true, score: 800 };
      if (re.test(cat)) return { match: true, score: 600 };
      if (re.test(desc)) return { match: true, score: 300 };
      return { match: false, score: 0 };
    }

    // Multi-word mode: matches name, class (category), or two parts of expression
    const words = matcher.words;
    if (words.length === 0) return { match: true, score: 0 };

    const targetName = matcher.isCaseSensitive ? name : name.toLowerCase();
    const targetCat = matcher.isCaseSensitive ? cat : cat.toLowerCase();
    const targetDesc = matcher.isCaseSensitive ? desc : desc.toLowerCase();
    const cleanQuery = matcher.clean;

    // Check if every word appears in name, category, or description
    const combined = `${targetName} ${targetCat} ${targetDesc}`;
    const allFound = words.every(w => combined.includes(w));
    if (!allFound) return { match: false, score: 0 };

    // Calculate score based on where words were matched
    let score = 0;
    if (targetName === cleanQuery) {
      score = 1000; // Exact match
    } else if (targetName.startsWith(cleanQuery)) {
      score = 900; // Prefix match
    } else if (words.every(w => targetName.includes(w))) {
      // 2 parties de la même expression (ex: "get" & "data" dans "get_trigger_data")
      score = 800;
    } else if (words.every(w => targetName.includes(w) || targetCat.includes(w))) {
      // Mots répartis entre la classe et la méthode (ex: "component" et "build")
      score = 700;
    } else if (words.every(w => targetCat.includes(w))) {
      // Tous les mots dans la classe
      score = 500;
    } else {
      // Mots trouvés dans la description
      score = 300;
    }

    return { match: true, score };
  }

  function highlightMatch(text, matcher) {
    if (!text) return '';
    if (!matcher) return escapeHtml(text);

    let pattern = null;
    if (matcher.type === 'regex') {
      if (!matcher.valid || !matcher.regex) return escapeHtml(text);
      try {
        const gFlags = (matcher.regex.flags || '') + (matcher.regex.flags.includes('g') ? '' : 'g');
        pattern = new RegExp(matcher.regex.source, gFlags);
      } catch (e) {
        return escapeHtml(text);
      }
    } else {
      const words = matcher.words;
      if (!words || words.length === 0) return escapeHtml(text);
      const escaped = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).filter(Boolean);
      if (escaped.length === 0) return escapeHtml(text);
      pattern = new RegExp(`(${escaped.join('|')})`, matcher.isCaseSensitive ? 'g' : 'gi');
    }

    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = pattern.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(escapeHtml(text.substring(lastIndex, match.index)));
      }
      parts.push(`<strong style="color:var(--primary); text-decoration:underline">${escapeHtml(match[0])}</strong>`);
      lastIndex = pattern.lastIndex;

      if (match[0].length === 0) {
        pattern.lastIndex++;
      }
    }

    if (lastIndex < text.length) {
      parts.push(escapeHtml(text.substring(lastIndex)));
    }

    return parts.join('');
  }

  function isItemTypeAllowed(itemType, filterSet) {
    if (!filterSet || filterSet.has('all') || filterSet.size === 0) return true;
    if (!itemType) return false;
    if (itemType === 'method') {
      return filterSet.has('function') || filterSet.has('task') || filterSet.has('method');
    }
    if (itemType === 'studio' || itemType === 'stepper' || itemType === 'example') {
      return filterSet.has('example');
    }
    if (itemType === 'overview') {
      return filterSet.has('class') || filterSet.has('file');
    }
    return filterSet.has(itemType);
  }

  function isRagResultAllowed(r, filterSet) {
    if (!filterSet || filterSet.has('all') || filterSet.size === 0) return true;

    const url = (r.targetUrl || (r.chunk && r.chunk.url) || '').toLowerCase();
    const isExample = url.includes('examples_view/') || r.type === 'example' || r.type === 'studio' || r.type === 'stepper' || r.targetType === 'example';

    // 1. Example Filter
    if (filterSet.has('example')) {
      if (isExample) {
        if (filterSet.has('beginner') || filterSet.has('intermediate') || filterSet.has('advanced')) {
          const desc = (r.snippet || (r.chunk && r.chunk.text) || '').toLowerCase();
          const diff = ((r.chunk && r.chunk.difficulty) || '').toLowerCase();
          const cat = (r.category || '').toLowerCase();
          let matchDiff = false;
          ['beginner', 'intermediate', 'advanced'].forEach(d => {
            if (filterSet.has(d)) {
              if (diff === d || cat.includes(d) || desc.includes(d + ' level') || desc.includes('level: ' + d)) {
                matchDiff = true;
              }
            }
          });
          return matchDiff;
        }
        return true;
      }
    }
    if (filterSet.size === 1 && filterSet.has('example') && !isExample) {
      return false;
    }
    if (isExample && !filterSet.has('example')) {
      return false;
    }

    // 2. Class Filter
    if (filterSet.has('class')) {
      if (r.type === 'class' || r.targetType === 'class' || r.type === 'overview') return true;
    }

    // 3. Functions & Tasks Filter
    if (filterSet.has('function') || filterSet.has('task')) {
      if (r.type === 'method' || r.type === 'function' || r.type === 'task' ||
        r.targetType === 'method' || r.targetType === 'function' || r.targetType === 'task') {
        return true;
      }
      if (r.targetSections && r.targetSections.some(s => s.type === 'method' || s.type === 'function' || s.type === 'task')) {
        return true;
      }
      if (r.children && r.children.some(c => c.chunk && (c.chunk.type === 'method' || c.chunk.type === 'function' || c.chunk.type === 'task'))) {
        return true;
      }
    }

    // 4. Macro Filter
    if (filterSet.has('macro')) {
      if (r.type === 'macro' || r.targetType === 'macro') return true;
      if (r.targetSections && r.targetSections.some(s => s.type === 'macro')) return true;
      if (r.children && r.children.some(c => c.chunk && c.chunk.type === 'macro')) return true;
    }

    // 5. Source File Filter
    if (filterSet.has('file')) {
      if (r.type === 'file' || r.targetType === 'file') return true;
      const docPath = url.split('#')[0];
      if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docToSrc && UVM_DATA.docToSrc[docPath]) {
        return true;
      }
      if (r.type === 'overview') return true;
    }

    return false;
  }

  function handleMultiFilterPillClick(clickedPill, allPills, filterSet, onFilterChange) {
    const type = clickedPill.getAttribute('data-type');
    if (!type) return;

    if (type === 'all') {
      // Clicking 'All' resets to only 'all'
      filterSet.clear();
      filterSet.add('all');
      allPills.forEach(p => p.classList.toggle('active', p.getAttribute('data-type') === 'all'));
    } else {
      // If 'all' was active, deactivate it because specific types are being selected
      if (filterSet.has('all')) {
        filterSet.delete('all');
        const allPill = Array.from(allPills).find(p => p.getAttribute('data-type') === 'all');
        if (allPill) allPill.classList.remove('active');
      }

      // Toggle the clicked type (non-exclusive)
      if (filterSet.has(type)) {
        filterSet.delete(type);
        clickedPill.classList.remove('active');
      } else {
        filterSet.add(type);
        clickedPill.classList.add('active');
      }

      // If no specific types remain selected, reset back to 'all'
      if (filterSet.size === 0) {
        filterSet.clear();
        filterSet.add('all');
        allPills.forEach(p => p.classList.toggle('active', p.getAttribute('data-type') === 'all'));
      }
    }

    onFilterChange();
  }

  function docItemMatchesMatcher(item, matcher) {
    if (!matcher) {
      if (sidebarFilterTypes.has('all') || sidebarFilterTypes.size === 0) return true;
      if (sidebarFilterTypes.has('class') && item.title && !item.title.includes('Package') && !item.title.includes('Overview')) {
        return true;
      }
      if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docHeadings && item.href) {
        const headings = UVM_DATA.docHeadings[item.href] || [];
        return headings.some(h => {
          if (h.type === 'main') return sidebarFilterTypes.has('class');
          if (h.type === 'method') return sidebarFilterTypes.has('function') || sidebarFilterTypes.has('task');
          if (h.type === 'macro') return sidebarFilterTypes.has('macro');
          return false;
        });
      }
      return true;
    }

    const title = item.title || '';
    if (matcher.type === 'regex') {
      if (!matcher.valid || !matcher.regex) return false;
      if (matcher.regex.test(title)) return true;
      if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docHeadings && item.href) {
        const headings = UVM_DATA.docHeadings[item.href] || [];
        return headings.some(h => {
          const hTitle = h.title || '';
          const hGroup = h.group || '';
          return matcher.regex.test(hTitle) || matcher.regex.test(`${title}::${hTitle}`) || matcher.regex.test(`${title} ${hTitle}`) || matcher.regex.test(hGroup);
        });
      }
      return false;
    }

    // Multi-word mode:
    const words = matcher.words;
    if (words.length === 0) return true;
    const lowerTitle = matcher.isCaseSensitive ? title : title.toLowerCase();

    // If all words match in doc title (e.g. "uvm component")
    if (words.every(w => lowerTitle.includes(w))) return true;

    // If words match across title and method headings (e.g. "component build")
    if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docHeadings && item.href) {
      const headings = UVM_DATA.docHeadings[item.href] || [];
      return headings.some(h => {
        if (!sidebarFilterTypes.has('all') && sidebarFilterTypes.size > 0) {
          if (h.type === 'main' && !sidebarFilterTypes.has('class')) return false;
          if (h.type === 'method' && !sidebarFilterTypes.has('function') && !sidebarFilterTypes.has('task')) return false;
          if (h.type === 'macro' && !sidebarFilterTypes.has('macro')) return false;
        }
        const hTitle = matcher.isCaseSensitive ? (h.title || '') : (h.title || '').toLowerCase();
        const hGroup = matcher.isCaseSensitive ? (h.group || '') : (h.group || '').toLowerCase();
        const combined = `${lowerTitle} ${hTitle} ${hGroup}`;
        return words.every(w => combined.includes(w));
      });
    }

    return false;
  }

  function sourceNodeMatches(node, matcher) {
    if (!matcher) return true;
    const name = node.name || '';
    const path = node.path || '';

    if (matcher.type === 'regex') {
      if (!matcher.valid || !matcher.regex) return false;
      return matcher.regex.test(name) || matcher.regex.test(path);
    }

    const words = matcher.words;
    if (words.length === 0) return true;
    const combined = (matcher.isCaseSensitive ? `${name} ${path}` : `${name} ${path}`.toLowerCase());
    return words.every(w => combined.includes(w));
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
      updateSidebarPillsForTab();
      renderSidebar();
    });
  });

  function updateSidebarPillsForTab() {
    if (!sidebarPillsContainer) return;
    // Reset sidebarFilterTypes to 'all' when switching tabs so filters from one tab don't block the other
    sidebarFilterTypes.clear();
    sidebarFilterTypes.add('all');

    if (activeSidebarTab === 'examples') {
      sidebarPillsContainer.innerHTML = `
            <button class="sidebar-pill active" data-type="all">All</button>
            <button class="sidebar-pill" data-type="beginner">Beginner</button>
            <button class="sidebar-pill" data-type="intermediate">Intermediate</button>
            <button class="sidebar-pill" data-type="advanced">Advanced</button>
          `;
    } else if (activeSidebarTab === 'hierarchy') {
      sidebarPillsContainer.innerHTML = `
            <button class="sidebar-pill active" data-type="all">All</button>
            <button class="sidebar-pill" data-type="component">Components</button>
            <button class="sidebar-pill" data-type="object">Objects</button>
            <button class="sidebar-pill" data-type="sequence">Sequences</button>
            <button class="sidebar-pill" data-type="tlm">TLM</button>
            <button class="sidebar-pill" data-type="reg">Registers</button>
            <button class="sidebar-pill" data-type="phase">Phases</button>
          `;
    } else {
      // For docs / source / index: show language symbol types (Docs has no examples)
      sidebarPillsContainer.innerHTML = `
            <button class="sidebar-pill active" data-type="all">All</button>
            <button class="sidebar-pill" data-type="class">Classes</button>
            <button class="sidebar-pill" data-type="function">Functions</button>
            <button class="sidebar-pill" data-type="task">Tasks</button>
            <button class="sidebar-pill" data-type="macro">Macros</button>
          `;
    }

    // Re-query and bind click listeners to updated pills
    sidebarPills = sidebarPillsContainer.querySelectorAll('.sidebar-pill');
    sidebarPills.forEach(pill => {
      pill.addEventListener('click', () => {
        handleMultiFilterPillClick(pill, sidebarPills, sidebarFilterTypes, () => {
          renderSidebar();
        });
      });
    });
  }

  if (sidebarFilter) {
    sidebarFilter.addEventListener('input', debounce((e) => {
      if (sidebarFilterClear) {
        sidebarFilterClear.style.display = e.target.value.length > 0 ? 'inline-flex' : 'none';
      }
      renderSidebar();
    }, 150));

    sidebarFilter.addEventListener('keydown', (e) => {
      if (e.key === 'r' && e.altKey) {
        e.preventDefault();
        sidebarRegexEnabled = !sidebarRegexEnabled;
        if (sidebarFilterRegex) sidebarFilterRegex.classList.toggle('active', sidebarRegexEnabled);
        renderSidebar();
      } else if (e.key === 'Escape') {
        if (sidebarFilter.value.length > 0) {
          e.preventDefault();
          sidebarFilter.value = '';
          if (sidebarFilterClear) sidebarFilterClear.style.display = 'none';
          sidebarFilter.classList.remove('regex-error');
          renderSidebar();
        }
      }
    });
  }

  if (sidebarFilterClear) {
    sidebarFilterClear.addEventListener('click', () => {
      if (sidebarFilter) {
        sidebarFilter.value = '';
        sidebarFilterClear.style.display = 'none';
        sidebarFilter.classList.remove('regex-error');
        sidebarFilter.focus();
        renderSidebar();
      }
    });
  }

  if (sidebarFilterRegex) {
    sidebarFilterRegex.addEventListener('click', () => {
      sidebarRegexEnabled = !sidebarRegexEnabled;
      sidebarFilterRegex.classList.toggle('active', sidebarRegexEnabled);
      renderSidebar();
    });
  }

  sidebarPills.forEach(pill => {
    pill.addEventListener('click', () => {
      handleMultiFilterPillClick(pill, sidebarPills, sidebarFilterTypes, () => {
        renderSidebar();
      });
    });
  });

  function renderSidebar() {
    if (!sidebarContent) return;
    if (typeof UVM_DATA === 'undefined') {
      sidebarContent.innerHTML = `
            <div style="padding: 1.5rem; text-align: center; color: var(--color-text-muted, #64748b);">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin: 0 auto 0.75rem; display: block; opacity: 0.6;">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <p style="font-weight: 600; margin-bottom: 0.5rem; color: var(--color-text-primary, #1e293b);">Search data not loaded</p>
              <p style="font-size: 0.85rem; line-height: 1.4;">Run <code>python scripts/build_docs.py --search-only</code> to generate <code>js/search_data.js</code>.</p>
            </div>
          `;
      return;
    }
    const rawQuery = sidebarFilter ? sidebarFilter.value : '';

    if (activeSidebarTab === 'docs') {
      renderDocsMenu(rawQuery);
    } else if (activeSidebarTab === 'source') {
      renderSourceTree(rawQuery);
    } else if (activeSidebarTab === 'examples') {
      renderExamplesTree(rawQuery);
    } else if (activeSidebarTab === 'hierarchy') {
      renderHierarchyTree(rawQuery);
    } else if (activeSidebarTab === 'index') {
      renderAlphabeticalIndex(rawQuery);
    }
  }

  function renderExamplesTree(rawQuery) {
    const examplesTree = UVM_DATA.examplesTree || [];
    const matcher = getQueryMatcher(rawQuery, sidebarRegexEnabled, false, sidebarFilter);
    let html = '';

    examplesTree.forEach(cat => {
      const subItems = (cat.children || []).filter(ex => {
        // Difficulty filtering if beginner, intermediate, or advanced is selected
        if (sidebarFilterTypes.has('beginner') || sidebarFilterTypes.has('intermediate') || sidebarFilterTypes.has('advanced')) {
          const exDiff = (ex.difficulty || 'beginner').toLowerCase();
          let matchDiff = false;
          ['beginner', 'intermediate', 'advanced'].forEach(d => {
            if (sidebarFilterTypes.has(d) && exDiff === d) {
              matchDiff = true;
            }
          });
          if (!matchDiff) return false;
        } else if (!isItemTypeAllowed('example', sidebarFilterTypes)) {
          return false;
        }

        if (!matcher) return true;
        const haystack = `${ex.title} ${ex.difficulty} ${ex.scope} ${ex.summary || ''}`.toLowerCase();
        if (matcher.type === 'regex') {
          return matcher.regex ? matcher.regex.test(haystack) : true;
        }
        return matcher.words.every(w => haystack.includes(w));
      });

      const catTitleMatches = matcher && matcher.type === 'words' && matcher.words.every(w => cat.title.toLowerCase().includes(w));
      if (subItems.length > 0 || catTitleMatches) {
        html += `<div class="nav-group">
              <div class="nav-group-header">
                <span>${highlightMatch(cat.title, matcher)}</span>
                <span style="font-size:0.7rem; opacity:0.6; margin-left:auto; margin-right:0.5rem; background:var(--surface-color); padding:0.1rem 0.4rem; border-radius:9999px;">${subItems.length}</span>
                <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
              <ul class="nav-group-items">
                ${subItems.map(ex => {
          const isActive = urlsMatch(ex.href, currentDocUrl);
          return `<li>
                    <a href="#" data-doc-href="${ex.href}" class="nav-item-link ${isActive ? 'active' : ''}" title="${escapeHtml(ex.summary || '')}">
                      <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${highlightMatch(ex.title, matcher)}</span>
                      <span class="badge badge-diff-${(ex.difficulty || 'beginner').toLowerCase()}" style="font-size:0.65rem; padding:0.1rem 0.35rem; margin-left:auto; flex-shrink:0;">${ex.difficulty}</span>
                    </a>
                  </li>`;
        }).join('')}
              </ul>
            </div>`;
      }
    });

    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching examples</div>';
    attachSidebarListeners();
  }

  function renderDocsMenu(rawQuery) {
    const categories = UVM_DATA.categories || [];
    const matcher = getQueryMatcher(rawQuery, sidebarRegexEnabled, false, sidebarFilter);
    let html = '';

    categories.forEach(cat => {
      if (cat.type === 'file' || cat.type === 'index') {
        const matches = docItemMatchesMatcher(cat, matcher);
        if (matches) {
          const isActive = urlsMatch(cat.href, currentDocUrl);
          html += `<div class="nav-single-item">
            <a href="#" data-doc-href="${cat.href}" class="nav-item-link ${isActive ? 'active' : ''}">
              ${highlightMatch(cat.title, matcher)}
            </a>
          </div>`;
        }
      } else if (cat.type === 'group') {
        const subItems = filterGroupItems(cat.children || [], matcher);
        const groupTitleMatches = matcher && matcher.type === 'words' && matcher.words.every(w => cat.title.toLowerCase().includes(w));
        if (subItems.length > 0 || groupTitleMatches || (cat.overviewHref && (!matcher || groupTitleMatches))) {
          const hasOverview = !!cat.overviewHref;
          const isOverviewActive = hasOverview && urlsMatch(cat.overviewHref, currentDocUrl);
          const titleHtml = hasOverview
            ? `<a href="#" data-doc-href="${cat.overviewHref}" class="nav-group-title-link nav-item-link ${isOverviewActive ? 'active' : ''}" title="View ${escapeHtml(cat.title)} Overview">${highlightMatch(cat.title, matcher)}</a>`
            : `<span class="nav-group-title-text">${highlightMatch(cat.title, matcher)}</span>`;

          html += `<div class="nav-group ${hasOverview ? 'has-overview' : ''}">
            <div class="nav-group-header">
              ${titleHtml}
              <button type="button" class="nav-group-chevron-btn" title="Toggle section" aria-label="Toggle ${escapeHtml(cat.title)} section">
                <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </button>
            </div>
            <ul class="nav-group-items">
              ${renderGroupItemsHtml(subItems, matcher)}
            </ul>
          </div>`;
        }
      }
    });

    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching topics</div>';
    attachSidebarListeners();
  }

  function filterGroupItems(items, matcher) {
    if (!matcher) {
      if (sidebarFilterTypes.has('all') || sidebarFilterTypes.size === 0) return items;
    }
    const res = [];
    items.forEach(item => {
      if (item.type === 'file' || item.type === 'index') {
        if (docItemMatchesMatcher(item, matcher)) {
          res.push(item);
        }
      } else if (item.type === 'group') {
        const subs = filterGroupItems(item.children || [], matcher);
        const titleMatches = matcher && matcher.type === 'words' && matcher.words.every(w => item.title.toLowerCase().includes(w));
        if (subs.length > 0 || titleMatches) {
          res.push({ ...item, children: subs });
        }
      }
    });
    return res;
  }

  function renderGroupItemsHtml(items, matcher) {
    let out = '';
    items.forEach(item => {
      if (item.type === 'file' || item.type === 'index') {
        const isActive = urlsMatch(item.href, currentDocUrl);
        out += `<li>
          <a href="#" data-doc-href="${item.href}" class="nav-item-link ${isActive ? 'active' : ''}">
            ${highlightMatch(item.title, matcher)}
          </a>
        </li>`;
      } else if (item.type === 'group') {
        const hasOverview = !!item.overviewHref;
        const isOverviewActive = hasOverview && urlsMatch(item.overviewHref, currentDocUrl);
        const titleHtml = hasOverview
          ? `<a href="#" data-doc-href="${item.overviewHref}" class="nav-group-title-link nav-item-link ${isOverviewActive ? 'active' : ''}" title="View ${escapeHtml(item.title)} Overview">${highlightMatch(item.title, matcher)}</a>`
          : `<span class="nav-group-title-text">${highlightMatch(item.title, matcher)}</span>`;

        out += `<div class="nav-group ${hasOverview ? 'has-overview' : ''}">
          <div class="nav-group-header">
            ${titleHtml}
            <button type="button" class="nav-group-chevron-btn" title="Toggle section" aria-label="Toggle ${escapeHtml(item.title)} section">
              <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
          </div>
          <ul class="nav-group-items">
            ${renderGroupItemsHtml(item.children || [], matcher)}
          </ul>
        </div>`;
      }
    });
    return out;
  }

  function renderSourceTree(rawQuery) {
    const root = UVM_DATA.sourceTree || {};
    const matcher = getQueryMatcher(rawQuery, sidebarRegexEnabled, false, sidebarFilter);

    function renderNode(node, depth) {
      if (node.type === 'file') {
        if (sourceNodeMatches(node, matcher)) {
          const isActive = urlsMatch(node.url, currentSrcUrl);
          return `<div class="file-tree-item ${isActive ? 'active' : ''}" data-src-href="${node.url}" style="padding-left: ${depth * 12 + 10}px">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span>${highlightMatch(node.name, matcher)}</span>
          </div>`;
        }
        return '';
      } else if (node.type === 'dir') {
        if (hasMatch(node, matcher)) {
          const childrenHtml = (node.children || []).map(child => renderNode(child, depth + 1)).join('');
          return `<div class="nav-group">
            <div class="nav-group-header" style="padding-left: ${depth * 12 + 8}px">
              <span style="display:flex;align-items:center;gap:0.35rem;font-family:var(--font-mono)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                ${highlightMatch(node.name, matcher)}
              </span>
              <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            <div class="nav-group-items" style="padding:0">
              ${childrenHtml}
            </div>
          </div>`;
        }
        return '';
      }
      return '';
    }

    function hasMatch(node, matcher) {
      if (!matcher) return true;
      if (sourceNodeMatches(node, matcher)) return true;
      if (node.children) {
        return node.children.some(c => hasMatch(c, matcher));
      }
      return false;
    }

    const html = (root.children || []).map(child => renderNode(child, 0)).join('');
    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching files</div>';
    attachSidebarListeners();
  }

  function renderAlphabeticalIndex(rawQuery) {
    const items = UVM_DATA.searchIndex || [];
    const matcher = getQueryMatcher(rawQuery, sidebarRegexEnabled, false, sidebarFilter);

    const allSymbols = items.filter(x => {
      if (!isItemTypeAllowed(x.type, sidebarFilterTypes)) return false;
      return x.type === 'class' || x.type === 'macro' || x.type === 'function' || x.type === 'task' || x.type === 'method';
    });

    const matchedSymbols = [];
    allSymbols.forEach(item => {
      const matchRes = matchSymbolItem(item, matcher);
      if (matchRes.match) {
        matchedSymbols.push({ item, score: matchRes.score });
      }
    });

    matchedSymbols.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.item.name.localeCompare(b.item.name);
    });

    let html = '';
    matchedSymbols.forEach(({ item }) => {
      const badgeClass = item.type === 'class' ? 'badge-class' :
        (item.type === 'macro' ? 'badge-macro' :
          (item.type === 'function' ? 'badge-function' :
            (item.type === 'task' ? 'badge-task' :
              (item.type === 'example' ? 'badge-example' : 'badge-method'))));
      const isMethodLike = item.type === 'function' || item.type === 'task' || item.type === 'method';
      const ownerInfo = item.category && isMethodLike ?
        `<span class="az-symbol-owner" style="font-size:0.68rem; color:var(--text-muted); margin-left:auto; margin-right:0.35rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:110px;">${highlightMatch(item.category, matcher)}</span>` : '';
      const isDocActive = item.doc && urlsMatch(item.doc, currentDocUrl);
      const isSrcActive = item.src && urlsMatch(item.src, currentSrcUrl);
      const isActive = isDocActive || isSrcActive;
      html += `<div class="nav-single-item">
            <a href="#" data-doc-href="${item.doc || ''}" data-src-href="${item.src || ''}" class="nav-item-link az-index-link ${isActive ? 'active' : ''}" title="${item.desc || item.name}">
              <span class="az-symbol-name">${highlightMatch(item.name, matcher)}</span>
              ${ownerInfo}
              <span class="res-badge ${badgeClass}">${item.type}</span>
            </a>
          </div>`;
    });

    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching symbols</div>';
    attachSidebarListeners();
  }

  // =========================================================================
  // Class Hierarchy Tree Renderer & Controller
  // =========================================================================

  function renderHierarchyTree(rawQuery) {
    if (!UVM_DATA || !UVM_DATA.classHierarchy) {
      sidebarContent.innerHTML = `
        <div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
          <p>Class hierarchy data not available.</p>
        </div>`;
      return;
    }

    const { nodes, roots } = UVM_DATA.classHierarchy;
    const matcher = getQueryMatcher(rawQuery, sidebarRegexEnabled, false, sidebarFilter);
    const selectedRoles = sidebarFilterTypes;
    const filterByRole = !selectedRoles.has('all');

    const matchCache = new Map();
    function nodeOrDescendantMatches(cname) {
      if (matchCache.has(cname)) return matchCache.get(cname);
      const node = nodes[cname];
      if (!node) {
        const fallback = { selfMatches: false, anyChildMatches: false, keep: false };
        matchCache.set(cname, fallback);
        return fallback;
      }

      let roleMatches = true;
      if (filterByRole) {
        roleMatches = selectedRoles.has(node.role);
      }

      let textMatches = true;
      if (matcher && matcher.clean) {
        const cLower = node.name.toLowerCase();
        const sLower = (node.summary || '').toLowerCase();
        textMatches = matcher.words.every(w => cLower.includes(w) || sLower.includes(w));
      }

      const selfMatches = roleMatches && textMatches;
      let anyChildMatches = false;
      if (node.children && node.children.length > 0) {
        for (const ch of node.children) {
          const chRes = nodeOrDescendantMatches(ch);
          if (chRes.keep) {
            anyChildMatches = true;
          }
        }
      }

      const res = { selfMatches, anyChildMatches, keep: selfMatches || anyChildMatches };
      matchCache.set(cname, res);
      return res;
    }

    const isSearching = (matcher && matcher.clean) || filterByRole;

    function renderNodeHtml(cname, depth = 0) {
      const node = nodes[cname];
      if (!node) return '';

      const matchInfo = isSearching ? nodeOrDescendantMatches(cname) : { selfMatches: true, anyChildMatches: false, keep: true };
      if (isSearching && !matchInfo.keep) return '';

      const hasChildren = node.children && node.children.length > 0;
      const shouldExpand = isSearching ? matchInfo.anyChildMatches : (depth === 0 && cname === 'uvm_void');

      const roleBadges = {
        component: '<span class="hierarchy-role-badge role-component" title="UVM Component">C</span>',
        sequence: '<span class="hierarchy-role-badge role-sequence" title="UVM Sequence / Item">S</span>',
        reg: '<span class="hierarchy-role-badge role-reg" title="Register Model (UVM_REG)">R</span>',
        tlm: '<span class="hierarchy-role-badge role-tlm" title="TLM Channel / Port">T</span>',
        phase: '<span class="hierarchy-role-badge role-phase" title="Phasing">P</span>',
        object: '<span class="hierarchy-role-badge role-object" title="UVM Object">O</span>',
        utility: '<span class="hierarchy-role-badge role-utility" title="Utility">U</span>'
      };
      const badgeHtml = roleBadges[node.role] || roleBadges.utility;

      let metaBadges = '';
      if (node.methodsCount > 0) {
        metaBadges += `<span class="hierarchy-badge hierarchy-meta-methods" title="${node.methodsCount} methods">${node.methodsCount}m</span>`;
      }
      if (hasChildren) {
        metaBadges += `<span class="hierarchy-badge hierarchy-meta-subs" title="${node.children.length} subclasses">${node.children.length}</span>`;
      }

      const srcBtn = node.src
        ? `<a href="${node.src}" class="hierarchy-src-link" title="Open SystemVerilog source code" data-src-href="${node.src}">
             <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
           </a>`
        : '';

      const docHref = node.doc || '';
      const srcHref = node.src || '';

      let childrenHtml = '';
      if (hasChildren) {
        let renderedChildren = '';
        for (const ch of node.children) {
          renderedChildren += renderNodeHtml(ch, depth + 1);
        }
        if (renderedChildren) {
          childrenHtml = `<div class="hierarchy-children ${shouldExpand ? 'open' : ''}">${renderedChildren}</div>`;
        }
      }

      const displayName = highlightMatch(node.name, matcher);

      return `
        <div class="hierarchy-tree-node ${shouldExpand ? '' : 'collapsed'}" data-cname="${cname}">
          <div class="hierarchy-row" data-cname="${cname}">
            <span class="hierarchy-expander ${hasChildren ? (shouldExpand ? 'open' : '') : 'empty'}" role="button" title="${hasChildren ? 'Toggle subclasses' : ''}">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </span>
            ${badgeHtml}
            <a href="${docHref || srcHref}" class="hierarchy-link" data-doc-href="${docHref}" data-src-href="${srcHref}" data-cname="${cname}" title="${node.summary || cname}">
              ${displayName}
            </a>
            <div class="hierarchy-meta">
              ${metaBadges}
              ${srcBtn}
            </div>
          </div>
          ${childrenHtml}
        </div>`;
    }

    let treeHtml = '<div class="hierarchy-tree-root">';
    let renderedCount = 0;
    for (const rootName of roots) {
      const rendered = renderNodeHtml(rootName, 0);
      if (rendered) {
        treeHtml += rendered;
        renderedCount++;
      }
    }
    treeHtml += '</div>';

    if (renderedCount === 0) {
      sidebarContent.innerHTML = '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching classes</div>';
    } else {
      sidebarContent.innerHTML = treeHtml;
    }

    attachHierarchyListeners();
    attachSidebarListeners();
  }

  function attachHierarchyListeners() {
    sidebarContent.querySelectorAll('.hierarchy-expander:not(.empty)').forEach(exp => {
      exp.addEventListener('click', (e) => {
        e.stopPropagation();
        const node = exp.closest('.hierarchy-tree-node');
        if (!node) return;
        const children = node.querySelector(':scope > .hierarchy-children');
        if (children) {
          const isOpen = children.classList.toggle('open');
          exp.classList.toggle('open', isOpen);
          node.classList.toggle('collapsed', !isOpen);
        }
        updateSidebarToggleAllBtn();
      });
    });

    sidebarContent.querySelectorAll('.hierarchy-row').forEach(row => {
      row.addEventListener('click', (e) => {
        if (e.target.closest('.hierarchy-expander') || e.target.closest('.hierarchy-src-link') || e.target.closest('.hierarchy-link')) {
          return;
        }
        const link = row.querySelector('.hierarchy-link');
        if (link) link.click();
      });
    });
  }

  // =========================================================================
  // Left Sidebar Expand / Collapse All Controller
  // =========================================================================

  function updateSidebarToggleAllBtn() {
    if (!sidebarToggleAll) return;
    if (activeSidebarTab === 'index') {
      sidebarToggleAll.style.display = 'none';
      return;
    }
    if (activeSidebarTab === 'hierarchy') {
      const allChildren = sidebarContent.querySelectorAll('.hierarchy-children');
      if (allChildren.length === 0) {
        sidebarToggleAll.style.display = 'none';
        return;
      }
      sidebarToggleAll.style.display = 'inline-flex';
      const allCollapsed = Array.from(allChildren).every(c => !c.classList.contains('open'));
      const textSpan = sidebarToggleAll.querySelector('.sidebar-toggle-text');
      const icon = sidebarToggleAll.querySelector('.sidebar-toggle-icon');
      if (allCollapsed) {
        if (textSpan) textSpan.textContent = 'Expand all';
        if (icon) icon.innerHTML = '<polyline points="4 6 12 14 20 6"/>';
        sidebarToggleAll.setAttribute('title', 'Expand all classes');
      } else {
        if (textSpan) textSpan.textContent = 'Collapse all';
        if (icon) icon.innerHTML = '<polyline points="4 14 12 6 20 14"/>';
        sidebarToggleAll.setAttribute('title', 'Collapse all classes');
      }
      return;
    }
    const allGroups = sidebarContent.querySelectorAll('.nav-group');
    if (allGroups.length === 0) {
      sidebarToggleAll.style.display = 'none';
      return;
    }
    sidebarToggleAll.style.display = 'inline-flex';
    const allCollapsed = Array.from(allGroups).every(g => g.classList.contains('collapsed'));
    const textSpan = sidebarToggleAll.querySelector('.sidebar-toggle-text');
    const icon = sidebarToggleAll.querySelector('.sidebar-toggle-icon');
    if (allCollapsed) {
      if (textSpan) textSpan.textContent = 'Expand all';
      if (icon) icon.innerHTML = '<polyline points="4 6 12 14 20 6"/>';
      sidebarToggleAll.setAttribute('title', 'Expand all sections');
    } else {
      if (textSpan) textSpan.textContent = 'Collapse all';
      if (icon) icon.innerHTML = '<polyline points="4 14 12 6 20 14"/>';
      sidebarToggleAll.setAttribute('title', 'Collapse all sections');
    }
  }

  if (sidebarToggleAll) {
    sidebarToggleAll.addEventListener('click', () => {
      if (activeSidebarTab === 'hierarchy') {
        const allChildren = sidebarContent.querySelectorAll('.hierarchy-children');
        if (allChildren.length === 0) return;
        const anyExpanded = Array.from(allChildren).some(c => c.classList.contains('open'));
        if (anyExpanded) {
          allChildren.forEach(c => c.classList.remove('open'));
          sidebarContent.querySelectorAll('.hierarchy-expander:not(.empty)').forEach(exp => exp.classList.remove('open'));
          sidebarContent.querySelectorAll('.hierarchy-tree-node').forEach(n => n.classList.add('collapsed'));
        } else {
          allChildren.forEach(c => c.classList.add('open'));
          sidebarContent.querySelectorAll('.hierarchy-expander:not(.empty)').forEach(exp => exp.classList.add('open'));
          sidebarContent.querySelectorAll('.hierarchy-tree-node').forEach(n => n.classList.remove('collapsed'));
        }
        updateSidebarToggleAllBtn();
        return;
      }
      const allGroups = sidebarContent.querySelectorAll('.nav-group');
      if (allGroups.length === 0) return;
      const anyExpanded = Array.from(allGroups).some(g => !g.classList.contains('collapsed'));
      if (anyExpanded) {
        // Collapse all
        allGroups.forEach(g => g.classList.add('collapsed'));
      } else {
        // Expand all
        allGroups.forEach(g => g.classList.remove('collapsed'));
      }
      updateSidebarToggleAllBtn();
    });
  }

  function attachSidebarListeners() {
    // Collapsible group headers: Clicking chevron button toggles expand/collapse
    sidebarContent.querySelectorAll('.nav-group-chevron-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const group = btn.closest('.nav-group');
        if (group) group.classList.toggle('collapsed');
        updateSidebarToggleAllBtn();
      });
    });

    // Clicking on header (when it doesn't have an overview link) toggles expand/collapse
    sidebarContent.querySelectorAll('.nav-group-header').forEach(header => {
      header.addEventListener('click', (e) => {
        if (e.target.closest('a') || e.target.closest('.nav-group-chevron-btn')) {
          return;
        }
        header.closest('.nav-group').classList.toggle('collapsed');
        updateSidebarToggleAllBtn();
      });
    });

    // Navigation links (doc & src & group overview title links)
    sidebarContent.querySelectorAll('[data-doc-href], [data-src-href]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const docHref = link.getAttribute('data-doc-href');
        const srcHref = link.getAttribute('data-src-href');

        // Immediately highlight the clicked item for instant, reliable visual feedback
        sidebarContent.querySelectorAll('.nav-item-link, .file-tree-item, .hierarchy-link').forEach(el => el.classList.remove('active'));
        sidebarContent.querySelectorAll('.hierarchy-row').forEach(el => el.classList.remove('active'));
        link.classList.add('active');
        const row = link.closest('.hierarchy-row');
        if (row) row.classList.add('active');

        // Make sure all ancestor groups are expanded so the active item is in plain view
        let p = link.parentElement;
        while (p && p !== sidebarContent) {
          if (p.classList.contains('hierarchy-children')) {
            p.classList.add('open');
            const parentNode = p.closest('.hierarchy-tree-node');
            if (parentNode) {
              parentNode.classList.remove('collapsed');
              const exp = parentNode.querySelector(':scope > .hierarchy-row > .hierarchy-expander');
              if (exp) exp.classList.add('open');
            }
          } else if (p.classList.contains('nav-group')) {
            p.classList.remove('collapsed');
          }
          p = p.parentElement;
        }
        updateSidebarToggleAllBtn();

        if (activeSidebarTab === 'source' || (!docHref && srcHref)) {
          if (srcHref) loadSource(srcHref);
        } else if (docHref) {
          loadDoc(docHref);
          if (currentMode === 'split' && srcHref) {
            loadSource(srcHref);
          }
        } else if (srcHref) {
          loadSource(srcHref);
        }
        if (window.innerWidth <= 860 && sidebar) {
          sidebar.classList.remove('open');
        }
      });
    });

    // Ensure parent groups of active doc item are expanded so it is visible
    const activeItem = sidebarContent.querySelector('.nav-item-link.active, .file-tree-item.active, .hierarchy-link.active');
    if (activeItem) {
      let p = activeItem.parentElement;
      while (p && p !== sidebarContent) {
        if (p.classList.contains('hierarchy-children')) {
          p.classList.add('open');
          const parentNode = p.closest('.hierarchy-tree-node');
          if (parentNode) {
            parentNode.classList.remove('collapsed');
            const exp = parentNode.querySelector(':scope > .hierarchy-row > .hierarchy-expander');
            if (exp) exp.classList.add('open');
          }
        } else if (p.classList.contains('nav-group')) {
          p.classList.remove('collapsed');
        }
        p = p.parentElement;
      }
    }

    updateSidebarToggleAllBtn();
  }

  function highlightActiveSidebar(url) {
    const isSrcUrl = url && (url.includes('src_view/') || url.endsWith('.sv') || url.endsWith('.svh') || url.endsWith('.v') || url.endsWith('.c') || url.endsWith('.h'));
    const isExUrl = url && url.includes('examples_view/');
    const isDocUrl = url && !isSrcUrl && !isExUrl;

    // Guard: Never clear documentation/example active selection when a source file navigates, and vice versa
    if (url) {
      if ((activeSidebarTab === 'docs' || activeSidebarTab === 'examples' || activeSidebarTab === 'hierarchy') && isSrcUrl) return;
      if (activeSidebarTab === 'source' && (isDocUrl || isExUrl)) return;
    }

    let targetUrl = url;
    if (!targetUrl) {
      if (activeSidebarTab === 'source') {
        targetUrl = currentSrcUrl;
      } else if (activeSidebarTab === 'examples' || activeSidebarTab === 'docs' || activeSidebarTab === 'hierarchy') {
        targetUrl = currentDocUrl;
      } else {
        targetUrl = currentDocUrl || currentSrcUrl;
      }
    }

    let foundActive = false;
    sidebarContent.querySelectorAll('.nav-item-link, .file-tree-item, .hierarchy-link').forEach(el => {
      const docHref = el.getAttribute('data-doc-href');
      const srcHref = el.getAttribute('data-src-href');
      const href = (activeSidebarTab === 'source') ? (srcHref || docHref) : (docHref || srcHref);

      const isMatch = urlsMatch(href, targetUrl);
      if (isMatch && !foundActive) {
        el.classList.add('active');
        const row = el.closest('.hierarchy-row');
        if (row) row.classList.add('active');
        foundActive = true;
        let p = el.parentElement;
        while (p && p !== sidebarContent) {
          if (p.classList.contains('hierarchy-children')) {
            p.classList.add('open');
            const parentNode = p.closest('.hierarchy-tree-node');
            if (parentNode) {
              parentNode.classList.remove('collapsed');
              const exp = parentNode.querySelector(':scope > .hierarchy-row > .hierarchy-expander');
              if (exp) exp.classList.add('open');
            }
          } else if (p.classList.contains('nav-group')) {
            p.classList.remove('collapsed');
          }
          p = p.parentElement;
        }
      } else {
        el.classList.remove('active');
        const row = el.closest('.hierarchy-row');
        if (row && !isMatch) row.classList.remove('active');
      }
    });

    updateSidebarToggleAllBtn();
  }

  // =========================================================================
  // Resizable Split View Divider
  // =========================================================================

  if (splitDivider) {
    let isDragging = false;
    const viewport = document.getElementById('app-viewport');
    const dividerWidth = 6;
    const minPaneWidth = 180; // matches CSS min-width

    function updateSplitPosition(clientX) {
      if (!viewport || !docPane || !srcPane) return;
      const rect = viewport.getBoundingClientRect();
      const totalWidth = rect.width;
      const minX = minPaneWidth;
      const maxX = totalWidth - minPaneWidth - dividerWidth;

      if (maxX <= minX) return;

      const rawX = clientX - rect.left;
      const clampedX = Math.max(minX, Math.min(maxX, rawX));
      const pct = (clampedX / totalWidth) * 100;

      docPane.style.flex = `0 0 ${pct}%`;
      docPane.style.width = `${pct}%`;
      srcPane.style.flex = `0 0 calc(${100 - pct}% - ${dividerWidth}px)`;
      srcPane.style.width = `calc(${100 - pct}% - ${dividerWidth}px)`;
    }

    splitDivider.addEventListener('mousedown', (e) => {
      e.preventDefault();
      isDragging = true;
      splitDivider.classList.add('active');
      document.body.classList.add('is-resizing');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    let rafPending = false;
    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      if (rafPending) return;
      rafPending = true;
      window.requestAnimationFrame(() => {
        updateSplitPosition(e.clientX);
        rafPending = false;
      });
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

    // Touch support for mobile / touch devices
    splitDivider.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        isDragging = true;
        splitDivider.classList.add('active');
        document.body.classList.add('is-resizing');
      }
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (!isDragging || e.touches.length !== 1) return;
      if (rafPending) return;
      rafPending = true;
      const clientX = e.touches[0].clientX;
      window.requestAnimationFrame(() => {
        updateSplitPosition(clientX);
        rafPending = false;
      });
    }, { passive: true });

    window.addEventListener('touchend', () => {
      if (isDragging) {
        isDragging = false;
        splitDivider.classList.remove('active');
        document.body.classList.remove('is-resizing');
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

  function adjustSearchInputHeight() {
    if (!searchInput) return;
    searchInput.style.height = 'auto';
    const newHeight = Math.min(Math.max(searchInput.scrollHeight, 26), 120);
    searchInput.style.height = `${newHeight}px`;
  }

  function syncModalDiffPillsVisibility() {
    const modalDiffSep = document.getElementById('modal-filter-diff-sep');
    const diffPills = document.querySelectorAll('.filter-pill-diff');
    const isExActive = searchFilterTypes.has('example');
    if (modalDiffSep) modalDiffSep.style.display = isExActive ? 'inline-block' : 'none';
    diffPills.forEach(p => {
      p.style.display = isExActive ? 'inline-flex' : 'none';
      if (!isExActive) {
        p.classList.remove('active');
        searchFilterTypes.delete(p.getAttribute('data-type'));
      }
    });
  }

  // Active Search Session State for seamless cross-result navigation
  const activeSearchSession = {
    query: '',
    mode: 'standard', // 'standard' | 'ai'
    results: [], // array of { item, ... }
    currentIndex: -1,
    viewedIndices: new Set(),
    isActive: false
  };

  // Recent Searches Manager (stored in localStorage)
  const RECENT_SEARCHES_KEY = 'uvm_recent_searches';
  const MAX_RECENT_SEARCHES = 8;

  function getRecentSearches() {
    try {
      const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
      if (!stored) return [];
      const parsed = JSON.parse(stored);
      if (!Array.isArray(parsed)) return [];
      return parsed.map(item => {
        if (typeof item === 'string') {
          return { query: item, mode: 'standard' };
        }
        return {
          query: item.query || '',
          mode: item.mode === 'ai' ? 'ai' : 'standard'
        };
      }).filter(item => item.query && item.query.trim().length > 0);
    } catch (e) {
      return [];
    }
  }

  function saveRecentSearch(query, mode) {
    const q = (query || '').trim();
    if (!q || q.length < 2) return;
    const m = mode === 'ai' ? 'ai' : (mode === 'standard' ? 'standard' : (modalAiEnabled ? 'ai' : 'standard'));
    try {
      let list = getRecentSearches();
      list = list.filter(item => item.query.toLowerCase() !== q.toLowerCase());
      list.unshift({ query: q, mode: m });
      if (list.length > MAX_RECENT_SEARCHES) list = list.slice(0, MAX_RECENT_SEARCHES);
      localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(list));
    } catch (e) { }
  }

  function removeRecentSearch(query, mode) {
    const q = (query || '').trim().toLowerCase();
    try {
      let list = getRecentSearches();
      list = list.filter(item => !(item.query.toLowerCase() === q && (!mode || item.mode === mode)));
      localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(list));
    } catch (e) { }
    renderRecentSearches();
  }

  function clearRecentSearches() {
    try {
      localStorage.removeItem(RECENT_SEARCHES_KEY);
    } catch (e) { }
    renderRecentSearches();
  }

  function renderRecentSearches() {
    if (!modalRecentSearches || !recentSearchesChips) return;
    const history = getRecentSearches();
    if (!history.length) {
      if (modalAiEnabled) {
        // En mode IA : afficher un état vide élégant pour que la section historique reste toujours visible
        recentSearchesChips.innerHTML = `
          <div class="recent-searches-empty" style="padding:1.25rem 1.25rem; text-align:center; color:var(--text-muted); font-size:0.825rem;">
            <span style="opacity:0.75;">Aucune recherche récente. Vos requêtes s'afficheront ici.</span>
          </div>`;
        modalRecentSearches.style.display = 'flex';
        if (modalSearchPrompts) modalSearchPrompts.style.display = 'flex';
        if (searchResults) searchResults.style.display = 'none';
      } else {
        modalRecentSearches.style.display = 'none';
        if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
        if (searchResults) {
          searchResults.style.display = 'block';
          if (!searchInput || !searchInput.value.trim()) {
            searchResults.innerHTML = `<li style="padding:3rem 1.5rem; text-align:center; color:var(--text-muted); font-size:0.875rem">
              <div style="font-size:1.75rem; margin-bottom:0.6rem; opacity:0.65;">🔍</div>
              <strong style="color:var(--text-main); font-size:0.95rem;">Type to search UVM documentation</strong><br>
              <span style="font-size:0.8rem; margin-top:0.35rem; display:inline-block; opacity:0.75;">Search 3,096 classes, methods, tasks, macros, files and interactive examples</span>
            </li>`;
          }
        }
      }
      return;
    }

    let html = '';
    history.forEach(item => {
      const isAi = item.mode === 'ai';
      html += `<div class="recent-search-row recent-search-chip" data-query="${escapeHtml(item.query)}" data-mode="${isAi ? 'ai' : 'standard'}" role="button" tabindex="0">
        <div class="recent-row-main">
          ${isAi ? `
            <svg class="recent-row-icon icon-ai" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
          ` : `
            <svg class="recent-row-icon icon-standard" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          `}
          <span class="recent-row-query">${escapeHtml(item.query)}</span>
          <span class="recent-mode-badge ${isAi ? 'badge-ai' : 'badge-standard'}">${isAi ? 'AI' : 'Standard'}</span>
        </div>
        <div class="recent-row-actions">
          <span class="recent-row-hint">Jump to search ↵</span>
          <button type="button" class="recent-row-remove" data-remove="${escapeHtml(item.query)}" data-mode="${isAi ? 'ai' : 'standard'}" title="Remove from history" aria-label="Remove '${escapeHtml(item.query)}' from history">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>`;
    });

    recentSearchesChips.innerHTML = html;
    modalRecentSearches.style.display = 'flex';
    if (searchResults) searchResults.style.display = 'none';

    if (modalAiEnabled) {
      if (modalSearchPrompts) modalSearchPrompts.style.display = 'flex';
    } else {
      if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
    }

    // Click on row to run search and activate corresponding mode
    recentSearchesChips.querySelectorAll('.recent-search-row').forEach(row => {
      row.addEventListener('click', (e) => {
        if (e.target.closest('.recent-row-remove')) return;
        const query = row.getAttribute('data-query');
        const mode = row.getAttribute('data-mode') || 'standard';

        // Switch to corresponding mode
        if (mode === 'ai') {
          if (!modalAiEnabled) {
            if (window.UVMRagEngine && !window.UVMRagEngine.hasConsent()) {
              openAiConsentModal();
              return;
            }
            toggleAiSearchMode(true, { skipSearch: true });
          }
        } else {
          if (modalAiEnabled) {
            toggleAiSearchMode(false, { skipSearch: true });
          }
        }

        if (searchInput) {
          searchInput.value = query;
          adjustSearchInputHeight();
          if (modalSearchClear) modalSearchClear.style.display = 'inline-flex';
          modalRecentSearches.style.display = 'none';
          if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
          if (searchResults) searchResults.style.display = 'block';
          searchInput.focus();
          executeSearch(query);
        }
      });
      row.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          row.click();
        }
      });
    });

    // Click on individual remove button
    recentSearchesChips.querySelectorAll('.recent-row-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const query = btn.getAttribute('data-remove');
        const mode = btn.getAttribute('data-mode');
        removeRecentSearch(query, mode);
      });
    });
  }

  function updateSearchPilotBar() {
    if (!searchNavBar) return;
    if (!activeSearchSession.isActive || !activeSearchSession.results || activeSearchSession.results.length === 0) {
      searchNavBar.style.display = 'none';
      return;
    }
    const total = activeSearchSession.results.length;
    const current = (activeSearchSession.currentIndex >= 0 && activeSearchSession.currentIndex < total)
      ? activeSearchSession.currentIndex + 1
      : 1;

    if (searchNavQuery) {
      searchNavQuery.textContent = activeSearchSession.query || 'Results';
      searchNavQuery.title = `Search query: "${activeSearchSession.query}" (${total} results)`;
    }
    if (searchNavBadge) {
      searchNavBadge.textContent = `${current} of ${total}`;
    }
    if (searchNavPrev) {
      searchNavPrev.disabled = activeSearchSession.currentIndex <= 0;
      searchNavPrev.classList.toggle('disabled', activeSearchSession.currentIndex <= 0);
    }
    if (searchNavNext) {
      searchNavNext.disabled = activeSearchSession.currentIndex >= total - 1;
      searchNavNext.classList.toggle('disabled', activeSearchSession.currentIndex >= total - 1);
    }
    searchNavBar.style.display = 'flex';
  }

  function closeSearchPilot() {
    if (searchNavBar) {
      searchNavBar.style.display = 'none';
    }
    activeSearchSession.isActive = false;
  }

  function navigateSearchResult(delta) {
    if (!activeSearchSession.isActive || !activeSearchSession.results || activeSearchSession.results.length === 0) return;
    const newIndex = activeSearchSession.currentIndex + delta;
    if (newIndex >= 0 && newIndex < activeSearchSession.results.length) {
      const entry = activeSearchSession.results[newIndex];
      const item = entry.item || entry;
      selectSearchResult(item, { index: newIndex, keepModalClosed: true });
    }
  }

  function openSearchModal(options = {}) {
    if (!searchModal) return;
    searchModal.classList.add('open');

    const shouldPreserve = options.preserveSession || (activeSearchSession.isActive && activeSearchSession.query);
    if (shouldPreserve && activeSearchSession.query) {
      searchSelectedIndex = -1;
      searchInput.value = activeSearchSession.query;
      adjustSearchInputHeight();
      if (modalSearchClear) modalSearchClear.style.display = 'inline-flex';
      if (modalRecentSearches) modalRecentSearches.style.display = 'none';
      if (searchResults) searchResults.style.display = 'block';
      searchInput.focus();
      searchInput.select();
      executeSearch(activeSearchSession.query);
    } else {
      searchInput.value = '';
      searchSelectedIndex = -1;
      adjustSearchInputHeight();
      if (modalSearchClear) modalSearchClear.style.display = 'none';
      if (modalSearchHeader) modalSearchHeader.classList.remove('regex-error');
      if (modalSearchRegex) modalSearchRegex.classList.remove('regex-error');

      // Context-aware filter selection: if user was browsing Examples, auto-select Example filter
      if (activeSidebarTab === 'examples') {
        searchFilterTypes.clear();
        searchFilterTypes.add('example');
        searchFilterPills.forEach(p => {
          p.classList.toggle('active', p.getAttribute('data-type') === 'example');
        });
      }
      syncModalDiffPillsVisibility();

      if (modalAiEnabled) {
        renderPromptChips();
        if (modalSearchPrompts) modalSearchPrompts.style.display = 'flex';
      } else {
        if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
      }
      renderRecentSearches();
      searchInput.focus();
      searchSelectedIndex = -1;
      executeSearch('');
    }
  }

  function closeSearchModal() {
    if (!searchModal) return;
    searchModal.classList.remove('open');
    if (modalAiLoading) modalAiLoading.style.display = 'none';
    if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
    if (searchResults) searchResults.style.display = 'block';
    if (modalRecentSearches) modalRecentSearches.style.display = 'none';
    if (window.UVMRagEngine) {
      window.UVMRagEngine.unloadPipeline();
    }
  }

  // RAG State & Helpers
  let modalAiEnabled = false;
  let activeAiSearchId = 0;
  let lastAiRawResults = null;
  let lastAiQuery = null;

  function renderStarRating(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
      stars += i <= rating ? '★' : '☆';
    }
    return stars;
  }

  function renderPromptChips() {
    if (!promptsChips || !window.UVMRagEngine) return;
    const prompts = window.UVMRagEngine.prompts || [];
    if (!prompts.length) {
      fetch('config/rag_prompts.json').then(r => r.ok ? r.json() : []).then(data => {
        if (window.UVMRagEngine) window.UVMRagEngine.prompts = data;
        renderPromptChips();
      }).catch(() => { });
      return;
    }

    let html = '';
    prompts.slice(0, 15).forEach(p => {
      html += `
            <button type="button" class="prompt-chip" data-query="${escapeHtml(p.query)}" title="${escapeHtml(p.category)} : cliquer pour poser cette question">
              <div class="prompt-chip-top">
                <span class="prompt-chip-cat">${escapeHtml(p.category)}</span>
                <span class="prompt-chip-icon">↗</span>
              </div>
              <span class="prompt-chip-text">${escapeHtml(p.query)}</span>
            </button>
          `;
    });
    promptsChips.innerHTML = html;
    promptsChips.querySelectorAll('.prompt-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const query = chip.getAttribute('data-query');
        if (searchInput) {
          saveRecentSearch(query, 'ai');
          searchInput.value = query;
          adjustSearchInputHeight();
          if (modalSearchClear) modalSearchClear.style.display = 'inline-flex';
          if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
          if (searchResults) searchResults.style.display = 'block';
          searchInput.focus();
          executeSearch(query);
        }
      });
    });
  }

  function renderAiModelList(container, isConsent) {
    if (!container || !window.UVMRagEngine) return;
    const models = window.UVMRagEngine.models || [];
    const currentId = window.UVMRagEngine.currentModelId;
    let html = '';

    models.forEach(m => {
      const isSelected = m.id === currentId;
      const recBadge = m.recommended ? `<span class="ai-badge-rec">Recommended</span>` : '';
      const radioName = isConsent ? 'consent-model-radio' : 'settings-model-radio';
      html += `
            <label class="ai-model-card ${isSelected ? 'selected' : ''}" data-model-id="${m.id}" tabindex="0" role="radio" aria-checked="${isSelected}">
              <input type="radio" name="${radioName}" value="${m.id}" class="ai-model-radio" ${isSelected ? 'checked' : ''}>
              <div class="ai-model-info">
                <div class="ai-model-header">
                  <span class="ai-model-name">${escapeHtml(m.name)}</span>
                  ${recBadge}
                </div>
                <div class="ai-model-desc">${escapeHtml(m.description)}</div>
                <div class="ai-model-metrics">
                  <span class="ai-metric-item"><strong>Speed:</strong> <span class="ai-stars">${renderStarRating(m.speedRating)}</span></span>
                  <span class="ai-metric-item"><strong>Accuracy:</strong> <span class="ai-stars">${renderStarRating(m.accuracyRating)}</span></span>
                  <span class="ai-metric-item"><strong>Size:</strong> ${escapeHtml(m.downloadSize)} (${escapeHtml(m.ramUsage)})</span>
                </div>
              </div>
            </label>
          `;
    });

    container.innerHTML = html;

    container.querySelectorAll('.ai-model-card').forEach(card => {
      const selectCard = () => {
        container.querySelectorAll('.ai-model-card').forEach(c => {
          c.classList.remove('selected');
          c.setAttribute('aria-checked', 'false');
        });
        card.classList.add('selected');
        card.setAttribute('aria-checked', 'true');
        const radio = card.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
        const modelId = card.getAttribute('data-model-id');
        window.UVMRagEngine.setModel(modelId);
        lastAiRawResults = null;
        lastAiQuery = null;
      };

      card.addEventListener('click', selectCard);
      card.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          selectCard();
        }
      });
    });
  }

  function updateCacheStatusUI() {
    if (!settingsCacheStatus || !window.UVMRagEngine) return;
    window.UVMRagEngine.getCacheInfo().then(({ count, sizeMB }) => {
      if (settingsCacheStatus) {
        settingsCacheStatus.textContent = sizeMB > 0 ? `Cached models storage: ~${sizeMB} MB (${count} files cached)` : 'No cached models';
      }
    }).catch(() => {
      if (settingsCacheStatus) settingsCacheStatus.textContent = 'Cache status unavailable';
    });
  }

  function openAiConsentModal() {
    if (!aiConsentModal) return;
    renderAiModelList(aiConsentModelList, true);
    aiConsentModal.style.display = 'flex';
    if (aiConsentConfirm) aiConsentConfirm.focus();
  }

  function closeAiConsentModal() {
    if (!aiConsentModal) return;
    aiConsentModal.style.display = 'none';
    if (searchInput) searchInput.focus();
  }

  function openSearchSettingsModal() {
    if (!searchSettingsModal) return;
    renderAiModelList(settingsModelList, false);
    if (settingsToggleHybrid && window.UVMRagEngine) {
      settingsToggleHybrid.checked = window.UVMRagEngine.isHybrid;
    }
    if (settingsToggleAutoSemantic && window.UVMRagEngine) {
      settingsToggleAutoSemantic.checked = window.UVMRagEngine.isAutoSemantic;
    }
    if (window.UVMRagEngine) {
      const mode = window.UVMRagEngine.displayMode;
      if (settingsModeConsolidated) settingsModeConsolidated.checked = (mode !== 'mixed');
      if (settingsModeMixed) settingsModeMixed.checked = (mode === 'mixed');
    }
    updateCacheStatusUI();
    searchSettingsModal.style.display = 'flex';
    if (searchSettingsDone) searchSettingsDone.focus();
  }

  function closeSearchSettingsModal() {
    if (!searchSettingsModal) return;
    searchSettingsModal.style.display = 'none';
    if (searchInput) searchInput.focus();
  }

  function toggleAiSearchMode(forceState, options = {}) {
    const query = searchInput ? searchInput.value.trim() : '';

    if (forceState !== undefined) {
      modalAiEnabled = forceState;
    } else {
      modalAiEnabled = !modalAiEnabled;
    }

    if (modalSearchAi) {
      modalSearchAi.classList.toggle('active', modalAiEnabled);
      modalSearchAi.setAttribute('aria-pressed', modalAiEnabled ? 'true' : 'false');
    }

    if (searchInput) {
      if (modalAiEnabled) {
        searchInput.placeholder = "Posez votre question en langage naturel (ex: 'how to pass vifs with config db')...";
      } else {
        searchInput.placeholder = "Search classes, functions, tasks, macros, files...";
      }
    }

    if (modalAiEnabled && !query) {
      renderPromptChips();
      if (modalSearchPrompts) modalSearchPrompts.style.display = 'flex';
      renderRecentSearches();
      if (searchResults) searchResults.style.display = 'none';
    } else if (!modalAiEnabled && !query) {
      if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
      renderRecentSearches();
    }

    if (!options.skipSearch) {
      executeSearch(searchInput ? searchInput.value : '');
    }
  }

  if (modalSearchAi) {
    modalSearchAi.addEventListener('click', () => {
      if (!modalAiEnabled && window.UVMRagEngine && !window.UVMRagEngine.hasConsent()) {
        openAiConsentModal();
      } else {
        toggleAiSearchMode();
      }
    });
  }

  if (modalSearchSettings) {
    modalSearchSettings.addEventListener('click', openSearchSettingsModal);
  }

  if (aiConsentClose) aiConsentClose.addEventListener('click', closeAiConsentModal);
  if (aiConsentCancel) aiConsentCancel.addEventListener('click', closeAiConsentModal);
  if (aiConsentConfirm) {
    aiConsentConfirm.addEventListener('click', () => {
      if (window.UVMRagEngine) {
        window.UVMRagEngine.grantConsent();
      }
      closeAiConsentModal();
      toggleAiSearchMode(true);
    });
  }

  if (searchSettingsClose) searchSettingsClose.addEventListener('click', closeSearchSettingsModal);
  if (searchSettingsDone) searchSettingsDone.addEventListener('click', closeSearchSettingsModal);
  if (settingsToggleHybrid) {
    settingsToggleHybrid.addEventListener('change', (e) => {
      if (window.UVMRagEngine) window.UVMRagEngine.setHybrid(e.target.checked);
      lastAiRawResults = null;
      lastAiQuery = null;
      executeSearch(searchInput ? searchInput.value : '');
    });
  }
  if (settingsToggleAutoSemantic) {
    settingsToggleAutoSemantic.addEventListener('change', (e) => {
      if (window.UVMRagEngine) window.UVMRagEngine.setAutoSemantic(e.target.checked);
    });
  }
  if (settingsModeConsolidated) {
    settingsModeConsolidated.addEventListener('change', (e) => {
      if (e.target.checked && window.UVMRagEngine) {
        window.UVMRagEngine.setDisplayMode('consolidated');
        lastAiRawResults = null;
        lastAiQuery = null;
        if (modalAiEnabled && searchInput) executeSearch(searchInput.value);
      }
    });
  }
  if (settingsModeMixed) {
    settingsModeMixed.addEventListener('change', (e) => {
      if (e.target.checked && window.UVMRagEngine) {
        window.UVMRagEngine.setDisplayMode('mixed');
        lastAiRawResults = null;
        lastAiQuery = null;
        if (modalAiEnabled && searchInput) executeSearch(searchInput.value);
      }
    });
  }
  if (settingsClearCache) {
    settingsClearCache.addEventListener('click', async () => {
      if (confirm('Are you sure you want to clear locally cached AI models?')) {
        if (window.UVMRagEngine) {
          await window.UVMRagEngine.clearCache();
          updateCacheStatusUI();
        }
      }
    });
  }

  if (searchTrigger) {
    searchTrigger.addEventListener('click', () => openSearchModal({ preserveSession: true }));
  }

  window.addEventListener('keydown', (e) => {
    // Search Pilot navigation shortcuts (Alt+[ and Alt+])
    if (e.altKey && (e.key === '[' || e.code === 'BracketLeft')) {
      e.preventDefault();
      navigateSearchResult(-1);
      return;
    }
    if (e.altKey && (e.key === ']' || e.code === 'BracketRight')) {
      e.preventDefault();
      navigateSearchResult(1);
      return;
    }

    // Handle shortcuts when AI Consent Modal is open
    if (aiConsentModal && aiConsentModal.style.display !== 'none') {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeAiConsentModal();
        return;
      }
    }

    // Handle shortcuts when Search Settings Modal is open
    if (searchSettingsModal && searchSettingsModal.style.display !== 'none') {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeSearchSettingsModal();
        return;
      }
    }

    // Handle shortcuts when Image Zoom Modal is open
    if (imageZoomModal && imageZoomModal.classList.contains('open')) {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeImageZoomModal();
        return;
      } else if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        setZoom(currentZoom * 1.25);
        return;
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        setZoom(currentZoom * 0.8);
        return;
      } else if (e.key === '0') {
        e.preventDefault();
        fitImageToViewport();
        return;
      } else if (e.key === '1') {
        e.preventDefault();
        currentZoom = 1.0;
        panX = 0;
        panY = 0;
        updateImageTransform();
        return;
      }
    }

    // Open on '/' or 'Ctrl+K' / 'Cmd+K'
    if ((e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') ||
      (e.key === 'k' && (e.ctrlKey || e.metaKey))) {
      e.preventDefault();
      openSearchModal({ preserveSession: true });
    } else if (e.key === 'Escape' && searchModal && searchModal.classList.contains('open')) {
      if (searchInput && searchInput.value.length > 0) {
        e.preventDefault();
        searchInput.value = '';
        adjustSearchInputHeight();
        if (modalSearchClear) modalSearchClear.style.display = 'none';
        if (modalSearchHeader) modalSearchHeader.classList.remove('regex-error');
        if (modalSearchRegex) modalSearchRegex.classList.remove('regex-error');
        executeSearch('');
      } else {
        closeSearchModal();
      }
    }
  });

  // Close modal ONLY when mousedown AND mouseup both occur outside on the backdrop
  // Prevents accidental closing when user selects text or drags cursor outside
  function bindModalOutsideClick(modalElement, closeFn) {
    if (!modalElement) return;
    let isMouseDownOnBackdrop = false;
    modalElement.addEventListener('mousedown', (e) => {
      isMouseDownOnBackdrop = (e.target === modalElement);
    });
    modalElement.addEventListener('mouseup', (e) => {
      if (isMouseDownOnBackdrop && e.target === modalElement) {
        closeFn();
      }
      isMouseDownOnBackdrop = false;
    });
  }

  bindModalOutsideClick(searchModal, closeSearchModal);
  bindModalOutsideClick(aiConsentModal, closeAiConsentModal);
  bindModalOutsideClick(searchSettingsModal, closeSearchSettingsModal);

  // Search Pilot bar and history event bindings
  if (searchNavPrev) {
    searchNavPrev.addEventListener('click', (e) => {
      e.stopPropagation();
      navigateSearchResult(-1);
    });
  }
  if (searchNavNext) {
    searchNavNext.addEventListener('click', (e) => {
      e.stopPropagation();
      navigateSearchResult(1);
    });
  }
  if (searchNavList) {
    searchNavList.addEventListener('click', (e) => {
      e.stopPropagation();
      openSearchModal({ preserveSession: true });
    });
  }
  if (searchNavReopenBtn) {
    searchNavReopenBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      openSearchModal({ preserveSession: true });
    });
    searchNavReopenBtn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openSearchModal({ preserveSession: true });
      }
    });
  }
  if (searchNavClose) {
    searchNavClose.addEventListener('click', (e) => {
      e.stopPropagation();
      closeSearchPilot();
    });
  }
  if (recentSearchesClear) {
    recentSearchesClear.addEventListener('click', (e) => {
      e.stopPropagation();
      clearRecentSearches();
    });
  }

  if (modalSearchClear) {
    modalSearchClear.addEventListener('click', () => {
      if (searchInput) {
        searchInput.value = '';
        adjustSearchInputHeight();
        modalSearchClear.style.display = 'none';
        if (modalSearchHeader) modalSearchHeader.classList.remove('regex-error');
        if (modalSearchRegex) modalSearchRegex.classList.remove('regex-error');
        searchInput.focus();
        executeSearch('');
      }
    });
  }

  if (modalSearchCase) {
    modalSearchCase.addEventListener('click', () => {
      modalCaseSensitive = !modalCaseSensitive;
      modalSearchCase.classList.toggle('active', modalCaseSensitive);
      executeSearch(searchInput ? searchInput.value : '');
    });
  }

  if (modalSearchRegex) {
    modalSearchRegex.addEventListener('click', () => {
      modalRegexEnabled = !modalRegexEnabled;
      modalSearchRegex.classList.toggle('active', modalRegexEnabled);
      executeSearch(searchInput ? searchInput.value : '');
    });
  }

  searchFilterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      handleMultiFilterPillClick(pill, searchFilterPills, searchFilterTypes, () => {
        syncModalDiffPillsVisibility();
        executeSearch(searchInput ? searchInput.value : '');
      });
    });
  });

  if (searchInput) {
    const debouncedExecuteSearch = debounce((val) => {
      executeSearch(val);
    }, 150);

    searchInput.addEventListener('input', (e) => {
      adjustSearchInputHeight();
      if (modalSearchClear) {
        modalSearchClear.style.display = e.target.value.length > 0 ? 'inline-flex' : 'none';
      }
      debouncedExecuteSearch(e.target.value);
    });

    searchInput.addEventListener('keydown', (e) => {
      const items = searchResults.querySelectorAll('.search-result-item');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (items.length > 0) {
          searchSelectedIndex = (searchSelectedIndex + 1) % items.length;
          updateSelectedSearchItem(items);
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (items.length > 0) {
          searchSelectedIndex = (searchSelectedIndex - 1 + items.length) % items.length;
          updateSelectedSearchItem(items);
        }
      } else if (e.key === 'Enter') {
        if (e.shiftKey) {
          setTimeout(adjustSearchInputHeight, 0);
          return;
        }
        e.preventDefault();
        const val = searchInput ? searchInput.value.trim() : '';

        if (searchSelectedIndex === -1) {
          // Premier appui sur Entrée : sélectionne le premier résultat en le mettant en évidence
          // C'est à ce moment que la requête est mémorisée par l'historique
          if (items.length > 0) {
            searchSelectedIndex = 0;
            updateSelectedSearchItem(items);
            if (val.length >= 2) {
              saveRecentSearch(val, modalAiEnabled ? 'ai' : 'standard');
            }
          } else if (val.length >= 2) {
            // Validation immédiate par Entrée (ex: mode IA ou avant la fin du debounce)
            saveRecentSearch(val, modalAiEnabled ? 'ai' : 'standard');
            debouncedExecuteSearch.cancel();
            executeSearch(val);
          }
        } else if (searchSelectedIndex >= 0 && searchSelectedIndex < filteredSearchResults.length) {
          // Second appui sur Entrée (ou déjà sélectionné) : validation et ouverture
          if (val.length >= 2) {
            saveRecentSearch(val, modalAiEnabled ? 'ai' : 'standard');
          }
          const entry = filteredSearchResults[searchSelectedIndex];
          const item = entry.item || entry;
          selectSearchResult(item, { index: searchSelectedIndex });
        }
      } else if (e.key === 'r' && e.altKey) {
        e.preventDefault();
        modalRegexEnabled = !modalRegexEnabled;
        if (modalSearchRegex) modalSearchRegex.classList.toggle('active', modalRegexEnabled);
        executeSearch(searchInput.value);
      } else if (e.key === 'c' && e.altKey) {
        e.preventDefault();
        modalCaseSensitive = !modalCaseSensitive;
        if (modalSearchCase) modalSearchCase.classList.toggle('active', modalCaseSensitive);
        executeSearch(searchInput.value);
      } else if (e.key === 'n' && e.altKey) {
        e.preventDefault();
        if (!modalAiEnabled && window.UVMRagEngine && !window.UVMRagEngine.hasConsent()) {
          openAiConsentModal();
        } else {
          toggleAiSearchMode();
        }
      } else if (e.key === 'Escape') {
        if (searchInput.value.length > 0) {
          e.preventDefault();
          e.stopPropagation();
          searchInput.value = '';
          adjustSearchInputHeight();
          if (modalSearchClear) modalSearchClear.style.display = 'none';
          if (modalSearchHeader) modalSearchHeader.classList.remove('regex-error');
          if (modalSearchRegex) modalSearchRegex.classList.remove('regex-error');
          executeSearch('');
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

  async function executeSearch(query) {
    if (!searchResults) return;

    // Auto-detect natural language if setting is enabled and not yet in AI mode
    if (!modalAiEnabled && window.UVMRagEngine && window.UVMRagEngine.isAutoSemantic && window.UVMRagEngine.hasConsent()) {
      const words = (query || '').trim().split(/\s+/);
      if (words.length >= 3 && /^(how|what|why|where|can|is|when|comment|pourquoi|quelle?|est)/i.test(words[0])) {
        toggleAiSearchMode(true);
        return;
      }
    }

    // ==========================================
    // Mode 1: AI / Natural Language Semantic Search
    // ==========================================
    if (modalAiEnabled) {
      const trimmed = (query || '').trim();
      if (!trimmed) {
        lastAiRawResults = null;
        lastAiQuery = null;
        renderPromptChips();
        if (modalSearchPrompts) modalSearchPrompts.style.display = 'flex';
        renderRecentSearches();
        searchResults.innerHTML = '';
        if (searchResults) searchResults.style.display = 'none';
        filteredSearchResults = [];
        searchSelectedIndex = -1;
        return;
      }

      if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
      if (searchResults) searchResults.style.display = 'block';
      if (modalRecentSearches) modalRecentSearches.style.display = 'none';

      let results = null;

      // Fast cache path: if the query didn't change and we already computed RAG vectors, filter immediately
      if (trimmed === lastAiQuery && lastAiRawResults !== null) {
        results = lastAiRawResults;
      } else {
        const searchId = ++activeAiSearchId;

        // Show progress / loading state
        if (modalAiLoading) {
          modalAiLoading.style.display = 'flex';
          if (aiLoadingText) aiLoadingText.textContent = "Computing semantic similarity...";
          if (aiLoadingPct) aiLoadingPct.textContent = "";
          if (aiLoadingBarFill) aiLoadingBarFill.style.width = "30%";
        }

        try {
          results = await window.UVMRagEngine.search(trimmed, {
            topK: 40,
            onProgress: (prog) => {
              if (searchId !== activeAiSearchId) return;
              if (modalAiLoading) modalAiLoading.style.display = 'flex';
              if (aiLoadingText && prog.message) aiLoadingText.textContent = prog.message;
              if (aiLoadingPct && prog.progress !== undefined) aiLoadingPct.textContent = `${prog.progress}%`;
              if (aiLoadingBarFill && prog.progress !== undefined) aiLoadingBarFill.style.width = `${prog.progress}%`;
            }
          });

          if (searchId !== activeAiSearchId) return; // Discard superseded search
          if (modalAiLoading) modalAiLoading.style.display = 'none';

          lastAiRawResults = results;
          lastAiQuery = trimmed;
        } catch (err) {
          console.error('[RAG] Search error:', err);
          if (modalAiLoading) modalAiLoading.style.display = 'none';
          searchResults.innerHTML = `<li style="padding:1.5rem; text-align:center; color:#ef4444; font-size:0.875rem">
                <strong>AI Search Error</strong><br>
                <span style="font-size:0.775rem; color:var(--text-muted)">${escapeHtml(err.message)}</span>
              </li>`;
          return;
        }
      }

      // Filter results by active pills using isRagResultAllowed
      const filtered = results.filter(r => isRagResultAllowed(r, searchFilterTypes));

      filteredSearchResults = filtered.map(r => ({
        item: {
          name: r.title,
          type: r.targetType || r.type || 'class',
          category: r.category,
          doc: r.targetUrl || r.chunk.url,
          src: (typeof UVM_DATA !== 'undefined' && UVM_DATA.docToSrc) ? UVM_DATA.docToSrc[(r.targetUrl || r.chunk.url).split('#')[0]] : null,
          desc: r.snippet
        },
        score: r.score,
        matchPct: r.matchPct,
        snippet: r.snippet,
        chunk: r.chunk,
        targetUrl: r.targetUrl,
        targetSections: r.targetSections || [],
        targetSectionTitle: r.targetSectionTitle,
        targetType: r.targetType,
        highlightedTitle: r.highlightedTitle,
        title: r.title,
        breadcrumb: r.breadcrumb,
        type: r.type
      }));

      searchSelectedIndex = -1;
      activeSearchSession.query = trimmed;
      activeSearchSession.mode = 'ai';
      activeSearchSession.results = filteredSearchResults;

      if (filteredSearchResults.length === 0) {
        const filterLabels = Array.from(searchFilterTypes).filter(t => t !== 'all');
        const filterNotice = filterLabels.length > 0 ? ` for filter [${filterLabels.join(', ')}]` : '';
        searchResults.innerHTML = `<li style="padding:2rem; text-align:center; color:var(--text-muted); font-size:0.875rem">
              No semantic matches found${filterNotice}.<br>
              <span style="font-size:0.8rem; margin-top:0.35rem; display:inline-block;">Try selecting "All" or rephrasing your question.</span>
            </li>`;
        return;
      }

      let html = '';
      filteredSearchResults.forEach((res, idx) => {
        const pct = res.matchPct;
        const badgeClass = pct >= 80 ? 'rag-match-high' : (pct >= 65 ? 'rag-match-med' : 'rag-match-low');

        let displayType = res.targetType || res.type || 'class';
        if (searchFilterTypes.has('example') || (res.targetUrl && res.targetUrl.includes('examples_view/'))) {
          displayType = 'example';
        } else if (searchFilterTypes.has('class') && (res.type === 'class' || res.type === 'overview')) {
          displayType = 'class';
        } else if (searchFilterTypes.has('macro') && (res.type === 'macro' || (res.targetSections && res.targetSections.some(s => s.type === 'macro')))) {
          displayType = 'macro';
        } else if (searchFilterTypes.has('task')) {
          displayType = 'task';
        } else if (searchFilterTypes.has('function')) {
          displayType = 'function';
        } else if (displayType === 'method') {
          displayType = 'function';
        }

        const typeBadgeClass = displayType === 'class' ? 'badge-class' :
          (displayType === 'macro' ? 'badge-macro' :
            (displayType === 'function' ? 'badge-function' :
              (displayType === 'task' ? 'badge-task' :
                (displayType === 'example' ? 'badge-example' :
                  (displayType === 'method' ? 'badge-method' : 'badge-file')))));

        let sectionsPillsHtml = '';
        if (res.targetSections && res.targetSections.length > 0) {
          sectionsPillsHtml = `<div class="rag-sections-list">
                ${res.targetSections.map(s => {
            const isIntro = s.isIntro;
            const pillClass = isIntro ? 'rag-section-pill intro-pill' : 'rag-section-pill';
            const pillLabel = isIntro ? '📖 Intro' : `🎯 ${escapeHtml(s.title)}`;
            return `<button type="button" class="${pillClass}" data-section-url="${escapeHtml(s.url)}" title="Jump directly to: ${escapeHtml(s.title)}">${pillLabel}</button>`;
          }).join('')}
              </div>`;
        } else if (res.targetSectionTitle) {
          sectionsPillsHtml = `<span class="rag-section-badge" title="Target section in this document">🎯 Section: ${escapeHtml(res.targetSectionTitle)}</span>`;
        }

        const isCurrent = (activeSearchSession.isActive && activeSearchSession.currentIndex === idx);
        const isViewed = activeSearchSession.viewedIndices.has(idx);
        const isSelected = (searchSelectedIndex >= 0 && searchSelectedIndex === idx);

        const itemClasses = ['search-result-item'];
        if (isCurrent) itemClasses.push('current-result');
        if (isSelected) itemClasses.push('selected');
        if (isViewed) itemClasses.push('viewed');

        const viewedBadge = isViewed ? `<span class="res-viewed-icon" title="Viewed in this session" aria-label="Viewed">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </span>` : '';

        html += `<li class="${itemClasses.join(' ')}" data-index="${idx}">
              <div class="res-main">
                <div class="res-title-row" style="display:flex; align-items:center; gap:0.4rem; flex-wrap:wrap;">
                  <span style="color:var(--text-muted); font-size:0.775rem;">${escapeHtml(res.breadcrumb)}</span>
                </div>
                <div class="rag-res-title" style="font-weight:600; font-size:0.925rem; color:var(--text-main); margin-top:0.15rem; display:flex; align-items:center;">
                  <span>${res.highlightedTitle || escapeHtml(res.title)}</span>
                  ${viewedBadge}
                </div>
                ${sectionsPillsHtml}
                <div class="rag-snippet">${res.snippet}</div>
              </div>
              <div style="display:flex; flex-direction:column; align-items:flex-end; gap:0.35rem; flex-shrink:0;">
                <span class="rag-match-badge ${badgeClass}">${pct}% match</span>
                <span class="res-badge ${typeBadgeClass}">${displayType}</span>
              </div>
            </li>`;
      });

      searchResults.innerHTML = html;


      // Bind section pills
      searchResults.querySelectorAll('.rag-section-pill').forEach(pill => {
        pill.addEventListener('click', (e) => {
          e.stopPropagation();
          const targetUrl = pill.getAttribute('data-section-url');
          const parentItem = pill.closest('.search-result-item');
          const idx = parentItem ? parseInt(parentItem.getAttribute('data-index'), 10) : 0;
          const baseItem = filteredSearchResults[idx].item;
          selectSearchResult({
            name: baseItem.name,
            category: baseItem.category,
            type: baseItem.type,
            doc: targetUrl,
            src: baseItem.src,
            desc: baseItem.desc
          }, { index: idx });
        });
      });

      // Bind main result card
      searchResults.querySelectorAll('.search-result-item').forEach(el => {
        el.addEventListener('click', () => {
          const idx = parseInt(el.getAttribute('data-index'), 10);
          selectSearchResult(filteredSearchResults[idx].item, { index: idx });
        });
      });

      return;
    }

    // ==========================================
    // Mode 2: Standard Exact / Regex / Case Search
    // ==========================================
    if (modalSearchPrompts) modalSearchPrompts.style.display = 'none';
    if (modalAiLoading) modalAiLoading.style.display = 'none';

    const trimmedStandard = (query || '').trim();
    if (!trimmedStandard) {
      if (searchResults) searchResults.innerHTML = '';
      filteredSearchResults = [];
      searchSelectedIndex = -1;
      renderRecentSearches();
      return;
    }

    if (modalRecentSearches) modalRecentSearches.style.display = 'none';
    if (searchResults) searchResults.style.display = 'block';

    if (typeof UVM_DATA === 'undefined') {
      searchResults.innerHTML = `<li style="padding:1.5rem; text-align:center; color:var(--text-muted, #64748b); font-size:0.875rem">
            <strong>Search index not available</strong><br>
            <span style="font-size:0.775rem;">Run <code>python scripts/build_docs.py --search-only</code> to generate search data.</span>
          </li>`;
      return;
    }
    const items = UVM_DATA.searchIndex || [];
    const matcher = getQueryMatcher(query, modalRegexEnabled, modalCaseSensitive, modalSearchHeader);

    if (modalSearchRegex) {
      modalSearchRegex.classList.toggle('regex-error', matcher && matcher.type === 'regex' && !matcher.valid);
    }

    filteredSearchResults = [];
    if (matcher && matcher.type === 'regex' && !matcher.valid) {
      searchResults.innerHTML = `<li style="padding:1.5rem; text-align:center; color:#ef4444; font-size:0.875rem">
            <strong>Invalid Regular Expression</strong><br>
            <span style="font-size:0.775rem; color:var(--text-muted)">${escapeHtml(matcher.error)}</span>
          </li>`;
      searchSelectedIndex = -1;
      return;
    }

    items.forEach(item => {
      if (!isItemTypeAllowed(item.type, searchFilterTypes)) {
        return;
      }
      if (item.type === 'example') {
        if (searchFilterTypes.has('beginner') || searchFilterTypes.has('intermediate') || searchFilterTypes.has('advanced')) {
          const diff = (item.difficulty || '').toLowerCase();
          let matchDiff = false;
          ['beginner', 'intermediate', 'advanced'].forEach(d => {
            if (searchFilterTypes.has(d) && diff === d) {
              matchDiff = true;
            }
          });
          if (!matchDiff) return;
        }
      }
      const res = matchSymbolItem(item, matcher);
      if (res.match) {
        filteredSearchResults.push({ item, score: res.score });
      }
    });

    filteredSearchResults.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      const aname = (a.item.name || '').toLowerCase();
      const bname = (b.item.name || '').toLowerCase();
      const aIsMethod = a.item.type === 'function' || a.item.type === 'task' || a.item.type === 'method';
      const bIsMethod = b.item.type === 'function' || b.item.type === 'task' || b.item.type === 'method';
      if (a.item.type === 'class' && bIsMethod && aname === bname) return -1;
      if (b.item.type === 'class' && aIsMethod && aname === bname) return 1;
      return aname.localeCompare(bname);
    });

    const displayResults = filteredSearchResults.slice(0, 80);
    searchSelectedIndex = -1;
    activeSearchSession.query = query;
    activeSearchSession.mode = 'standard';
    activeSearchSession.results = displayResults;

    let html = '';
    displayResults.forEach(({ item }, idx) => {
      const badgeClass = item.type === 'class' ? 'badge-class' :
        (item.type === 'macro' ? 'badge-macro' :
          (item.type === 'function' ? 'badge-function' :
            (item.type === 'task' ? 'badge-task' :
              (item.type === 'example' ? 'badge-example' :
                (item.type === 'method' ? 'badge-method' : 'badge-file')))));

      const isMethodLike = item.type === 'function' || item.type === 'task' || item.type === 'method';
      const categoryTag = item.category && isMethodLike ?
        `<span style="color:var(--text-muted); font-size:0.8rem; margin-right:0.35rem">${highlightMatch(item.category, matcher)} ::</span>` : '';

      const isCurrent = (activeSearchSession.isActive && activeSearchSession.currentIndex === idx);
      const isViewed = activeSearchSession.viewedIndices.has(idx);
      const isSelected = (searchSelectedIndex >= 0 && searchSelectedIndex === idx);

      const itemClasses = ['search-result-item'];
      if (isCurrent) itemClasses.push('current-result');
      if (isSelected) itemClasses.push('selected');
      if (isViewed) itemClasses.push('viewed');

      const viewedBadge = isViewed ? `<span class="res-viewed-icon" title="Viewed in this session" aria-label="Viewed">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      </span>` : '';

      html += `<li class="${itemClasses.join(' ')}" data-index="${idx}">
            <div class="res-main">
              <div class="res-title-row" style="display:flex; align-items:center;">
                ${categoryTag}
                <span class="res-name">${highlightMatch(item.name, matcher)}</span>
                ${viewedBadge}
              </div>
              <span class="res-desc">${highlightMatch(item.desc || '', matcher)}</span>
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
        selectSearchResult(displayResults[idx].item, { index: idx });
      });
    });
  }

  function selectSearchResult(item, options = {}) {
    if (!item) return;
    if (!options.keepModalClosed) {
      closeSearchModal();
    }

    // Update session tracking
    if (options.index !== undefined && options.index >= 0) {
      activeSearchSession.currentIndex = options.index;
    } else if (activeSearchSession.results && activeSearchSession.results.length > 0) {
      const foundIdx = activeSearchSession.results.findIndex(r => {
        const it = r.item || r;
        return it.name === item.name && (it.doc === item.doc || it.src === item.src);
      });
      if (foundIdx !== -1) {
        activeSearchSession.currentIndex = foundIdx;
      }
    }
    // No result should remain selected in the search results list
    searchSelectedIndex = -1;
    if (activeSearchSession.currentIndex >= 0) {
      activeSearchSession.viewedIndices.add(activeSearchSession.currentIndex);
    }
    activeSearchSession.isActive = true;

    const qToSave = activeSearchSession.query || (searchInput ? searchInput.value.trim() : '');
    if (qToSave && qToSave.length >= 2) {
      saveRecentSearch(qToSave, activeSearchSession.mode || (modalAiEnabled ? 'ai' : 'standard'));
    }

    updateSearchPilotBar();

    const isExample = (item.type === 'example' || (item.doc && item.doc.includes('examples_view/')));

    if (currentMode === 'split') {
      if (item.doc) {
        currentDocUrl = isExample ? normalizeExampleUrl(item.doc) : normalizeDocUrl(item.doc);
        setFrameSrc(docFrame, currentDocUrl);
        updateDocTitle(currentDocUrl);
      }
      if (item.src && !item.src.includes('examples_view/')) {
        currentSrcUrl = normalizeSrcUrl(item.src);
        setFrameSrc(srcFrame, currentSrcUrl);
        updateSrcTitle(currentSrcUrl);
      } else if (item.doc) {
        if (isExample) {
          const exClean = currentDocUrl.replace(/^examples_view\//, '');
          if (typeof UVM_DATA !== 'undefined' && UVM_DATA.exampleToSrc && UVM_DATA.exampleToSrc[exClean]) {
            currentSrcUrl = UVM_DATA.exampleToSrc[exClean];
            setFrameSrc(srcFrame, currentSrcUrl);
            updateSrcTitle(currentSrcUrl);
          }
        } else {
          const docClean = currentDocUrl.replace(/^docs_view\//, '');
          if (typeof UVM_DATA !== 'undefined' && UVM_DATA.docToSrc && UVM_DATA.docToSrc[docClean]) {
            currentSrcUrl = UVM_DATA.docToSrc[docClean];
            setFrameSrc(srcFrame, currentSrcUrl);
            updateSrcTitle(currentSrcUrl);
          }
        }
      }
      updateHash();
      highlightActiveSidebar(item.doc || item.src);
      if (isExample) {
        switchSidebarTab('examples');
      }
    } else {
      if (isExample) {
        window.openExampleView(item.doc);
      } else if (item.doc) {
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
  // Image Zoom Lightbox Controller
  // =========================================================================

  function updateImageTransform() {
    if (!imageModalStage) return;
    imageModalStage.style.transform = `translate(${panX}px, ${panY}px) scale(${currentZoom})`;
    if (imageZoomLevel) {
      imageZoomLevel.textContent = `${Math.round(currentZoom * 100)}%`;
    }
  }

  function setZoom(newZoom, centerX = null, centerY = null) {
    const clamped = Math.max(0.2, Math.min(5.0, newZoom));
    if (centerX !== null && centerY !== null && imageModalViewport) {
      const rect = imageModalViewport.getBoundingClientRect();
      const vx = centerX - rect.left - rect.width / 2;
      const vy = centerY - rect.top - rect.height / 2;
      const ratio = clamped / currentZoom;
      panX = vx - (vx - panX) * ratio;
      panY = vy - (vy - panY) * ratio;
    }
    currentZoom = clamped;
    updateImageTransform();
  }

  function fitImageToViewport() {
    if (!imageModalImg || !imageModalViewport) return;
    const naturalW = imageModalImg.naturalWidth || 600;
    const naturalH = imageModalImg.naturalHeight || 400;
    const vpW = imageModalViewport.clientWidth || 800;
    const vpH = imageModalViewport.clientHeight || 600;

    const availW = Math.max(100, vpW - 80);
    const availH = Math.max(100, vpH - 80);

    const scaleX = availW / naturalW;
    const scaleY = availH / naturalH;
    let targetScale = Math.min(scaleX, scaleY);
    if (targetScale > 1.5) targetScale = 1.5;
    if (targetScale < 0.25) targetScale = 0.25;

    fitZoom = targetScale;
    currentZoom = targetScale;
    panX = 0;
    panY = 0;
    updateImageTransform();
  }

  function openImageZoomModal(src, title) {
    if (!imageZoomModal || !imageModalImg) return;
    const diagramTitle = title || 'UVM Diagram';
    if (imageModalTitle) {
      imageModalTitle.textContent = diagramTitle;
    }
    const modalCaption = document.getElementById('image-modal-caption');
    if (modalCaption) {
      modalCaption.textContent = diagramTitle;
    }
    imageModalImg.src = src;
    imageModalImg.onload = () => {
      fitImageToViewport();
    };
    if (imageModalImg.complete) {
      fitImageToViewport();
    }
    imageZoomModal.style.display = 'flex';
    imageZoomModal.style.pointerEvents = 'auto';
    void imageZoomModal.offsetWidth;
    imageZoomModal.classList.add('open');
    imageZoomModal.setAttribute('aria-hidden', 'false');
  }

  function closeImageZoomModal() {
    if (!imageZoomModal) return;
    imageZoomModal.classList.remove('open');
    imageZoomModal.setAttribute('aria-hidden', 'true');
    imageZoomModal.style.pointerEvents = 'none';
    imageZoomModal.style.display = 'none';
    isPanning = false;
    if (imageModalViewport) {
      imageModalViewport.classList.remove('is-dragging');
    }
    if (document.activeElement && imageZoomModal.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    if (imageModalImg) {
      imageModalImg.src = '';
    }
  }

  window.openImageZoomModal = openImageZoomModal;
  window.closeImageZoomModal = closeImageZoomModal;

  if (imageZoomInBtn) {
    imageZoomInBtn.addEventListener('click', () => setZoom(currentZoom * 1.25));
  }
  if (imageZoomOutBtn) {
    imageZoomOutBtn.addEventListener('click', () => setZoom(currentZoom * 0.8));
  }
  if (imageZoomFitBtn) {
    imageZoomFitBtn.addEventListener('click', () => fitImageToViewport());
  }
  if (imageZoomActualBtn) {
    imageZoomActualBtn.addEventListener('click', () => {
      currentZoom = 1.0;
      panX = 0;
      panY = 0;
      updateImageTransform();
    });
  }
  if (imageModalCloseBtn) {
    imageModalCloseBtn.addEventListener('click', closeImageZoomModal);
  }
  if (imageZoomModal) {
    imageZoomModal.addEventListener('click', (e) => {
      if (e.target === imageZoomModal) {
        closeImageZoomModal();
      }
    });
  }

  if (imageModalViewport) {
    imageModalViewport.addEventListener('wheel', (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.15 : 0.87;
      setZoom(currentZoom * factor, e.clientX, e.clientY);
    }, { passive: false });

    imageModalViewport.addEventListener('mousedown', (e) => {
      if (e.target.closest('.image-modal-toolbar') || e.target.closest('.image-modal-header')) return;
      isPanning = true;
      panStartX = e.clientX - panX;
      panStartY = e.clientY - panY;
      imageModalViewport.classList.add('is-dragging');
    });

    window.addEventListener('mousemove', (e) => {
      if (!isPanning) return;
      panX = e.clientX - panStartX;
      panY = e.clientY - panStartY;
      updateImageTransform();
    });

    window.addEventListener('mouseup', () => {
      if (isPanning) {
        isPanning = false;
        if (imageModalViewport) {
          imageModalViewport.classList.remove('is-dragging');
        }
      }
    });

    imageModalViewport.addEventListener('dblclick', (e) => {
      if (e.target.closest('.image-modal-toolbar') || e.target.closest('.image-modal-header')) return;
      if (Math.abs(currentZoom - fitZoom) < 0.1 || currentZoom <= 1.1) {
        setZoom(2.0, e.clientX, e.clientY);
      } else {
        fitImageToViewport();
      }
    });
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

