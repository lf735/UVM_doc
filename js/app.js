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

  // Image Zoom Modal Controller (provided by js/app_modals.js)
  const imageModalController = window.UvmImageModal ? window.UvmImageModal.init() : null;
  const openImageZoomModal = imageModalController ? imageModalController.open : () => { };
  const closeImageZoomModal = imageModalController ? imageModalController.close : () => { };

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

  // =========================================================================
  // URL Normalization Helpers (provided by js/app_utils.js)
  // =========================================================================

  const {
    normalizeDocUrl,
    normalizeExampleUrl,
    normalizeSrcUrl,
    normalizePathForCompare,
    urlsMatch,
    escapeHtml,
    debounce,
    getQueryMatcher,
    matchSymbolItem,
    highlightMatch,
    isItemTypeAllowed,
    isRagResultAllowed,
    getRecentSearches,
    saveRecentSearch: saveRecentSearchStorage,
    deleteRecentSearch,
    wipeRecentSearches
  } = window.UvmAppUtils;

  function cancelPendingFrameNav(frame) {
    if (!frame || !frame._pendingNav) return;
    const prev = frame._pendingNav;
    if (prev.onLoad) {
      frame.removeEventListener('load', prev.onLoad);
    }
    if (Array.isArray(prev.timeouts)) {
      prev.timeouts.forEach(id => clearTimeout(id));
    }
    frame._pendingNav = null;
  }

  function setFrameSrc(frame, relUrl) {
    if (!frame || !relUrl) return;
    cancelPendingFrameNav(frame);
    const navToken = (frame._navSeq = (frame._navSeq || 0) + 1);
    const pendingNav = { token: navToken, timeouts: [], onLoad: null };
    frame._pendingNav = pendingNav;

    const dispatchScroll = (anchor) => {
      if (!frame._pendingNav || frame._pendingNav.token !== navToken) return;
      try {
        if (frame.contentWindow) {
          frame.contentWindow.postMessage({
            type: 'scrollToSection',
            anchor: anchor,
            id: anchor,
            navToken: navToken
          }, '*');
        }
      } catch (err) { }
    };

    try {
      if (!frame.hasAttribute('srcdoc')) {
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

        // If already on the same page, do not reload the iframe; scroll smoothly via postMessage
        if (currentPath === targetUrl.pathname) {
          if (targetUrl.hash) {
            if (frame.contentWindow && rawAnchor) {
              dispatchScroll(rawAnchor);
            } else {
              try {
                frame.contentWindow.location.hash = targetUrl.hash;
              } catch (e) { }
            }
          } else {
            // Navigating to top of the current page
            try {
              frame.contentWindow.scrollTo({ top: 0, behavior: 'smooth' });
            } catch (e) { }
            dispatchScroll('MainTopic');
          }
          return;
        }
      }
    } catch (e) { }

    // When loading a new document, apply theme and execute cross-frame scroll once frame is loaded
    let rawAnchor = '';
    try {
      const targetUrl = new URL(relUrl, window.location.href);
      rawAnchor = targetUrl.hash ? targetUrl.hash.replace(/^#/, '') : '';
    } catch (e) { }

    const onFrameLoaded = function () {
      frame.removeEventListener('load', onFrameLoaded);
      if (!frame._pendingNav || frame._pendingNav.token !== navToken) return;

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

      if (rawAnchor) {
        dispatchScroll(rawAnchor);
        [120, 320, 600].forEach(delay => {
          pendingNav.timeouts.push(setTimeout(() => dispatchScroll(rawAnchor), delay));
        });
      }
    };
    pendingNav.onLoad = onFrameLoaded;
    frame.addEventListener('load', onFrameLoaded);

    frame.removeAttribute('srcdoc');
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
      const isActive = btn.getAttribute('data-tab') === tabName;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
    if (typeof updateSidebarPillsForTab === 'function') {
      updateSidebarPillsForTab();
    }
    renderSidebar();
    highlightActiveSidebar();
  }

  function setViewMode(mode, updateHistory = true) {
    if (window.innerWidth <= 860 && mode === 'split') {
      mode = 'docs';
    }
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

    const isMobileView = window.innerWidth <= 860;
    const expandSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9" /><polyline points="9 21 3 21 3 15" /><line x1="21" y1="3" x2="14" y2="10" /><line x1="3" y1="21" x2="10" y2="14" /></svg>';
    const collapseSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 14 10 14 10 20" /><polyline points="20 10 14 10 14 4" /><line x1="14" y1="10" x2="21" y2="3" /><line x1="3" y1="21" x2="10" y2="14" /></svg>';
    const codeSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></svg>';
    const docSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></svg>';

    const btnFullDoc = document.getElementById('open-full-doc');
    if (btnFullDoc) {
      if (isMobileView) {
        btnFullDoc.title = 'Switch to Source view';
        btnFullDoc.innerHTML = codeSvg;
      } else {
        const isFullDoc = mode === 'docs';
        btnFullDoc.title = isFullDoc ? 'Restore split view' : 'Expand documentation full width';
        btnFullDoc.innerHTML = isFullDoc ? collapseSvg : expandSvg;
      }
    }
    const btnFullSrc = document.getElementById('open-full-src');
    if (btnFullSrc) {
      if (isMobileView) {
        btnFullSrc.title = 'Switch to Documentation view';
        btnFullSrc.innerHTML = docSvg;
      } else {
        const isFullSrc = mode === 'source';
        btnFullSrc.title = isFullSrc ? 'Restore split view' : 'Expand source code full width';
        btnFullSrc.innerHTML = isFullSrc ? collapseSvg : expandSvg;
      }
    }

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

    // On mobile, open full source view directly (no split view); on desktop, switch to split view
    const targetMode = window.innerWidth <= 860 ? 'source' : 'split';
    if (currentMode !== targetMode) {
      setViewMode(targetMode, true);
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

  let lastOpenDoc = { url: '', time: 0 };

  // Global handler for when a source page requests to view documentation
  window.openDocView = function (docUrl, symbol, ownerClass) {
    let rawSymbol = symbol || '';
    let resolvedOwner = ownerClass || '';
    if (rawSymbol.includes('::') && !resolvedOwner) {
      const parts = rawSymbol.split('::');
      resolvedOwner = parts[0].trim();
      rawSymbol = parts[parts.length - 1].trim();
    }

    let fullDoc = null;
    if (docUrl) {
      fullDoc = normalizeDocUrl(docUrl);
    }

    if (!fullDoc && rawSymbol && typeof UVM_DATA !== 'undefined' && UVM_DATA.searchIndex) {
      const symClean = rawSymbol.replace(/^`/, '');
      const symLower = rawSymbol.toLowerCase();
      const cleanLower = symClean.toLowerCase();
      let match = null;

      // 0. Owner / ancestor-scoped match when ownerClass is known
      if (resolvedOwner) {
        if (resolvedOwner === 'Global' || resolvedOwner === 'Globals') {
          match = UVM_DATA.searchIndex.find(s =>
            s.doc && s.name === symClean && (!s.category || s.category === 'Global' || s.category === 'Globals')
          );
        } else {
          const chain = [];
          const seen = new Set();
          let curr = resolvedOwner;
          const nodes = (UVM_DATA.classHierarchy && UVM_DATA.classHierarchy.nodes) || {};
          while (curr && !seen.has(curr)) {
            seen.add(curr);
            chain.push(curr);
            curr = nodes[curr] ? nodes[curr].parent : null;
          }
          for (const cls of chain) {
            match = UVM_DATA.searchIndex.find(s => {
              if (!s.doc || !s.name) return false;
              const nameOk = s.name === symClean || s.name === cls + '::' + symClean || s.name.endsWith('::' + symClean);
              const catOk = s.category && (s.category === cls || s.category.split('::')[0] === cls);
              return nameOk && catOk;
            });
            if (match) break;
          }
        }
      }

      // 1. Exact match
      if (!match) {
        match = UVM_DATA.searchIndex.find(s => s.name === rawSymbol && s.doc);
      }
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

    if (!fullDoc) {
      fullDoc = 'docs_view/overviews/intro-txt.html';
    }

    const now = Date.now();
    if (lastOpenDoc.url === fullDoc && (now - lastOpenDoc.time) < 200) {
      return;
    }
    lastOpenDoc = { url: fullDoc, time: now };

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
    if (e.data.type === 'scrollAck' && typeof e.data.navToken === 'number') {
      [docFrame, srcFrame].forEach(f => {
        if (f && f._pendingNav && f._pendingNav.token === e.data.navToken) {
          cancelPendingFrameNav(f);
        }
      });
      return;
    }
    if (e.data.type === 'openSourceView' && e.data.url) {
      window.openSourceView(e.data.url);
    } else if (e.data.type === 'openDocView' && (e.data.url || e.data.symbol)) {
      window.openDocView(e.data.url, e.data.symbol, e.data.ownerClass);
    } else if (e.data.type === 'openExampleView' && e.data.url) {
      window.openExampleView(e.data.url);
    } else if (e.data.type === 'studioFileChanged' && e.data.url) {
      if (currentMode === 'split') {
        loadSource(e.data.url, true, false);
      }
    } else if (e.data.type === 'exampleNavigated' && e.data.url) {
      let fullEx = normalizeExampleUrl(e.data.url);
      if (!fullEx.includes('#') && currentDocUrl && currentDocUrl.includes('#') && currentDocUrl.split('#')[0] === fullEx) {
        fullEx = currentDocUrl;
      }
      currentDocUrl = fullEx;
      updateDocTitle(fullEx);
      highlightActiveSidebar(fullEx);
      updateHash();
    } else if (e.data.type === 'docNavigated' && e.data.url) {
      let fullDoc = normalizeDocUrl(e.data.url);
      if (!fullDoc.includes('#') && currentDocUrl && currentDocUrl.includes('#') && currentDocUrl.split('#')[0] === fullDoc) {
        fullDoc = currentDocUrl;
      }
      currentDocUrl = fullDoc;
      updateDocTitle(fullDoc);
      highlightActiveSidebar(fullDoc);
      updateHash();
    } else if (e.data.type === 'srcNavigated' && e.data.url) {
      let fullSrc = normalizeSrcUrl(e.data.url);
      if (!fullSrc.includes('#') && currentSrcUrl && currentSrcUrl.includes('#') && currentSrcUrl.split('#')[0] === fullSrc) {
        fullSrc = currentSrcUrl;
      }
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

  function loadDoc(url, pushState = true, autoPair = true) {
    const fullDoc = normalizeDocUrl(url);
    currentDocUrl = fullDoc;
    setFrameSrc(docFrame, fullDoc);
    updateDocTitle(fullDoc);

    if (autoPair && currentMode === 'split') {
      // In split mode, check if we should pair with its source file
      const docClean = fullDoc.replace(/^docs_view\//, '').split('#')[0];
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

  function loadSource(url, pushState = true, autoPair = true) {
    const fullSrc = normalizeSrcUrl(url);
    currentSrcUrl = fullSrc;
    setFrameSrc(srcFrame, fullSrc);
    updateSrcTitle(fullSrc);

    if (autoPair && currentMode === 'split') {
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
  // Augmented Search Index (Includes Inherited Methods & Elements)
  // =========================================================================

  let cachedAugmentedSearchIndex = null;

  function normalizeClassNameForSearch(cat) {
    if (!cat) return '';
    return String(cat).replace(/\s*#\([^)]*\)/g, '').trim();
  }

  function getAugmentedSearchIndex() {
    if (cachedAugmentedSearchIndex) return cachedAugmentedSearchIndex;
    if (typeof UVM_DATA === 'undefined' || !Array.isArray(UVM_DATA.searchIndex)) return [];

    const baseItems = UVM_DATA.searchIndex;
    const classNodes = (UVM_DATA.classHierarchy && UVM_DATA.classHierarchy.nodes) ? UVM_DATA.classHierarchy.nodes : null;
    if (!classNodes) {
      cachedAugmentedSearchIndex = baseItems;
      return cachedAugmentedSearchIndex;
    }

    const inheritableTypes = new Set([
      'function', 'task', 'method', 'variable', 'port',
      'constant', 'parameter', 'type', 'enum', 'enumeration'
    ]);

    const ownMembersByClass = new Map();
    baseItems.forEach(item => {
      if (!item || !item.name || !item.category || !inheritableTypes.has(item.type)) return;
      const normClass = normalizeClassNameForSearch(item.category);
      if (!normClass || !classNodes[normClass]) return;
      if (!ownMembersByClass.has(normClass)) {
        ownMembersByClass.set(normClass, new Map());
      }
      const memberMap = ownMembersByClass.get(normClass);
      const existing = memberMap.get(item.name);
      if (!existing || ((item.doc || '').includes('#') && !(existing.doc || '').includes('#'))) {
        memberMap.set(item.name, item);
      }
    });

    function resolveParentForSearch(clsName) {
      const node = classNodes[clsName];
      if (!node || !node.parent) return '';
      if (node.parent === 'BASE' && clsName === 'uvm_reg_sequence') return 'uvm_sequence';
      if (node.parent === 'IF' && clsName === 'uvm_port_base') return 'uvm_void';
      return node.parent;
    }

    const inheritedItems = [];
    Object.keys(classNodes).forEach(cname => {
      const cNode = classNodes[cname];
      if (!cNode || !cNode.parent) return;

      const ancestorsNearestFirst = [];
      let curr = resolveParentForSearch(cname);
      const visited = new Set([cname]);
      while (curr && !visited.has(curr) && classNodes[curr]) {
        visited.add(curr);
        ancestorsNearestFirst.push(curr);
        curr = resolveParentForSearch(curr);
      }
      if (!ancestorsNearestFirst.length) return;

      const seenNames = new Set(['new']);
      const ownMap = ownMembersByClass.get(cname);
      if (ownMap) {
        ownMap.forEach((_, memberName) => seenNames.add(memberName));
      }

      const safeClass = cname.replace(/[^A-Za-z0-9_]/g, '_');
      const baseDoc = (cNode.doc || '').split('#')[0];

      ancestorsNearestFirst.forEach(anc => {
        const ancMap = ownMembersByClass.get(anc);
        if (!ancMap) return;
        ancMap.forEach((ancItem, memberName) => {
          if (seenNames.has(memberName)) return;
          seenNames.add(memberName);
          const safeMember = memberName.replace(/[^A-Za-z0-9_]/g, '_');
          const inhDoc = baseDoc ? `${baseDoc}#${cname}.${memberName}` : ancItem.doc;
          inheritedItems.push({
            name: memberName,
            type: ancItem.type,
            category: cname,
            inheritedFrom: anc,
            isInherited: true,
            src: ancItem.src,
            doc: inhDoc,
            desc: `Inherited from ${anc}${ancItem.desc ? ' — ' + ancItem.desc : ''}`
          });
        });
      });
    });

    cachedAugmentedSearchIndex = baseItems.concat(inheritedItems);
    return cachedAugmentedSearchIndex;
  }

  // Matcher & search filter helpers provided by js/app_utils.js

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
    const title = item.title || '';
    const href = item.href || '';
    const hrefLower = href.toLowerCase();
    const titleLower = title.toLowerCase();

    // Check sidebar filter pills for docs tab
    if (activeSidebarTab === 'docs' && !sidebarFilterTypes.has('all') && sidebarFilterTypes.size > 0) {
      let pillMatch = false;
      if (sidebarFilterTypes.has('class')) {
        if (!title.includes('Overview') && !title.includes('Package') && !hrefLower.includes('macro') && !hrefLower.includes('intro') && !hrefLower.includes('notes')) {
          pillMatch = true;
        }
      }
      if (sidebarFilterTypes.has('macro')) {
        if (hrefLower.includes('macro') || titleLower.includes('macro') || (typeof UVM_DATA !== 'undefined' && (UVM_DATA.docHeadings[href] || []).some(h => h.type === 'macro'))) {
          pillMatch = true;
        }
      }
      if (sidebarFilterTypes.has('overview')) {
        if (title.includes('Overview') || title.includes('Introduction') || title.includes('Release Notes') || hrefLower.includes('intro') || hrefLower.includes('notes') || item.type === 'index') {
          pillMatch = true;
        }
      }
      if (sidebarFilterTypes.has('component') && (hrefLower.includes('comps/') || hrefLower.includes('component') || titleLower.includes('component'))) {
        pillMatch = true;
      }
      if (sidebarFilterTypes.has('sequence') && (hrefLower.includes('seq/') || hrefLower.includes('sequence') || titleLower.includes('sequence'))) {
        pillMatch = true;
      }
      if (sidebarFilterTypes.has('tlm') && (hrefLower.includes('tlm') || titleLower.includes('tlm'))) {
        pillMatch = true;
      }
      if (sidebarFilterTypes.has('reg') && (hrefLower.includes('reg/') || titleLower.includes('reg') || titleLower.includes('register'))) {
        pillMatch = true;
      }
      if (sidebarFilterTypes.has('phase') && (hrefLower.includes('phase') || hrefLower.includes('phasing') || titleLower.includes('phase'))) {
        pillMatch = true;
      }
      if (!pillMatch) return false;
    }

    if (!matcher) return true;

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
        const hTitle = matcher.isCaseSensitive ? (h.title || '') : (h.title || '').toLowerCase();
        const hGroup = matcher.isCaseSensitive ? (h.group || '') : (h.group || '').toLowerCase();
        const combined = `${lowerTitle} ${hTitle} ${hGroup}`;
        return words.every(w => combined.includes(w));
      });
    }

    return false;
  }

  function sourceNodeMatches(node, matcher) {
    if (activeSidebarTab === 'source' && !sidebarFilterTypes.has('all') && sidebarFilterTypes.size > 0) {
      const p = (node.path || node.url || node.name || '').toLowerCase();
      let matchPill = false;
      if (sidebarFilterTypes.has('svh') && p.endsWith('.svh')) matchPill = true;
      if (sidebarFilterTypes.has('sv') && (p.endsWith('.sv') && !p.endsWith('.svh'))) matchPill = true;
      if (sidebarFilterTypes.has('c') && (p.endsWith('.c') || p.endsWith('.h') || p.endsWith('.cc'))) matchPill = true;
      if (sidebarFilterTypes.has('base') && p.includes('base/')) matchPill = true;
      if (sidebarFilterTypes.has('comps') && p.includes('comps/')) matchPill = true;
      if (sidebarFilterTypes.has('seq') && p.includes('seq/')) matchPill = true;
      if (sidebarFilterTypes.has('tlm') && (p.includes('tlm1/') || p.includes('tlm2/'))) matchPill = true;
      if (sidebarFilterTypes.has('reg') && p.includes('reg/')) matchPill = true;
      if (!matchPill && node.type === 'file') return false;
    }

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
      tabBtns.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
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

    if (activeSidebarTab === 'source') {
      sidebarPillsContainer.style.display = 'flex';
      sidebarPillsContainer.innerHTML = `
            <button class="sidebar-pill active" data-type="all">All</button>
            <button class="sidebar-pill" data-type="svh">.svh</button>
            <button class="sidebar-pill" data-type="sv">.sv</button>
            <button class="sidebar-pill" data-type="c">.c / .h</button>
            <button class="sidebar-pill" data-type="base">Base</button>
            <button class="sidebar-pill" data-type="comps">Components</button>
            <button class="sidebar-pill" data-type="seq">Sequences</button>
            <button class="sidebar-pill" data-type="tlm">TLM</button>
            <button class="sidebar-pill" data-type="reg">Registers</button>
          `;
    } else if (activeSidebarTab === 'examples') {
      sidebarPillsContainer.style.display = 'flex';
      sidebarPillsContainer.innerHTML = `
            <button class="sidebar-pill active" data-type="all">All</button>
            <button class="sidebar-pill" data-type="beginner">Beginner</button>
            <button class="sidebar-pill" data-type="intermediate">Intermediate</button>
            <button class="sidebar-pill" data-type="advanced">Advanced</button>
          `;
    } else if (activeSidebarTab === 'hierarchy') {
      sidebarPillsContainer.style.display = 'flex';
      sidebarPillsContainer.innerHTML = `
            <button class="sidebar-pill active" data-type="all">All</button>
            <button class="sidebar-pill" data-type="component">Components</button>
            <button class="sidebar-pill" data-type="object">Objects</button>
            <button class="sidebar-pill" data-type="sequence">Sequences</button>
            <button class="sidebar-pill" data-type="tlm">TLM</button>
            <button class="sidebar-pill" data-type="reg">Registers</button>
            <button class="sidebar-pill" data-type="phase">Phases</button>
          `;
    } else if (activeSidebarTab === 'index') {
      sidebarPillsContainer.style.display = 'flex';
      sidebarPillsContainer.innerHTML = `
            <button class="sidebar-pill active" data-type="all">All</button>
            <button class="sidebar-pill" data-type="class">Classes</button>
            <button class="sidebar-pill" data-type="function">Functions</button>
            <button class="sidebar-pill" data-type="task">Tasks</button>
            <button class="sidebar-pill" data-type="macro">Macros</button>
            <button class="sidebar-pill" data-type="variable">Variables</button>
            <button class="sidebar-pill" data-type="constant">Constants</button>
            <button class="sidebar-pill" data-type="type">Types</button>
            <button class="sidebar-pill" data-type="port">Ports</button>
          `;
    } else {
      // For docs: show topics and category filters
      sidebarPillsContainer.style.display = 'flex';
      sidebarPillsContainer.innerHTML = `
            <button class="sidebar-pill active" data-type="all">All</button>
            <button class="sidebar-pill" data-type="class">Classes</button>
            <button class="sidebar-pill" data-type="macro">Macros</button>
            <button class="sidebar-pill" data-type="overview">Overviews</button>
            <button class="sidebar-pill" data-type="component">Components</button>
            <button class="sidebar-pill" data-type="sequence">Sequences</button>
            <button class="sidebar-pill" data-type="tlm">TLM</button>
            <button class="sidebar-pill" data-type="reg">Registers</button>
            <button class="sidebar-pill" data-type="phase">Phases</button>
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
    }, 200));

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
        let catPillMatch = false;
        if (activeSidebarTab === 'docs' && !sidebarFilterTypes.has('all') && sidebarFilterTypes.size > 0) {
          const cTitleLower = cat.title.toLowerCase();
          if (sidebarFilterTypes.has('component') && cTitleLower.includes('component')) catPillMatch = true;
          if (sidebarFilterTypes.has('sequence') && cTitleLower.includes('sequence')) catPillMatch = true;
          if (sidebarFilterTypes.has('tlm') && cTitleLower.includes('tlm')) catPillMatch = true;
          if (sidebarFilterTypes.has('reg') && (cTitleLower.includes('register') || cTitleLower.includes('reg'))) catPillMatch = true;
          if (sidebarFilterTypes.has('phase') && cTitleLower.includes('phas')) catPillMatch = true;
          if (sidebarFilterTypes.has('macro') && cTitleLower.includes('macro')) catPillMatch = true;
          if (sidebarFilterTypes.has('overview') && (cTitleLower.includes('overview') || cat.overviewHref)) catPillMatch = true;
        }
        if (subItems.length > 0 || groupTitleMatches || catPillMatch || (cat.overviewHref && (!matcher || groupTitleMatches))) {
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
              ${renderGroupItemsHtml(subItems.length > 0 ? subItems : cat.children, matcher)}
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
        let groupPillMatch = false;
        if (activeSidebarTab === 'docs' && !sidebarFilterTypes.has('all') && sidebarFilterTypes.size > 0) {
          const gTitleLower = item.title.toLowerCase();
          if (sidebarFilterTypes.has('component') && gTitleLower.includes('component')) groupPillMatch = true;
          if (sidebarFilterTypes.has('sequence') && gTitleLower.includes('sequence')) groupPillMatch = true;
          if (sidebarFilterTypes.has('tlm') && gTitleLower.includes('tlm')) groupPillMatch = true;
          if (sidebarFilterTypes.has('reg') && (gTitleLower.includes('register') || gTitleLower.includes('reg'))) groupPillMatch = true;
          if (sidebarFilterTypes.has('phase') && gTitleLower.includes('phas')) groupPillMatch = true;
          if (sidebarFilterTypes.has('macro') && gTitleLower.includes('macro')) groupPillMatch = true;
          if (sidebarFilterTypes.has('overview') && (gTitleLower.includes('overview') || item.overviewHref)) groupPillMatch = true;
        }
        if (subs.length > 0 || titleMatches || groupPillMatch) {
          res.push({ ...item, children: subs.length > 0 ? subs : item.children });
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
        const children = node.children || [];
        let childrenHtml = '';
        for (let i = 0; i < children.length; i++) {
          childrenHtml += renderNode(children[i], depth + 1);
        }
        if (childrenHtml) {
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

    const html = (root.children || []).map(child => renderNode(child, 0)).join('');
    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching files</div>';
    attachSidebarListeners();
  }

  let currentActiveIndexKey = null;
  let cachedAllowedBaseSymbols = null;
  let cachedAllowedAugmentedSymbols = null;
  const INDEX_ALLOWED_TYPES = new Set([
    'class', 'macro', 'function', 'task', 'method',
    'variable', 'constant', 'parameter', 'type', 'enum', 'enumeration', 'port'
  ]);

  function getSymbolIndexKey(item) {
    if (!item) return '';
    return `${item.name}::${item.type}::${item.category || ''}::${item.doc || ''}::${item.src || ''}`;
  }

  function renderAlphabeticalIndex(rawQuery) {
    const hasQuery = !!(rawQuery && rawQuery.trim().length > 0);
    let sourcePool;
    if (hasQuery) {
      if (!cachedAllowedAugmentedSymbols) {
        cachedAllowedAugmentedSymbols = getAugmentedSearchIndex().filter(x => x && INDEX_ALLOWED_TYPES.has(x.type));
      }
      sourcePool = cachedAllowedAugmentedSymbols;
    } else {
      if (!cachedAllowedBaseSymbols) {
        cachedAllowedBaseSymbols = (UVM_DATA.searchIndex || []).filter(x => x && INDEX_ALLOWED_TYPES.has(x.type));
      }
      sourcePool = cachedAllowedBaseSymbols;
    }

    const matcher = getQueryMatcher(rawQuery, sidebarRegexEnabled, false, sidebarFilter);
    const filterAll = sidebarFilterTypes.has('all') || sidebarFilterTypes.size === 0;

    const matchedSymbols = [];
    for (let i = 0; i < sourcePool.length; i++) {
      const item = sourcePool[i];
      if (!filterAll && !isItemTypeAllowed(item.type, sidebarFilterTypes)) continue;
      const matchRes = matchSymbolItem(item, matcher);
      if (matchRes.match) {
        matchedSymbols.push({ item, score: matchRes.score });
      }
    }

    matchedSymbols.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      if (Boolean(a.item.isInherited) !== Boolean(b.item.isInherited)) {
        return a.item.isInherited ? 1 : -1;
      }
      const an = a.item.name;
      const bn = b.item.name;
      return an < bn ? -1 : (an > bn ? 1 : 0);
    });

    const cleanDoc = currentDocUrl ? currentDocUrl.replace(/^[./]+/, '') : '';
    const cleanSrc = currentSrcUrl ? currentSrcUrl.replace(/^[./]+/, '') : '';

    function renderSymbolRange(startIdx, endIdx) {
      let chunkHtml = '';
      const limit = Math.min(endIdx, matchedSymbols.length);
      for (let i = startIdx; i < limit; i++) {
        const item = matchedSymbols[i].item;
        const badgeClass = item.type === 'class' ? 'badge-class' :
          (item.type === 'macro' ? 'badge-macro' :
            (item.type === 'function' ? 'badge-function' :
              (item.type === 'task' ? 'badge-task' :
                (item.type === 'variable' ? 'badge-variable' :
                  (item.type === 'constant' || item.type === 'parameter' ? 'badge-constant' :
                    (item.type === 'type' || item.type === 'enum' || item.type === 'enumeration' ? 'badge-type' :
                      (item.type === 'port' ? 'badge-port' :
                        (item.type === 'example' ? 'badge-example' : 'badge-method'))))))));
        const isMethodLike = item.type === 'function' || item.type === 'task' || item.type === 'method' || item.type === 'variable' || item.type === 'port';
        const ownerInfo = item.category && isMethodLike ?
          `<span class="az-symbol-owner" style="font-size:0.68rem; color:var(--text-muted); margin-left:auto; margin-right:0.35rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:110px;">${highlightMatch(item.category, matcher)}</span>` : '';
        const itemKey = getSymbolIndexKey(item);
        let isActive = false;
        if (currentActiveIndexKey) {
          isActive = (itemKey === currentActiveIndexKey);
        } else {
          if (item.doc && cleanDoc && (item.doc === cleanDoc || item.doc.replace(/^[./]+/, '') === cleanDoc)) {
            isActive = true;
          } else if (item.src && cleanSrc && (item.src === cleanSrc || item.src.replace(/^[./]+/, '') === cleanSrc)) {
            isActive = true;
          }
        }
        chunkHtml += `<div class="nav-single-item">
            <a href="#" data-doc-href="${item.doc || ''}" data-src-href="${item.src || ''}" data-index-key="${escapeHtml(itemKey)}" class="nav-item-link az-index-link ${isActive ? 'active' : ''}" title="${escapeHtml(item.desc || item.name)}">
              <span class="az-symbol-name">${highlightMatch(item.name, matcher)}</span>
              ${ownerInfo}
              <span class="res-badge ${badgeClass}">${item.type}</span>
            </a>
          </div>`;
      }
      return chunkHtml;
    }

    const MAX_INDEX_RENDER = 200;
    let html = renderSymbolRange(0, MAX_INDEX_RENDER);
    if (matchedSymbols.length > MAX_INDEX_RENDER) {
      html += `<div id="az-show-more-wrap" style="padding: 0.75rem; text-align: center; border-top: 1px solid var(--border-color);">
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.4rem;">Showing ${MAX_INDEX_RENDER} of ${matchedSymbols.length} results</div>
        <button type="button" id="az-show-all-btn" style="padding: 0.3rem 0.75rem; font-size: 0.75rem; border-radius: 6px; border: 1px solid var(--border-color); background: var(--bg-surface); color: var(--text-primary); cursor: pointer;">Show all (${matchedSymbols.length})</button>
      </div>`;
    }

    sidebarContent.innerHTML = html || '<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem">No matching symbols</div>';
    const showAllBtn = document.getElementById('az-show-all-btn');
    if (showAllBtn) {
      showAllBtn.addEventListener('click', () => {
        const wrap = document.getElementById('az-show-more-wrap');
        if (wrap) wrap.remove();
        sidebarContent.insertAdjacentHTML('beforeend', renderSymbolRange(MAX_INDEX_RENDER, matchedSymbols.length));
      });
    }
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
        if (matcher.type === 'regex') {
          textMatches = matcher.valid && matcher.regex ? (matcher.regex.test(node.name) || (node.summary && matcher.regex.test(node.summary))) : false;
        } else if (matcher.words && matcher.words.length > 0) {
          const cLower = node.name.toLowerCase();
          const sLower = (node.summary || '').toLowerCase();
          textMatches = matcher.words.every(w => cLower.includes(w) || sLower.includes(w));
        }
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

  function bindSidebarDelegation() {
    if (!sidebarContent || sidebarContent._delegatedBound) return;
    sidebarContent._delegatedBound = true;

    sidebarContent.addEventListener('click', (e) => {
      // 1. Collapsible group headers: Clicking chevron button toggles expand/collapse
      const chevronBtn = e.target.closest('.nav-group-chevron-btn');
      if (chevronBtn) {
        e.stopPropagation();
        const group = chevronBtn.closest('.nav-group');
        if (group) group.classList.toggle('collapsed');
        updateSidebarToggleAllBtn();
        return;
      }

      // 2. Navigation links (doc & src & group overview title links)
      const link = e.target.closest('[data-doc-href], [data-src-href]');
      if (link) {
        e.preventDefault();
        e.stopPropagation();
        const docHref = link.getAttribute('data-doc-href');
        const srcHref = link.getAttribute('data-src-href');
        const indexKey = link.getAttribute('data-index-key');
        if (indexKey) {
          currentActiveIndexKey = indexKey;
        }

        // Immediately highlight the clicked item for instant, reliable visual feedback
        sidebarContent.querySelectorAll('.nav-item-link.active, .file-tree-item.active, .hierarchy-link.active, .hierarchy-row.active')
          .forEach(el => el.classList.remove('active'));
        link.classList.add('active');
        const row = link.closest('.hierarchy-row');
        if (row) row.classList.add('active');
        try {
          link.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        } catch (err) { }

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
          if (currentMode === 'split' && srcHref) {
            loadDoc(docHref, true, false);
            loadSource(srcHref, true, false);
          } else {
            loadDoc(docHref);
          }
        } else if (srcHref) {
          loadSource(srcHref);
        }
        if (window.innerWidth <= 860 && sidebar) {
          sidebar.classList.remove('open');
        }
        return;
      }

      // 3. Clicking on header (when it doesn't have an overview link) toggles expand/collapse
      const header = e.target.closest('.nav-group-header');
      if (header && !e.target.closest('a')) {
        const group = header.closest('.nav-group');
        if (group) group.classList.toggle('collapsed');
        updateSidebarToggleAllBtn();
      }
    });
  }

  function attachSidebarListeners() {
    bindSidebarDelegation();

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
    if (activeSidebarTab === 'index') {
      // In the index tab, preserve and enforce the exact active index item!
      if (currentActiveIndexKey) {
        sidebarContent.querySelectorAll('.az-index-link').forEach(el => {
          const matches = el.getAttribute('data-index-key') === currentActiveIndexKey;
          el.classList.toggle('active', matches);
        });
        return;
      }
      // If no explicit indexKey yet, try to find an exact matching anchor
      if (url) {
        let found = false;
        sidebarContent.querySelectorAll('.az-index-link').forEach(el => {
          const docHref = el.getAttribute('data-doc-href') || '';
          const srcHref = el.getAttribute('data-src-href') || '';
          const matchExact = (docHref && url && docHref.includes('#') && (docHref === url || url.endsWith(docHref))) ||
            (srcHref && url && srcHref.includes('#') && (srcHref === url || url.endsWith(srcHref)));
          if (matchExact && !found) {
            el.classList.add('active');
            found = true;
            currentActiveIndexKey = el.getAttribute('data-index-key');
            try {
              el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } catch (e) { }
          } else {
            el.classList.remove('active');
          }
        });
        if (found) return;
      }
      return;
    }

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

  // Pane actions: Toggle Full View <-> Split View (Desktop) or Switch Docs <-> Source (Mobile)
  const openFullDoc = document.getElementById('open-full-doc');
  if (openFullDoc) {
    openFullDoc.addEventListener('click', () => {
      if (window.innerWidth <= 860) {
        setViewMode('source', true);
      } else {
        setViewMode(currentMode === 'docs' ? 'split' : 'docs', true);
      }
    });
  }
  const openFullSrc = document.getElementById('open-full-src');
  if (openFullSrc) {
    openFullSrc.addEventListener('click', () => {
      if (window.innerWidth <= 860) {
        setViewMode('docs', true);
      } else {
        setViewMode(currentMode === 'source' ? 'split' : 'source', true);
      }
    });
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

  // Recent Searches Manager (storage helpers provided by js/app_utils.js)
  function saveRecentSearch(query, mode) {
    const resolvedMode = mode === 'ai' ? 'ai' : (mode === 'standard' ? 'standard' : (modalAiEnabled ? 'ai' : 'standard'));
    saveRecentSearchStorage(query, resolvedMode);
  }

  function removeRecentSearch(query, mode) {
    deleteRecentSearch(query, mode);
    renderRecentSearches();
  }

  function clearRecentSearches() {
    wipeRecentSearches();
    renderRecentSearches();
  }

  function renderRecentSearches() {
    if (!modalRecentSearches || !recentSearchesChips) return;
    const history = getRecentSearches();
    if (!history.length) {
      if (modalAiEnabled) {
        recentSearchesChips.innerHTML = `
          <div class="recent-searches-empty" style="padding:1.25rem 1.25rem; text-align:center; color:var(--text-muted); font-size:0.825rem;">
            <span style="opacity:0.75;">No recent searches. Your queries will appear here.</span>
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

  const modalSearchClose = document.getElementById('modal-search-close');
  if (modalSearchClose) {
    modalSearchClose.addEventListener('click', closeSearchModal);
  }

  // RAG State & Helpers
  let modalAiEnabled = false;
  let activeAiSearchId = 0;
  let lastAiRawResults = null;
  let lastAiQuery = null;

  const searchModalsController = window.UvmSearchModals
    ? window.UvmSearchModals.init({
      onModelChange: () => {
        lastAiRawResults = null;
        lastAiQuery = null;
      }
    })
    : null;
  const updateCacheStatusUI = searchModalsController ? searchModalsController.updateCacheStatusUI : () => { };
  const openAiConsentModal = searchModalsController ? searchModalsController.openAiConsentModal : () => { };
  const closeAiConsentModal = searchModalsController ? searchModalsController.closeAiConsentModal : () => { };
  const openSearchSettingsModal = searchModalsController ? searchModalsController.openSearchSettingsModal : () => { };
  const closeSearchSettingsModal = searchModalsController ? searchModalsController.closeSearchSettingsModal : () => { };

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
            <button type="button" class="prompt-chip" data-query="${escapeHtml(p.query)}" title="${escapeHtml(p.category)}: click to ask this question">
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
        searchInput.placeholder = "Ask a natural language question (e.g. 'how to pass vifs with config db')...";
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
    if (imageModalController && imageModalController.handleKeydown(e)) {
      return;
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
                (displayType === 'variable' ? 'badge-variable' :
                  (displayType === 'constant' || displayType === 'parameter' ? 'badge-constant' :
                    (displayType === 'type' || displayType === 'enum' || displayType === 'enumeration' ? 'badge-type' :
                      (displayType === 'port' ? 'badge-port' :
                        (displayType === 'example' ? 'badge-example' :
                          (displayType === 'method' ? 'badge-method' : 'badge-file')))))))));

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
    const items = getAugmentedSearchIndex();
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
      if (Boolean(a.item.isInherited) !== Boolean(b.item.isInherited)) {
        return a.item.isInherited ? 1 : -1;
      }
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
              (item.type === 'variable' ? 'badge-variable' :
                (item.type === 'constant' || item.type === 'parameter' ? 'badge-constant' :
                  (item.type === 'type' || item.type === 'enum' || item.type === 'enumeration' ? 'badge-type' :
                    (item.type === 'port' ? 'badge-port' :
                      (item.type === 'example' ? 'badge-example' :
                        (item.type === 'method' ? 'badge-method' : 'badge-file')))))))));

      const isMethodLike = item.type === 'function' || item.type === 'task' || item.type === 'method' || item.type === 'variable' || item.type === 'port' || item.type === 'constant' || item.type === 'parameter' || item.type === 'type' || item.type === 'enum' || item.type === 'enumeration';
      const categoryTag = item.category && isMethodLike ?
        `<span style="color:var(--text-muted); font-size:0.8rem; margin-right:0.35rem">${highlightMatch(item.category, matcher)} ::</span>` : '';
      const inheritedTag = item.isInherited && item.inheritedFrom ?
        `<span class="res-inherited-badge" title="Inherited from ${escapeHtml(item.inheritedFrom)}">↳ ${escapeHtml(item.inheritedFrom)}</span>` : '';

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
              <div class="res-title-row" style="display:flex; align-items:center; flex-wrap:wrap; gap:0.25rem;">
                ${categoryTag}
                <span class="res-name">${highlightMatch(item.name, matcher)}</span>
                ${inheritedTag}
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

    currentActiveIndexKey = getSymbolIndexKey(item);

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
        if (currentMode === 'split' && item.src) {
          loadDoc(item.doc, true, false);
          loadSource(item.src, true, false);
        } else {
          loadDoc(item.doc);
        }
      } else if (item.src) {
        loadSource(item.src);
      }
    }
  }

  // =========================================================================
  // Sidebar Toggle (Desktop Collapsible & Mobile Drawer)
  // =========================================================================

  if (menuToggle && sidebar) {
    try {
      if (localStorage.getItem('sidebarCollapsed') === '1' && window.innerWidth > 860) {
        sidebar.classList.add('collapsed');
        menuToggle.setAttribute('aria-expanded', 'false');
      } else {
        menuToggle.setAttribute('aria-expanded', 'true');
      }
    } catch (e) { }

    menuToggle.addEventListener('click', () => {
      if (window.innerWidth <= 860) {
        const isOpen = sidebar.classList.toggle('open');
        menuToggle.setAttribute('aria-expanded', String(isOpen));
      } else {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        menuToggle.setAttribute('aria-expanded', String(!isCollapsed));
        try {
          localStorage.setItem('sidebarCollapsed', isCollapsed ? '1' : '0');
        } catch (e) { }
      }
    });

    // Auto-close mobile drawer when selecting an item or clicking outside
    sidebar.addEventListener('click', (e) => {
      if (window.innerWidth <= 860 && e.target.closest('.nav-item-link, .file-tree-item, .nav-group-title-link')) {
        sidebar.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
    const mainViewport = document.querySelector('.main-viewport');
    if (mainViewport) {
      mainViewport.addEventListener('click', () => {
        if (window.innerWidth <= 860 && sidebar.classList.contains('open')) {
          sidebar.classList.remove('open');
          menuToggle.setAttribute('aria-expanded', 'false');
        }
      });
    }
  }

  // Ensure mobile viewports never stay in split mode on resize
  window.addEventListener('resize', () => {
    if (window.innerWidth <= 860 && currentMode === 'split') {
      setViewMode('docs', false);
    }
  });

  // Initialize
  updateSidebarPillsForTab();
  renderSidebar();
  parseHash();
});

