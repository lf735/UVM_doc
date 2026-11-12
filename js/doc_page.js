/**
 * UVM 1.2 Documentation Page Controller
 * Powered by Universal Page Controller (js/page_common.js).
 *
 * Handles documentation-specific capabilities:
 * - Derived Classes & Component Hierarchy Cards (initDerivedClasses)
 * - Inherited Methods & Elements Explorer with file:// JSONP bundles (initInheritedMethodsExplorer)
 */
(function initDocPage(global) {
  'use strict';

  const PC = global.PageCommon;
  if (!PC) {
    console.warn('PageCommon must be loaded before doc_page.js');
    return;
  }

  const escapeHtml = PC.escapeHtml;
  const getUvmSymbols = PC.getUvmSymbols;
  const ensureUvmSymbolsLoaded = PC.ensureUvmSymbolsLoaded;
  const expandAllRetractedAncestors = PC.expandAllRetractedAncestors;
  const findMatchingInheritedSection = PC.findMatchingInheritedSection;

  // =========================================================================
  // Derived Classes & Component Hierarchy Cards
  // =========================================================================

  function initDerivedClasses() {
    document.addEventListener('click', function (e) {
      const header = e.target.closest('.derived-classes-header');
      if (header) {
        const card = header.closest('.derived-classes-card, .hierarchy-subclasses-card');
        if (card) card.classList.toggle('collapsed');
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        const header = e.target.closest('.derived-classes-header');
        if (header) {
          e.preventDefault();
          const card = header.closest('.derived-classes-card, .hierarchy-subclasses-card');
          if (card) card.classList.toggle('collapsed');
        }
      }
    });

    // Handle click on derived-class-pill for exact in-page or cross-page jump
    document.addEventListener('click', function (e) {
      const pill = e.target.closest('.derived-class-pill, .hierarchy-flow-node.parent');
      if (!pill) return;
      const href = pill.getAttribute('href');
      if (!href || pill.classList.contains('src-code-link')) return;

      try {
        const targetUrl = new URL(href, window.location.href);
        const isSamePage = targetUrl.pathname === window.location.pathname;
        const hash = targetUrl.hash;

        if (isSamePage && hash) {
          e.preventDefault();
          history.pushState(null, '', hash);
          const raw = decodeURIComponent(hash.replace(/^#/, ''));
          window.postMessage({ type: 'scrollToSection', anchor: raw, id: raw }, '*');
          return;
        }

        if (window.parent && window.parent !== window) {
          e.preventDefault();
          const match = targetUrl.pathname.match(/(docs_view\/.*)$/);
          if (match) {
            const fullDocRel = match[1] + hash;
            window.parent.postMessage({ type: 'openDocView', url: fullDocRel }, '*');
            return;
          }
        }
      } catch (err) { }
    });

    try {
      const curHash = (window.location.hash || '').replace(/^#/, '');
      if (curHash) {
        const decHash = decodeURIComponent(curHash);
        const directTarget = document.getElementById(decHash) || document.querySelector('[name="' + CSS.escape(decHash) + '"]');
        if (directTarget) {
          expandAllRetractedAncestors(directTarget);
        }
      }
    } catch (e) { }
  }

  // =========================================================================
  // Inherited Methods & Elements Explorer (From Parent Docs, Oldest -> Newest)
  // =========================================================================

  const DOC_TOPIC_CACHE = Object.create(null);
  const DOC_TOPIC_WAITERS = Object.create(null);

  window.__registerUvmDocTopics = function (clsName, items) {
    DOC_TOPIC_CACHE[clsName] = Array.isArray(items) ? items : [];
    const waiters = DOC_TOPIC_WAITERS[clsName];
    if (waiters) {
      delete DOC_TOPIC_WAITERS[clsName];
      waiters.forEach(function (fn) {
        try { fn(DOC_TOPIC_CACHE[clsName]); } catch (e) { }
      });
    }
  };

  function getDocRootRel() {
    const cleanPath = window.location.pathname.replace(/\\/g, '/');
    const m = cleanPath.match(/docs_view\/(.*)$/);
    if (m && m[1]) {
      const parts = m[1].split('/').filter(Boolean);
      return '../'.repeat(parts.length);
    }
    return '../../';
  }

  function loadUvmDocTopics(clsName, rootRel) {
    if (Object.prototype.hasOwnProperty.call(DOC_TOPIC_CACHE, clsName)) {
      return Promise.resolve(DOC_TOPIC_CACHE[clsName]);
    }
    return new Promise(function (resolve) {
      if (!DOC_TOPIC_WAITERS[clsName]) {
        DOC_TOPIC_WAITERS[clsName] = [];
        const safeName = String(clsName).replace(/[^A-Za-z0-9_]/g, '_');
        const script = document.createElement('script');
        script.src = rootRel + 'js/doc_topics/' + safeName + '.js';
        script.async = true;
        script.onerror = function () {
          if (!Object.prototype.hasOwnProperty.call(DOC_TOPIC_CACHE, clsName)) {
            window.__registerUvmDocTopics(clsName, []);
          }
        };
        document.head.appendChild(script);
      }
      DOC_TOPIC_WAITERS[clsName].push(resolve);
    });
  }

  function initInheritedMethodsExplorer() {
    const hierarchyWidgets = document.querySelectorAll('.class-hierarchy-widget[data-cname]');
    if (!hierarchyWidgets.length) return;
    const syms = getUvmSymbols();
    if (!syms) {
      ensureUvmSymbolsLoaded(function (loaded) {
        if (loaded) initInheritedMethodsExplorer();
      });
      return;
    }

    const classParents = syms.classParents || {};
    const classDocMembers = syms.classDocMembers || {};
    const rootRel = getDocRootRel();

    hierarchyWidgets.forEach(function (hierarchyWidget) {
      if (hierarchyWidget.dataset.inheritedBound) return;
      hierarchyWidget.dataset.inheritedBound = '1';

      const cname = hierarchyWidget.getAttribute('data-cname');
      if (!cname) return;

      const cNode = classParents[cname];
      if (!cNode || !cNode.parent) return;

      const summaryEl = hierarchyWidget.closest('.Summary, .ClassSummary')
        || document.getElementById('doc-nav-summary-' + cname)
        || hierarchyWidget.closest('.CClass');
      if (!summaryEl || !summaryEl.parentNode) return;

      function resolveParentName(clsName) {
        const node = classParents[clsName];
        if (!node || !node.parent) return '';
        if (node.parent === 'BASE' && clsName === 'uvm_reg_sequence') return 'uvm_sequence';
        if (node.parent === 'IF' && clsName === 'uvm_port_base') return 'uvm_void';
        return node.parent;
      }

      // Build ancestor chain from direct parent upward to root
      const ancestorsNearestFirst = [];
      let curr = resolveParentName(cname);
      const visited = new Set([cname]);
      while (curr && !visited.has(curr)) {
        visited.add(curr);
        ancestorsNearestFirst.push(curr);
        curr = resolveParentName(curr);
      }
      if (!ancestorsNearestFirst.length) return;

      // Collect own documented/defined symbols on this class so redefined ones are excluded
      const ownNames = new Set(['new']);
      (classDocMembers[cname] || []).forEach(function (m) {
        if (m && m.n) ownNames.add(m.n);
      });
      summaryEl.querySelectorAll('.STable tr:not(.SGroup):not(.SClass):not(.SMain):not(.SHierarchy):not(.SPrototype) td.SEntry a').forEach(function (a) {
        const txt = (a.textContent || '').trim();
        if (txt) ownNames.add(txt);
      });

      // Deduplicate nearest-to-oldest (nearest ancestor wins when overridden in hierarchy)
      const seenNames = new Set(ownNames);
      const retainedByAncestor = new Map();
      ancestorsNearestFirst.forEach(function (anc) {
        const members = classDocMembers[anc] || [];
        const keep = [];
        const keepSet = new Set();
        members.forEach(function (m) {
          if (!m || !m.n || seenNames.has(m.n)) return;
          seenNames.add(m.n);
          keep.push(m.n);
          keepSet.add(m.n);
        });
        if (keep.length > 0) {
          retainedByAncestor.set(anc, { names: keep, nameSet: keepSet });
        }
      });

      if (retainedByAncestor.size === 0) return;

      // Display order: oldest ancestor -> most recent parent
      const ancestorsOldestFirst = ancestorsNearestFirst
        .slice()
        .reverse()
        .filter(function (anc) { return retainedByAncestor.has(anc); });

      let totalCount = 0;
      ancestorsOldestFirst.forEach(function (anc) {
        totalCount += retainedByAncestor.get(anc).names.length;
      });

      const inheritedSection = document.createElement('div');
      inheritedSection.className = 'inherited-methods-section inherited-doc-category';
      inheritedSection.id = 'doc-nav-inherited-' + cname.replace(/[^A-Za-z0-9_]/g, '_');
      inheritedSection.setAttribute('data-cname', cname);

      const inheritedPrefix = inheritedSection.id + '-';
      const inheritedTocItems = [];
      ancestorsOldestFirst.forEach(function (anc) {
        const retained = retainedByAncestor.get(anc);
        retained.names.forEach(function (name) {
          const safeName = name.replace(/[^A-Za-z0-9_]/g, '_');
          inheritedTocItems.push({
            id: inheritedPrefix + safeName,
            anchor: cname + '.' + name,
            derivedAnchor: cname + '.' + name,
            originAnchor: anc + '.' + name,
            title: name,
            originClass: anc,
            isGroupHeader: false,
            type: 'subitem',
            inheritedSectionId: inheritedSection.id
          });
        });
      });
      inheritedSection._inheritedTocItems = inheritedTocItems;
      inheritedSection._inheritedTocTitle = 'Inherited Methods & Elements';
      inheritedSection._ancestorList = ancestorsOldestFirst;
      inheritedSection.setAttribute('data-ancestors', ancestorsOldestFirst.join(' '));

      const ancestorAnchorsHtml = ancestorsOldestFirst.map(function (anc) {
        return `<a name="${escapeHtml(anc)}" id="${escapeHtml(anc)}" class="inherited-ancestor-anchor" style="display:block;position:relative;top:-24px;visibility:hidden;"></a>`;
      }).join('');

      const summaryBadgesHtml = ancestorsOldestFirst.map(function (anc) {
        const ancNode = classParents[anc] || {};
        const ancDocRaw = ancNode.doc || '';
        if (ancDocRaw) {
          return `<a class="inherited-origin-badge" href="${escapeHtml(rootRel + ancDocRaw)}" data-doc-href="${escapeHtml(ancDocRaw)}" title="Open ${escapeHtml(anc)} documentation">${escapeHtml(anc)}</a>`;
        }
        return `<span class="inherited-origin-badge">${escapeHtml(anc)}</span>`;
      }).join('<span class="inherited-summary-arrow" aria-hidden="true">&rarr;</span>');

      inheritedSection.innerHTML = `
        <a name="Inherited_Methods" id="Inherited_Methods" style="display:block;position:relative;top:-24px;visibility:hidden;"></a>
        <a name="inherited-methods" id="inherited-methods" style="display:block;position:relative;top:-24px;visibility:hidden;"></a>
        <a name="doc-nav-inherited" id="doc-nav-inherited" style="display:block;position:relative;top:-24px;visibility:hidden;"></a>
        ${ancestorAnchorsHtml}
        <div class="inherited-section-header" role="button" tabindex="0" aria-expanded="false" title="Click to expand inherited methods and elements (not overridden)">
          <div class="inherited-header-title">
            <svg class="inherited-chevron" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            <span>Inherited Methods &amp; Elements (${totalCount})</span>
          </div>
          <span class="inherited-summary-badge">${summaryBadgesHtml}</span>
        </div>
        <div class="inherited-section-content" style="display: none;">
          <div class="inherited-loading-state">Loading inherited documentation...</div>
        </div>`;

      summaryEl.parentNode.insertBefore(inheritedSection, summaryEl.nextSibling);

      const toggleBtn = inheritedSection.querySelector('.inherited-section-header');
      const contentBox = inheritedSection.querySelector('.inherited-section-content');
      const chevron = inheritedSection.querySelector('.inherited-chevron');
      let hasRendered = false;
      let isLoading = false;

      function renderUnifiedInheritedList() {
        const listEl = document.createElement('div');
        listEl.className = 'inherited-unified-list';
        const renderedNames = new Set();

        ancestorsOldestFirst.forEach(function (anc) {
          const retained = retainedByAncestor.get(anc);
          const items = DOC_TOPIC_CACHE[anc] || [];
          const ancNode = classParents[anc] || {};
          const ancDocRaw = ancNode.doc || '';

          items.forEach(function (item) {
            if (!item || !retained.nameSet.has(item.n) || renderedNames.has(item.n)) return;
            renderedNames.add(item.n);

            const entryWrap = document.createElement('div');
            entryWrap.className = 'inherited-topic-entry';
            entryWrap.id = inheritedPrefix + item.n.replace(/[^A-Za-z0-9_]/g, '_');
            entryWrap.setAttribute('data-origin-class', anc);
            entryWrap.setAttribute('data-anchor', cname + '.' + item.n);
            entryWrap.setAttribute('data-origin-anchor', anc + '.' + item.n);
            entryWrap.setAttribute('data-member-name', item.n);
            if (item.s) {
              entryWrap.setAttribute('data-src-url', rootRel + item.s);
            }

            const renderedHtml = (item.h || '').replace(/__ROOT_REL__/g, rootRel);
            entryWrap.innerHTML = `
              <a name="${escapeHtml(cname + '.' + item.n)}" id="${escapeHtml(cname + '.' + item.n)}" class="inherited-anchor-target" style="display:block;position:relative;top:-24px;visibility:hidden;"></a>
              <a name="${escapeHtml(anc + '.' + item.n)}" id="${escapeHtml(anc + '.' + item.n)}" class="inherited-anchor-target" style="display:block;position:relative;top:-24px;visibility:hidden;"></a>
              <a name="${escapeHtml(item.n)}" id="${escapeHtml(item.n)}" class="inherited-anchor-target" style="display:block;position:relative;top:-24px;visibility:hidden;"></a>
            ` + renderedHtml;

            const titleEl = entryWrap.querySelector('h3.CTitle, .CTitle');
            if (titleEl) {
              const textLabel = titleEl.textContent.trim();
              const srcUrl = item.s ? (rootRel + item.s) : '';

              const titleMain = document.createElement('span');
              titleMain.className = 'inherited-title-main';
              titleMain.innerHTML = `<a name="${escapeHtml(cname + '.' + item.n)}" id="${escapeHtml(cname + '.' + item.n)}" ${srcUrl ? `href="${escapeHtml(srcUrl)}" data-src-url="${escapeHtml(srcUrl)}" title="Open source definition"` : ''} class="src-code-link">${escapeHtml(textLabel)}</a>`;

              titleEl.innerHTML = '';
              titleEl.appendChild(titleMain);

              const exactDocRaw = item.d || ancDocRaw;
              if (exactDocRaw) {
                const metaRight = document.createElement('span');
                metaRight.className = 'inherited-title-meta';
                const originBadge = document.createElement('a');
                originBadge.className = 'inherited-origin-badge';
                originBadge.href = rootRel + exactDocRaw;
                originBadge.setAttribute('data-doc-href', exactDocRaw);
                originBadge.textContent = anc + '::' + item.n;
                originBadge.title = 'Open exact definition of ' + anc + '::' + item.n + ' in documentation';
                metaRight.appendChild(originBadge);
                titleEl.appendChild(metaRight);
              }
            }

            listEl.appendChild(entryWrap);
          });
        });

        contentBox.innerHTML = '';
        contentBox.appendChild(listEl);

        if (typeof global._scanHeadingAnchors === 'function') {
          global._scanHeadingAnchors(listEl);
        }

        listEl.addEventListener('click', function (ev) {
          if (ev.target.closest('.inherited-origin-badge') || ev.target.closest('.heading-anchor-btn')) return;
          const headerTitle = ev.target.closest('.inherited-topic-entry .CTitle');
          if (!headerTitle) return;
          if (ev.target.closest('a.src-code-link')) return;
          const srcAnchor = headerTitle.querySelector('a.src-code-link');
          if (srcAnchor) {
            ev.preventDefault();
            srcAnchor.click();
          }
        });
      }

      const pendingReadyCallbacks = [];

      function ensureExpandedAndRendered(onReady) {
        const isHidden = contentBox.style.display === 'none';
        if (isHidden) {
          contentBox.style.display = 'block';
          inheritedSection.classList.add('is-expanded');
          toggleBtn.setAttribute('aria-expanded', 'true');
          if (chevron) {
            chevron.style.transform = 'rotate(0deg)';
          }
        }
        if (hasRendered) {
          if (typeof onReady === 'function') onReady();
          return;
        }
        if (typeof onReady === 'function') {
          pendingReadyCallbacks.push(onReady);
        }
        if (!isLoading) {
          isLoading = true;
          Promise.all(ancestorsOldestFirst.map(function (anc) {
            return loadUvmDocTopics(anc, rootRel);
          })).then(function () {
            hasRendered = true;
            isLoading = false;
            renderUnifiedInheritedList();
            while (pendingReadyCallbacks.length > 0) {
              const cb = pendingReadyCallbacks.shift();
              try { cb(); } catch (err) { }
            }
          });
        }
      }

      inheritedSection._ensureExpandedAndRendered = ensureExpandedAndRendered;

      function toggleSection() {
        const isHidden = contentBox.style.display === 'none';
        if (isHidden) {
          ensureExpandedAndRendered();
        } else {
          contentBox.style.display = 'none';
          inheritedSection.classList.remove('is-expanded');
          toggleBtn.setAttribute('aria-expanded', 'false');
          if (chevron) {
            chevron.style.transform = 'rotate(-90deg)';
          }
        }
      }

      toggleBtn.addEventListener('click', function (e) {
        if (e.target.closest('.inherited-summary-badge .inherited-origin-badge')) return;
        toggleSection();
      });
      toggleBtn.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          toggleSection();
        }
      });
    });

    // Rebuild the right-hand TOC so the newly injected Inherited Methods & Elements section appears
    if (typeof PC.initTOC === 'function') {
      PC.initTOC();
    }

    // Replay any scrollToSection message that arrived before inherited sections existed
    const replayed = typeof PC.retryPendingSectionScroll === 'function' && PC.retryPendingSectionScroll();

    if (!replayed) {
      try {
        const curHash = (window.location.hash || '').replace(/^#/, '');
        if (curHash) {
          const decHash = decodeURIComponent(curHash);
          const inhMatch = findMatchingInheritedSection(decHash);
          if (inhMatch && typeof inhMatch._ensureExpandedAndRendered === 'function') {
            inhMatch._ensureExpandedAndRendered(function () {
              setTimeout(function () {
                window.postMessage({ type: 'scrollToSection', anchor: decHash, id: decHash }, '*');
              }, 60);
            });
          }
        }
      } catch (e) { }
    }
  }

  function initDocFeatures() {
    if (document.querySelector('.derived-classes-card, .derived-class-pill, .class-hierarchy-widget, .hierarchy-subclasses-card')) {
      initDerivedClasses();
      initInheritedMethodsExplorer();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDocFeatures);
  } else {
    initDocFeatures();
  }

  global.DocPage = {
    initDerivedClasses: initDerivedClasses,
    initInheritedMethodsExplorer: initInheritedMethodsExplorer
  };
})(window);
