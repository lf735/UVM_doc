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
  const sidebarPills = document.querySelectorAll('.sidebar-pill');
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
  const modalSearchHeader = document.querySelector('.modal-search-header');

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
  // URL Normalization Helpers
  // =========================================================================

  function normalizeDocUrl(url) {
    if (!url) return 'docs_view/overviews/intro-txt.html';
    const hashIdx = url.indexOf('#');
    let pathPart = hashIdx !== -1 ? url.substring(0, hashIdx) : url;
    let hashPart = hashIdx !== -1 ? url.substring(hashIdx) : '';
    let clean = pathPart.replace(/^[./]+/, '');
    if (clean.includes('docs_view/')) {
      clean = clean.substring(clean.indexOf('docs_view/'));
    } else {
      clean = 'docs_view/' + clean;
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

  function setFrameSrc(frame, relUrl) {
    if (!frame || !relUrl) return;
    try {
      const targetUrl = new URL(relUrl, window.location.href);
      const currentUrl = new URL(frame.src, window.location.href);
        const rawAnchor = targetUrl.hash ? targetUrl.hash.replace(/^#/, '') : '';

        // If already on the same page, scroll immediately and directly
        if (currentUrl.pathname === targetUrl.pathname) {
          if (targetUrl.hash) {
            try {
              frame.contentWindow.location.hash = targetUrl.hash;
            } catch (e) { }
          }
          if (frame.contentWindow && rawAnchor) {
            frame.contentWindow.postMessage({
              type: 'scrollToSection',
              anchor: rawAnchor,
              id: rawAnchor
            }, '*');
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
        renderSidebar();
      }

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
        const clean = url.replace('docs_view/', '').replace('.html', '').split('#')[0];
        docPaneTitle.textContent = clean;
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
          .replace(/"/g, '&quot;');
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
        const safeText = escapeHtml(text);
        if (!matcher) return safeText;

        if (matcher.type === 'regex') {
          if (!matcher.valid || !matcher.regex) return safeText;
          try {
            const gFlags = (matcher.regex.flags || '') + (matcher.regex.flags.includes('g') ? '' : 'g');
            const re = new RegExp(matcher.regex.source, gFlags);
            return safeText.replace(re, m => `<strong style="color:var(--primary); text-decoration:underline">${m}</strong>`);
          } catch (e) {
            return safeText;
          }
        }

        const words = matcher.words;
        if (!words || words.length === 0) return safeText;
        const escaped = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).filter(Boolean);
        if (escaped.length === 0) return safeText;
        const pattern = new RegExp(`(${escaped.join('|')})`, matcher.isCaseSensitive ? 'g' : 'gi');
        return safeText.replace(pattern, '<strong style="color:var(--primary); text-decoration:underline">$1</strong>');
      }

      function isItemTypeAllowed(itemType, filterSet) {
        if (!filterSet || filterSet.has('all') || filterSet.size === 0) return true;
        if (itemType === 'method') {
          return filterSet.has('function') || filterSet.has('task') || filterSet.has('method');
        }
        return filterSet.has(itemType);
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
          renderSidebar();
        });
      });

      if (sidebarFilter) {
        sidebarFilter.addEventListener('input', (e) => {
          if (sidebarFilterClear) {
            sidebarFilterClear.style.display = e.target.value.length > 0 ? 'inline-flex' : 'none';
          }
          renderSidebar();
        });

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
        if (!sidebarContent || typeof UVM_DATA === 'undefined') return;
        const rawQuery = sidebarFilter ? sidebarFilter.value : '';

        if (activeSidebarTab === 'docs') {
          renderDocsMenu(rawQuery);
        } else if (activeSidebarTab === 'source') {
          renderSourceTree(rawQuery);
        } else if (activeSidebarTab === 'index') {
          renderAlphabeticalIndex(rawQuery);
        }
      }

      function renderDocsMenu(rawQuery) {
        const categories = UVM_DATA.categories || [];
        const matcher = getQueryMatcher(rawQuery, sidebarRegexEnabled, false, sidebarFilter);
        let html = '';

        categories.forEach(cat => {
          if (cat.type === 'file' || cat.type === 'index') {
            const matches = docItemMatchesMatcher(cat, matcher);
            if (matches) {
              const isActive = currentDocUrl.includes(cat.href);
              html += `<div class="nav-single-item">
            <a href="#" data-doc-href="${cat.href}" class="nav-item-link ${isActive ? 'active' : ''}">
              ${highlightMatch(cat.title, matcher)}
            </a>
          </div>`;
            }
          } else if (cat.type === 'group') {
            const subItems = filterGroupItems(cat.children || [], matcher);
            const groupTitleMatches = matcher && matcher.type === 'words' && matcher.words.every(w => cat.title.toLowerCase().includes(w));
            if (subItems.length > 0 || groupTitleMatches) {
              html += `<div class="nav-group">
            <div class="nav-group-header">
              <span>${highlightMatch(cat.title, matcher)}</span>
              <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
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
            const isActive = currentDocUrl.includes(item.href);
            out += `<li>
          <a href="#" data-doc-href="${item.href}" class="nav-item-link ${isActive ? 'active' : ''}">
            ${highlightMatch(item.title, matcher)}
          </a>
        </li>`;
          } else if (item.type === 'group') {
            out += `<div class="nav-group" style="margin-left: 0.5rem">
          <div class="nav-group-header" style="font-size:0.775rem;">
            <span>${highlightMatch(item.title, matcher)}</span>
            <svg class="nav-group-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
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
              const isActive = currentSrcUrl.includes(node.url);
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
                (item.type === 'task' ? 'badge-task' : 'badge-method')));
          const isMethodLike = item.type === 'function' || item.type === 'task' || item.type === 'method';
          const ownerInfo = item.category && isMethodLike ?
            `<span class="az-symbol-owner" style="font-size:0.68rem; color:var(--text-muted); margin-left:auto; margin-right:0.35rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:110px;">${highlightMatch(item.category, matcher)}</span>` : '';
          html += `<div class="nav-single-item">
            <a href="#" data-doc-href="${item.doc || ''}" data-src-href="${item.src || ''}" class="nav-item-link az-index-link" title="${item.desc || item.name}">
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
      // Left Sidebar Expand / Collapse All Controller
      // =========================================================================

      function updateSidebarToggleAllBtn() {
        if (!sidebarToggleAll) return;
        if (activeSidebarTab === 'index') {
          sidebarToggleAll.style.display = 'none';
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
        // Collapsible group headers
        sidebarContent.querySelectorAll('.nav-group-header').forEach(header => {
          header.addEventListener('click', () => {
            header.closest('.nav-group').classList.toggle('collapsed');
            updateSidebarToggleAllBtn();
          });
        });

        // Navigation links (doc & src)
        sidebarContent.querySelectorAll('[data-doc-href], [data-src-href]').forEach(link => {
          link.addEventListener('click', (e) => {
            e.preventDefault();
            const docHref = link.getAttribute('data-doc-href');
            const srcHref = link.getAttribute('data-src-href');
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
        const activeItem = sidebarContent.querySelector('.nav-item-link.active, .file-tree-item.active');
        if (activeItem) {
          let p = activeItem.closest('.nav-group');
          while (p) {
            p.classList.remove('collapsed');
            p = p.parentElement ? p.parentElement.closest('.nav-group') : null;
          }
        }

        updateSidebarToggleAllBtn();
      }

      function highlightActiveSidebar(url) {
        const baseUrl = url ? url.split('#')[0] : '';
        sidebarContent.querySelectorAll('.nav-item-link, .file-tree-item').forEach(el => {
          el.classList.remove('active');
          const docHref = el.getAttribute('data-doc-href');
          const srcHref = el.getAttribute('data-src-href');
          if ((docHref && baseUrl.includes(docHref)) || (srcHref && baseUrl.includes(srcHref))) {
            el.classList.add('active');
            let p = el.closest('.nav-group');
            while (p) {
              p.classList.remove('collapsed');
              p = p.parentElement ? p.parentElement.closest('.nav-group') : null;
            }
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
        if (modalSearchClear) modalSearchClear.style.display = 'none';
        if (modalSearchHeader) modalSearchHeader.classList.remove('regex-error');
        if (modalSearchRegex) modalSearchRegex.classList.remove('regex-error');
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
          if (searchInput && searchInput.value.length > 0) {
            e.preventDefault();
            searchInput.value = '';
            if (modalSearchClear) modalSearchClear.style.display = 'none';
            if (modalSearchHeader) modalSearchHeader.classList.remove('regex-error');
            if (modalSearchRegex) modalSearchRegex.classList.remove('regex-error');
            executeSearch('');
          } else {
            closeSearchModal();
          }
        }
      });

      if (searchModal) {
        searchModal.addEventListener('click', (e) => {
          if (e.target === searchModal) {
            closeSearchModal();
          }
        });
      }

      if (modalSearchClear) {
        modalSearchClear.addEventListener('click', () => {
          if (searchInput) {
            searchInput.value = '';
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
            executeSearch(searchInput ? searchInput.value : '');
          });
        });
      });

      if (searchInput) {
        searchInput.addEventListener('input', (e) => {
          if (modalSearchClear) {
            modalSearchClear.style.display = e.target.value.length > 0 ? 'inline-flex' : 'none';
          }
          executeSearch(e.target.value);
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
            e.preventDefault();
            if (searchSelectedIndex >= 0 && searchSelectedIndex < filteredSearchResults.length) {
              selectSearchResult(filteredSearchResults[searchSelectedIndex].item);
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
          } else if (e.key === 'Escape') {
            if (searchInput.value.length > 0) {
              e.preventDefault();
              e.stopPropagation();
              searchInput.value = '';
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

      function executeSearch(query) {
        if (!searchResults || typeof UVM_DATA === 'undefined') return;
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
        searchSelectedIndex = displayResults.length > 0 ? 0 : -1;

        let html = '';
        displayResults.forEach(({ item }, idx) => {
          const badgeClass = item.type === 'class' ? 'badge-class' :
            (item.type === 'macro' ? 'badge-macro' :
              (item.type === 'function' ? 'badge-function' :
                (item.type === 'task' ? 'badge-task' :
                  (item.type === 'method' ? 'badge-method' : 'badge-file'))));

          const isMethodLike = item.type === 'function' || item.type === 'task' || item.type === 'method';
          const categoryTag = item.category && isMethodLike ?
            `<span style="color:var(--text-muted); font-size:0.8rem; margin-right:0.35rem">${highlightMatch(item.category, matcher)} ::</span>` : '';

          html += `<li class="search-result-item ${idx === 0 ? 'selected' : ''}" data-index="${idx}">
            <div class="res-main">
              <div class="res-title-row" style="display:flex; align-items:center;">
                ${categoryTag}
                <span class="res-name">${highlightMatch(item.name, matcher)}</span>
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
            selectSearchResult(displayResults[idx].item);
          });
        });
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

