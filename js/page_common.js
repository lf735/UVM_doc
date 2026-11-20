/**
 * UVM 1.2 Universal Page Controller (js/page_common.js)
 * Comprehensive, modular client engine for documentation pages, interactive example studios,
 * and future custom page types.
 *
 * Capabilities:
 * - Immediate Anti-FOUC Theme Initialization & Dynamic Theme Synchronization
 * - Interactive In-Page Table of Contents (TOC) & Smooth ScrollSpy
 * - Heading Deep-Link Anchor Generator & Canonical URL Copying
 * - Multi-File Code Studio (Tabs, Dropdown Selector, Line-Number Deep Links, Code Copy)
 * - Zero-Dependency Client-Side Native ZIP Generator (Pure JavaScript PKZip)
 * - Simulation Console (Simulator Command Switcher, Real-Time Log Filtering)
 * - Interactive Visual Flow Stepper (Execution progression, Topology & Code Studio Sync)
 * - Collapsible Subclasses & Component Hierarchy Cards
 * - Media Lightbox Triggers & Code Block Clipboard Utilities
 * - Robust Cross-Frame postMessage Routing & Standalone Frame Restoration
 */

// 1. Immediate Theme Initialization (executes synchronously to prevent flash of unstyled content)
(function initImmediateTheme() {
  try {
    const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
    const localTheme = localStorage.getItem('theme');
    const theme = parentTheme || localTheme;
    if (theme) {
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.style.colorScheme = theme;
    }
  } catch (e) { }
})();

// Create Universal Page Controller Namespace
window.PageCommon = (function () {
  'use strict';

  // =========================================================================
  // Central Cross-Frame Message Bus
  // =========================================================================

  const messageHandlers = [];
  let messageBusBound = false;

  function registerMessageHandler(handler) {
    if (typeof handler !== 'function') return;
    messageHandlers.push(handler);
    if (!messageBusBound) {
      messageBusBound = true;
      window.addEventListener('message', function (e) {
        if (!e.data || typeof e.data !== 'object') return;
        if (e.source && e.source !== window && e.source !== window.parent) return;
        for (let i = 0; i < messageHandlers.length; i++) {
          try {
            messageHandlers[i](e.data, e);
          } catch (err) { }
        }
      });
    }
  }

  function sendScrollAck(navToken, anchor, id) {
    if (typeof navToken !== 'number') return;
    try {
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({
          type: 'scrollAck',
          navToken: navToken,
          anchor: anchor,
          id: id
        }, '*');
      }
    } catch (e) { }
  }

  let uvmSymbolsWaiters = null;

  function getUvmSymbols() {
    if (window.UVM_SYMBOLS) return window.UVM_SYMBOLS;
    try {
      if (window.parent && window.parent !== window && window.parent.UVM_SYMBOLS) {
        window.UVM_SYMBOLS = window.parent.UVM_SYMBOLS;
        return window.UVM_SYMBOLS;
      }
    } catch (e) { }
    return null;
  }

  function ensureUvmSymbolsLoaded(cb) {
    const existing = getUvmSymbols();
    if (existing) {
      if (typeof cb === 'function') cb(existing);
      return;
    }
    if (!uvmSymbolsWaiters) {
      uvmSymbolsWaiters = [];
      const flushWaiters = function () {
        const syms = getUvmSymbols();
        const q = uvmSymbolsWaiters || [];
        uvmSymbolsWaiters = null;
        q.forEach(function (fn) {
          try { fn(syms); } catch (err) { }
        });
      };
      const existingTag = document.querySelector('script[src*="uvm_symbol_quick.js"]');
      if (existingTag) {
        existingTag.addEventListener('load', flushWaiters, { once: true });
        existingTag.addEventListener('error', flushWaiters, { once: true });
        setTimeout(flushWaiters, 1500);
      } else {
        const s = document.createElement('script');
        s.src = getDocRootRel() + 'js/uvm_symbol_quick.js';
        s.async = true;
        s.onload = flushWaiters;
        s.onerror = flushWaiters;
        document.head.appendChild(s);
      }
    }
    if (typeof cb === 'function') {
      uvmSymbolsWaiters.push(cb);
    }
  }

  // =========================================================================
  // Clipboard Utilities
  // =========================================================================

  function execCommandFallback(text) {
    return new Promise(function (resolve, reject) {
      try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        ta.style.top = '-9999px';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        const successful = document.execCommand('copy');
        document.body.removeChild(ta);
        if (successful) resolve();
        else reject(new Error('execCommand copy failed'));
      } catch (e) {
        reject(e);
      }
    });
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () {
        return execCommandFallback(text);
      });
    }
    return execCommandFallback(text);
  }

  function bindCopyFeedback(buttonEl, originalText, successText, duration) {
    if (!buttonEl) return;
    const delay = duration || 2000;

    // Check if the button has SVG icon(s)
    const existingSvg = buttonEl.querySelector('svg');
    const existingSpan = buttonEl.querySelector('span');

    if (existingSvg) {
      // Icon-based button (e.g., toolbar studio-action-btn)
      const origHtml = buttonEl.innerHTML;
      const checkSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';

      buttonEl.innerHTML = checkSvg + (existingSpan ? ' <span>' + (successText || 'Copied!') + '</span>' : '');
      buttonEl.classList.add('btn-copied');

      setTimeout(function () {
        buttonEl.innerHTML = origHtml;
        buttonEl.classList.remove('btn-copied');
      }, delay);
    } else {
      // Text-only button
      const orig = originalText || buttonEl.textContent || 'Copy';
      buttonEl.textContent = successText || 'Copied!';
      buttonEl.classList.add('btn-copied');
      setTimeout(function () {
        buttonEl.textContent = orig;
        buttonEl.classList.remove('btn-copied');
      }, delay);
    }
  }

  // =========================================================================
  // Theme Synchronization
  // =========================================================================

  function initTheme() {
    registerMessageHandler(function (data) {
      if (data.theme) {
        document.documentElement.setAttribute('data-theme', data.theme);
        document.documentElement.style.colorScheme = data.theme;
      }
    });

    try {
      const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
      if (parentTheme) {
        document.documentElement.setAttribute('data-theme', parentTheme);
        document.documentElement.style.colorScheme = parentTheme;
      }
    } catch (e) { }
  }

  // =========================================================================
  // Retracted Zone & Collapsible Hierarchy Utilities
  // =========================================================================

  function expandAllRetractedAncestors(targetEl) {
    if (!targetEl || !targetEl.parentElement) return;
    let curr = targetEl;
    while (curr && curr !== document.body && curr !== document.documentElement) {
      // 1. Inherited methods section
      if (curr.classList && curr.classList.contains('inherited-methods-section')) {
        if (typeof curr._ensureExpandedAndRendered === 'function') {
          curr._ensureExpandedAndRendered();
        } else {
          const contentBox = curr.querySelector('.inherited-section-content');
          if (contentBox) contentBox.style.display = 'block';
          curr.classList.add('is-expanded');
          const toggleBtn = curr.querySelector('.inherited-section-header');
          if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'true');
          const chevron = curr.querySelector('.inherited-chevron');
          if (chevron) chevron.style.transform = 'rotate(0deg)';
        }
      }

      // 2. Derived classes card & hierarchy subclasses card
      if (curr.classList && (curr.classList.contains('derived-classes-card') || curr.classList.contains('hierarchy-subclasses-card'))) {
        curr.classList.remove('collapsed');
        const list = curr.querySelector('.derived-classes-list');
        if (list && list.style.display === 'none') {
          list.style.display = '';
        }
      }

      // 3. Native HTML5 details element
      if (curr.tagName === 'DETAILS' && !curr.open) {
        curr.open = true;
      }

      // 4. Any container with collapsed class
      if (curr.classList && curr.classList.contains('collapsed')) {
        curr.classList.remove('collapsed');
      }

      // 5. Elements with aria-expanded="false"
      if (curr.getAttribute && curr.getAttribute('aria-expanded') === 'false') {
        curr.setAttribute('aria-expanded', 'true');
      }

      // 6. Hidden elements or inline display: none
      if (curr.getAttribute && curr.hasAttribute('hidden')) {
        curr.removeAttribute('hidden');
      }
      if (curr.style && curr.style.display === 'none') {
        curr.style.display = '';
      }

      // 7. Accordion buttons controlling this element via aria-controls
      if (curr.id) {
        try {
          const controller = document.querySelector('[aria-controls="' + CSS.escape(curr.id) + '"]');
          if (controller && controller.getAttribute('aria-expanded') === 'false') {
            controller.setAttribute('aria-expanded', 'true');
          }
        } catch (e) { }
      }

      curr = curr.parentElement;
    }
  }

  function findMatchingInheritedSection(targetId) {
    if (!targetId) return null;
    const cleanId = decodeURIComponent(String(targetId).replace(/^#/, '')).trim();
    if (!cleanId) return null;

    const allInhSecs = Array.from(document.querySelectorAll('.inherited-methods-section'));
    if (!allInhSecs.length) return null;

    allInhSecs.sort(function (a, b) {
      return (b.id ? b.id.length : 0) - (a.id ? a.id.length : 0);
    });

    const cleanLower = cleanId.toLowerCase();

    // 1. Direct ID match or generic inherited anchor match
    const isGenericInherited = (
      cleanLower === 'inherited_methods' ||
      cleanLower === 'inherited-methods' ||
      cleanLower === 'inherited_elements' ||
      cleanLower === 'inherited-elements' ||
      cleanLower === 'doc-nav-inherited' ||
      cleanLower.startsWith('doc-nav-inherited')
    );

    for (let s = 0; s < allInhSecs.length; s++) {
      const sec = allInhSecs[s];
      if (sec && typeof sec._ensureExpandedAndRendered === 'function') {
        if (cleanId === sec.id || cleanId.indexOf(sec.id + '-') === 0 || isGenericInherited) {
          return sec;
        }
      }
    }

    // 2. Ancestor class name match (e.g. targetId = "uvm_report_object" or "uvm_object")
    for (let s = 0; s < allInhSecs.length; s++) {
      const sec = allInhSecs[s];
      if (!sec || typeof sec._ensureExpandedAndRendered !== 'function') continue;

      if (Array.isArray(sec._ancestorList) && sec._ancestorList.includes(cleanId)) {
        return sec;
      }
      if (Array.isArray(sec._inheritedTocItems)) {
        const hasAnc = sec._inheritedTocItems.some(function (it) {
          return it.originClass === cleanId;
        });
        if (hasAnc) return sec;
      }
    }

    // 3. Class.member format (e.g. "uvm_report_object.get_report_handler" or "uvm_component.get_report_handler")
    const dotIdx = cleanId.lastIndexOf('.');
    if (dotIdx !== -1) {
      const rawCls = cleanId.slice(0, dotIdx).trim();
      const rawMember = cleanId.slice(dotIdx + 1).trim();
      const safeCls = rawCls.replace(/\s*#\(.*?\)/g, '').replace(/[^A-Za-z0-9_]/g, '_');
      const expectedSecId = 'doc-nav-inherited-' + safeCls;

      for (let s = 0; s < allInhSecs.length; s++) {
        const sec = allInhSecs[s];
        if (!sec || typeof sec._ensureExpandedAndRendered !== 'function') continue;
        if (Array.isArray(sec._inheritedTocItems)) {
          const isTargetSec = (sec.id === expectedSecId ||
            sec.getAttribute('data-cname') === rawCls ||
            sec.getAttribute('data-cname') === safeCls ||
            (Array.isArray(sec._ancestorList) && sec._ancestorList.includes(rawCls)));

          const hasMatch = sec._inheritedTocItems.some(function (it) {
            return it.anchor === cleanId ||
              it.derivedAnchor === cleanId ||
              it.originAnchor === cleanId ||
              (isTargetSec && it.title === rawMember) ||
              (it.title === rawMember && (it.originClass === rawCls || it.originClass === safeCls));
          });
          if (hasMatch) return sec;
        }
      }
    }

    // 4. Member-only fallback (e.g. "get_report_handler" or "use_uvm_seeding")
    const memberPart = dotIdx !== -1 ? cleanId.slice(dotIdx + 1).trim() : cleanId;
    for (let s = 0; s < allInhSecs.length; s++) {
      const sec = allInhSecs[s];
      if (!sec || typeof sec._ensureExpandedAndRendered !== 'function') continue;
      if (Array.isArray(sec._inheritedTocItems)) {
        const hasMember = sec._inheritedTocItems.some(function (it) {
          return it.title === memberPart;
        });
        if (hasMember) return sec;
      }
    }

    return null;
  }

  // Pending scrollToSection target (replayed once doc_page.js injects inherited sections)
  let pendingSectionScroll = null;

  function retryPendingSectionScroll() {
    if (!pendingSectionScroll) return false;
    const req = pendingSectionScroll;
    pendingSectionScroll = null;
    window.postMessage({ type: 'scrollToSection', anchor: req.anchor, id: req.id, navToken: req.navToken }, '*');
    return true;
  }

  // =========================================================================
  // Sticky Breadcrumbs Metrics & Pinned State
  // =========================================================================

  function getBreadcrumbsHeight() {
    const bc = document.querySelector('.doc-breadcrumbs');
    if (!bc) return 0;
    const rect = bc.getBoundingClientRect();
    return rect.height > 0 ? Math.ceil(rect.height) : 0;
  }

  function initBreadcrumbs() {
    const bc = document.querySelector('.doc-breadcrumbs');
    if (!bc) {
      document.documentElement.style.setProperty('--doc-breadcrumbs-height', '0px');
      return;
    }

    function syncMetrics() {
      const h = getBreadcrumbsHeight();
      document.documentElement.style.setProperty('--doc-breadcrumbs-height', h + 'px');
    }

    function syncPinned() {
      const scrollY = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
      const rect = bc.getBoundingClientRect();
      bc.classList.toggle('is-pinned', scrollY > 4 && rect.top <= 1);
    }

    syncMetrics();
    syncPinned();

    if (typeof ResizeObserver === 'function') {
      if (window._uvmBreadcrumbsResizeObserver) {
        window._uvmBreadcrumbsResizeObserver.disconnect();
      }
      window._uvmBreadcrumbsResizeObserver = new ResizeObserver(function () {
        syncMetrics();
        syncPinned();
      });
      window._uvmBreadcrumbsResizeObserver.observe(bc);
    }

    if (window._uvmBreadcrumbsResizeHandler) {
      window.removeEventListener('resize', window._uvmBreadcrumbsResizeHandler);
    }
    window._uvmBreadcrumbsResizeHandler = function () {
      syncMetrics();
      syncPinned();
    };
    window.addEventListener('resize', window._uvmBreadcrumbsResizeHandler, { passive: true });

    if (window._uvmBreadcrumbsScrollHandler) {
      window.removeEventListener('scroll', window._uvmBreadcrumbsScrollHandler);
    }
    window._uvmBreadcrumbsScrollHandler = syncPinned;
    window.addEventListener('scroll', window._uvmBreadcrumbsScrollHandler, { passive: true });
  }

  // =========================================================================
  // Table of Contents (TOC) & ScrollSpy
  // =========================================================================

  function initTOC() {
    const contentEl = document.getElementById('Content');
    const tocSidebar = document.getElementById('doc-toc-sidebar');
    const tocNav = document.getElementById('doc-toc-nav');
    const toggleAllBtn = document.getElementById('doc-toc-toggle-all');
    if (!contentEl || !tocSidebar || !tocNav) return;

    const tocInner = tocSidebar.querySelector('.doc-toc-inner');
    if (tocInner && !tocInner.id) {
      tocInner.id = 'doc-toc-inner';
    }
    let mobileTriggerBtn = document.getElementById('doc-toc-mobile-trigger');
    if (!mobileTriggerBtn && tocInner) {
      mobileTriggerBtn = document.createElement('button');
      mobileTriggerBtn.className = 'doc-toc-mobile-trigger';
      mobileTriggerBtn.id = 'doc-toc-mobile-trigger';
      mobileTriggerBtn.type = 'button';
      mobileTriggerBtn.setAttribute('aria-expanded', 'false');
      mobileTriggerBtn.setAttribute('aria-controls', 'doc-toc-inner');
      mobileTriggerBtn.title = 'Toggle table of contents';
      mobileTriggerBtn.innerHTML =
        '<span class="doc-toc-mobile-left">' +
        '<svg class="doc-toc-mobile-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>' +
        '<line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>' +
        '</svg>' +
        '<span class="doc-toc-mobile-label">On this page</span>' +
        '<span class="doc-toc-mobile-sep" aria-hidden="true">&rsaquo;</span>' +
        '<span class="doc-toc-mobile-current" id="doc-toc-mobile-current">Overview</span>' +
        '</span>' +
        '<svg class="doc-toc-mobile-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<polyline points="6 9 12 15 18 9"/>' +
        '</svg>';
      tocSidebar.insertBefore(mobileTriggerBtn, tocInner);
    }
    const mobileCurrentEl = document.getElementById('doc-toc-mobile-current');

    let topicSeq = 0;
    const tocEntries = [];
    const allGroups = [];
    let currentGroup = null;

    function extractHeadingTitle(el, fallback) {
      if (!el) return fallback || '';
      const clone = el.cloneNode(true);
      clone.querySelectorAll('.heading-anchor-btn, .anchor-copy-tooltip').forEach(function (n) {
        n.remove();
      });
      const txt = (clone.innerText || clone.textContent || '').trim();
      return txt || fallback || '';
    }

    // Helper to process any inherited section and attach its items
    const processedInheritedSections = new Set();
    function createInheritedGroupEntry(sec) {
      if (!sec || !sec.id || processedInheritedSections.has(sec.id)) return null;
      if (!Array.isArray(sec._inheritedTocItems) || sec._inheritedTocItems.length === 0) return null;
      processedInheritedSections.add(sec.id);
      return {
        id: sec.id,
        anchor: sec.id,
        title: sec._inheritedTocTitle || 'Inherited Methods & Elements',
        el: sec,
        items: sec._inheritedTocItems,
        isInheritedGroup: true
      };
    }

    // 1. Process Main Topic & top-level summary/inherited section
    const mainTopicEl = contentEl.querySelector('#MainTopic');
    if (mainTopicEl) {
      const mainTitleEl = mainTopicEl.querySelector('.CTitle, h1, h2');
      if (mainTitleEl) {
        const safeId = 'doc-nav-main';
        if (!mainTitleEl.id) mainTitleEl.id = 'doc-nav-main-title';
        const mainA = mainTitleEl.querySelector('a[name]');
        const mainAnchor = mainA ? mainA.getAttribute('name') : 'MainTopic';
        mainTitleEl.setAttribute('data-anchor', mainAnchor);
        tocEntries.push({
          kind: 'item',
          data: {
            id: safeId,
            anchor: mainAnchor,
            title: extractHeadingTitle(mainTitleEl, 'Overview'),
            type: 'main',
            el: mainTitleEl
          }
        });
      }

      // Check for Summary inside MainTopic
      const topSummaryEl = mainTopicEl.querySelector('.Summary, .ContentsSummary') || contentEl.querySelector('.Summary, .ContentsSummary');
      if (topSummaryEl) {
        const sTitleEl = topSummaryEl.querySelector('.STitle');
        const sTitleText = extractHeadingTitle(sTitleEl, '');
        const isContents = sTitleText.toLowerCase() === 'contents';
        const safeId = isContents ? 'doc-nav-contents' : 'doc-nav-summary';
        const safeAnchor = isContents ? 'Contents' : 'Summary';
        const label = isContents ? 'Contents' : 'Summary';

        topSummaryEl.id = topSummaryEl.id || safeId;
        const resolvedSummaryAnchor = topSummaryEl.getAttribute('data-anchor') || safeAnchor;
        topSummaryEl.setAttribute('data-anchor', resolvedSummaryAnchor);
        tocEntries.push({
          kind: 'item',
          data: {
            id: topSummaryEl.id,
            anchor: resolvedSummaryAnchor,
            title: label,
            type: isContents ? 'contents' : 'summary',
            el: topSummaryEl
          }
        });
      }

      // Check for Inherited Methods section inside MainTopic (or directly attached after summary)
      const inhSecInMain = mainTopicEl.querySelector('.inherited-methods-section') || (topSummaryEl && topSummaryEl.parentNode && topSummaryEl.parentNode.querySelector('.inherited-methods-section'));
      if (inhSecInMain) {
        const inhGroup = createInheritedGroupEntry(inhSecInMain);
        if (inhGroup) {
          tocEntries.push({ kind: 'group', data: inhGroup, el: inhGroup.el });
          allGroups.push(inhGroup);
        }
      }
    }

    // 2. Scan all topics under #Content (excluding #doc-nav-main / MainTopic)
    const topicWrappers = contentEl.querySelectorAll('#Content > div, #Content > details.internal-details-section');

    topicWrappers.forEach(function (wrap) {
      if (wrap.id === 'doc-nav-main' || wrap.querySelector('#MainTopic')) return;

      if (wrap.matches && wrap.matches('details.internal-details-section')) {
        const intId = wrap.id || ('doc-nav-internal-' + (++topicSeq));
        wrap.id = intId;
        const headerSpan = wrap.querySelector('.internal-header-title > span:last-child');
        const rawIntTitle = headerSpan ? headerSpan.textContent.replace(/\s*\(\d+\)\s*$/, '').trim() : 'Internal Details';
        const intGroup = {
          id: intId,
          anchor: intId,
          title: rawIntTitle,
          el: wrap,
          items: [],
          isCollapsedByDefault: true
        };
        wrap.querySelectorAll('.internal-section-body > div').forEach(function (subEl) {
          const subTitleEl = subEl.querySelector('.CTitle');
          const subTitle = extractHeadingTitle(subTitleEl, '');
          if (!subTitle) return;
          const subId = subEl.id || subEl.getAttribute('data-doc-topic') || ('doc-nav-item-' + (++topicSeq));
          subEl.id = subId;
          subEl.setAttribute('data-doc-topic', subId);
          const subAnchor = subEl.getAttribute('data-anchor') || subId;
          intGroup.items.push({
            id: subId,
            anchor: subAnchor,
            title: subTitle,
            el: subEl,
            isGroupHeader: false,
            type: 'subitem'
          });
        });
        if (intGroup.items.length > 0) {
          tocEntries.push({ kind: 'group', data: intGroup, el: wrap });
          allGroups.push(intGroup);
        }
        return;
      }

      const cls = wrap.className || '';
      const isCClass = cls.indexOf('CClass') !== -1 || cls.indexOf('CSection') !== -1;
      const isCGroup = cls.indexOf('CGroup') !== -1;

      const topic = wrap.querySelector('.CTopic');
      if (!topic) return;

      const titleEl = topic.querySelector('.CTitle');
      if (!titleEl) return;
      const rawTitle = extractHeadingTitle(titleEl, '');
      if (!rawTitle) return;

      const safeId = wrap.id || wrap.getAttribute('data-doc-topic') || ('doc-nav-item-' + (++topicSeq));
      wrap.id = safeId;
      wrap.setAttribute('data-doc-topic', safeId);
      if (topic) topic.id = topic.id || (safeId + '-topic');

      const aTag = wrap.querySelector('a[name]');
      const aName = wrap.getAttribute('data-anchor') || (aTag ? aTag.getAttribute('name') : '');
      if (aName) {
        wrap.setAttribute('data-anchor', aName);
      }

      // Multi-class / multi-section page: encountering another class/section
      if (isCClass) {
        currentGroup = null;
        tocEntries.push({
          kind: 'item',
          data: {
            id: safeId,
            anchor: aName || safeId,
            title: rawTitle,
            type: 'class-header',
            el: wrap
          }
        });

        // Check if this class has its own Summary table
        const classSummary = wrap.querySelector('.Summary, .ClassSummary');
        if (classSummary) {
          classSummary.id = classSummary.id || ('doc-nav-summary-' + safeId);
          classSummary.setAttribute('data-anchor', classSummary.getAttribute('data-anchor') || (aName ? (aName + '.Summary') : 'Summary'));
          tocEntries.push({
            kind: 'item',
            data: {
              id: classSummary.id,
              anchor: classSummary.getAttribute('data-anchor') || classSummary.id,
              title: 'Summary',
              type: 'summary',
              el: classSummary
            }
          });
        }

        // Check if this class has an Inherited section
        const classInhSec = wrap.querySelector('.inherited-methods-section');
        if (classInhSec) {
          const inhGroup = createInheritedGroupEntry(classInhSec);
          if (inhGroup) {
            tocEntries.push({ kind: 'group', data: inhGroup, el: inhGroup.el });
            allGroups.push(inhGroup);
          }
        }
        return;
      }

      // Group header (Ports, Methods, Configuration Interface, etc.)
      if (isCGroup) {
        currentGroup = {
          id: safeId,
          anchor: aName || safeId,
          title: rawTitle,
          el: wrap,
          items: []
        };
        tocEntries.push({ kind: 'group', data: currentGroup, el: wrap });
        allGroups.push(currentGroup);
        return;
      }

      // Member topic (CPort, CMethod, CVariable, etc.)
      const itemObj = {
        id: safeId,
        anchor: aName || safeId,
        title: rawTitle,
        el: wrap,
        isGroupHeader: false,
        type: 'subitem'
      };

      if (currentGroup) {
        currentGroup.items.push(itemObj);
      } else {
        // Standalone topic defined before any CGroup (e.g. `new` in uvm_component)
        tocEntries.push({ kind: 'item', data: itemObj, el: wrap });
      }
    });

    // 3. Fallback for any uncaptured inherited sections
    contentEl.querySelectorAll('.inherited-methods-section').forEach(function (sec) {
      const inhGroup = createInheritedGroupEntry(sec);
      if (inhGroup) {
        let insertIdx = -1;
        for (let i = tocEntries.length - 1; i >= 0; i--) {
          const entryEl = tocEntries[i].el;
          if (entryEl && (entryEl.compareDocumentPosition(sec) & Node.DOCUMENT_POSITION_FOLLOWING)) {
            insertIdx = i + 1;
            break;
          }
        }
        if (insertIdx !== -1) {
          tocEntries.splice(insertIdx, 0, { kind: 'group', data: inhGroup, el: inhGroup.el });
        } else {
          tocEntries.push({ kind: 'group', data: inhGroup, el: inhGroup.el });
        }
        allGroups.push(inhGroup);
      }
    });

    const totalItemsCount = tocEntries.length + allGroups.reduce(function (acc, g) { return acc + g.items.length; }, 0);
    if (totalItemsCount <= 1) {
      tocSidebar.style.display = 'none';
      return;
    }

    if (toggleAllBtn) {
      toggleAllBtn.style.display = (allGroups.length === 0) ? 'none' : 'inline-flex';
    }

    // Render TOC HTML as a single continuous list
    let tocHtml = '<ul class="doc-toc-list">';

    tocEntries.forEach(function (entry) {
      if (entry.kind === 'item') {
        const item = entry.data;
        const cleanTitle = item.title.replace(/"/g, '&quot;');
        const typeCls = item.type ? (' doc-toc-type-' + item.type) : '';
        const isMono = item.type === 'subitem' ? ' doc-toc-subitem' : '';
        const itemAnchorAttr = item.anchor ? ' data-anchor="' + escapeHtml(item.anchor) + '"' : '';
        const itemHref = escapeHtml(item.anchor || item.id);
        tocHtml += '<li class="doc-toc-item' + typeCls + isMono + '">';
        tocHtml += '<a href="#' + itemHref + '" data-target-id="' + item.id + '"' + itemAnchorAttr + ' class="doc-toc-link" title="' + cleanTitle + '">';
        tocHtml += cleanTitle;
        tocHtml += '</a></li>';
        return;
      }

      const group = entry.data;
      const cleanGroupTitle = group.title.replace(/"/g, '&quot;');
      const hasSubItems = group.items.length > 0;
      const defaultCollapsedCls = (hasSubItems && (group.isInheritedGroup || group.isCollapsedByDefault)) ? ' collapsed' : '';
      const groupAnchorAttr = group.anchor ? ' data-anchor="' + escapeHtml(group.anchor) + '"' : '';
      const groupHref = escapeHtml(group.anchor || group.id);
      tocHtml += '<li class="doc-toc-item doc-toc-group-item doc-toc-group-block' + (hasSubItems ? '' : ' no-children') + defaultCollapsedCls + '" id="block-' + group.id + '">';
      tocHtml += '<div class="doc-toc-group-header">';
      if (hasSubItems) {
        tocHtml += '<button class="doc-toc-chevron-btn" type="button" aria-label="Toggle group ' + cleanGroupTitle + '" title="Toggle group">';
        tocHtml += '<svg class="doc-toc-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
        tocHtml += '</button>';
      } else {
        tocHtml += '<span class="doc-toc-dot-indicator"></span>';
      }
      tocHtml += '<a href="#' + groupHref + '" data-target-id="' + group.id + '"' + groupAnchorAttr + ' class="doc-toc-link doc-toc-group-title" title="' + cleanGroupTitle + '">';
      tocHtml += cleanGroupTitle;
      tocHtml += '</a>';
      if (hasSubItems) {
        tocHtml += '<span class="doc-toc-badge">' + group.items.length + '</span>';
      }
      tocHtml += '</div>';

      if (hasSubItems) {
        tocHtml += '<ul class="doc-toc-subitems">';
        group.items.forEach(function (sub) {
          const cleanSubTitle = sub.title.replace(/"/g, '&quot;');
          const extraCls = sub.isGroupHeader ? ' doc-toc-subgroup-header' : '';
          const inhAttr = sub.inheritedSectionId ? ' data-inherited-section-id="' + sub.inheritedSectionId + '"' : '';
          const anchorAttr = sub.anchor ? ' data-anchor="' + escapeHtml(sub.anchor) + '"' : '';
          const subHref = escapeHtml(sub.anchor || sub.id);
          tocHtml += '<li class="doc-toc-item doc-toc-subitem' + extraCls + '">';
          tocHtml += '<a href="#' + subHref + '" data-target-id="' + sub.id + '"' + inhAttr + anchorAttr + ' class="doc-toc-link' + (sub.isGroupHeader ? ' doc-toc-subgroup-link' : '') + '" title="' + cleanSubTitle + '">';
          tocHtml += cleanSubTitle;
          tocHtml += '</a></li>';
        });
        tocHtml += '</ul>';
      }
      tocHtml += '</li>';
    });

    tocHtml += '</ul>';
    tocNav.innerHTML = tocHtml;

    if (typeof wildcardManifest !== 'undefined' && wildcardManifest && currentWildcardVariant) {
      const curPat = wildcardManifest.pattern;
      const w = document.createTreeWalker(tocNav, NodeFilter.SHOW_TEXT, null);
      let tn;
      while ((tn = w.nextNode())) {
        if (tn.nodeValue && tn.nodeValue.indexOf(currentWildcardVariant) !== -1) {
          tn.__wildcardOrig = tn.nodeValue.split(currentWildcardVariant).join(curPat);
        }
      }
      tocNav.querySelectorAll('a.doc-toc-link[title]').forEach(a => {
        const t = a.getAttribute('title') || '';
        if (t.indexOf(currentWildcardVariant) !== -1) {
          a.dataset.wildcardOrigTitle = t.split(currentWildcardVariant).join(curPat);
        }
      });
    }
    if (typeof wildcardManifest !== 'undefined' && wildcardManifest && currentWildcardVariant) {
      applyWildcardVariant(currentWildcardVariant, false);
    }

    const allNavItems = [];
    tocEntries.forEach(function (entry) {
      if (entry.kind === 'item') {
        const item = entry.data;
        const link = tocNav.querySelector('.doc-toc-link[data-target-id="' + item.id + '"]');
        allNavItems.push({ id: item.id, anchor: item.anchor || item.id, title: item.title, el: item.el, link: link });
      } else {
        const group = entry.data;
        const groupLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + group.id + '"]');
        allNavItems.push({ id: group.id, anchor: group.anchor || group.id, title: group.title, el: group.el, link: groupLink });
        group.items.forEach(function (sub) {
          const subLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + sub.id + '"]');
          allNavItems.push({ id: sub.id, anchor: sub.anchor || sub.id, title: sub.title, el: sub.el, link: subLink });
        });
      }
    });

    let isManualScrolling = false;
    let manualScrollTimer = null;
    let pendingTargetEl = null;

    function isCompactTocMode() {
      return window.innerWidth <= 1000 && tocSidebar && tocSidebar.style.display !== 'none';
    }

    function getScrollOffset() {
      return getBreadcrumbsHeight() + (isCompactTocMode() ? 56 : 24);
    }

    function updateMobileCurrentLabel(title) {
      if (!mobileCurrentEl || !title) return;
      if (typeof wildcardManifest !== 'undefined' && wildcardManifest) {
        let orig = title;
        if (currentWildcardVariant && orig.indexOf(currentWildcardVariant) !== -1) {
          orig = orig.split(currentWildcardVariant).join(wildcardManifest.pattern);
        }
        if (orig.indexOf(wildcardManifest.pattern) !== -1) {
          mobileCurrentEl.dataset.wildcardOrig = orig;
          mobileCurrentEl.textContent = currentWildcardVariant
            ? orig.split(wildcardManifest.pattern).join(currentWildcardVariant)
            : orig;
          return;
        }
        delete mobileCurrentEl.dataset.wildcardOrig;
      }
      mobileCurrentEl.textContent = title;
    }

    function updatePinnedState() {
      if (!tocSidebar) return;
      if (!isCompactTocMode()) {
        tocSidebar.classList.remove('is-pinned');
        return;
      }
      const rect = tocSidebar.getBoundingClientRect();
      tocSidebar.classList.toggle('is-pinned', rect.top <= getBreadcrumbsHeight() + 12);
    }

    function onManualScrollDone() {
      isManualScrolling = false;
      pendingTargetEl = null;
      updateScrollSpy();
      updatePinnedState();
    }

    function startManualScroll(duration) {
      isManualScrolling = true;
      clearTimeout(manualScrollTimer);
      manualScrollTimer = setTimeout(checkAndCorrectScroll, duration || 1800);
    }

    function getTargetScrollY(targetEl) {
      if (!targetEl) return 0;
      const rect = targetEl.getBoundingClientRect();
      const currentScroll = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
      return Math.max(0, currentScroll + rect.top - getScrollOffset());
    }

    function performScroll(targetY, instant) {
      const behavior = instant ? 'auto' : 'smooth';
      try {
        window.scrollTo({ top: targetY, behavior: behavior });
      } catch (e) {
        window.scrollTo(0, targetY);
      }
    }

    let lastHighlightEl = null;
    let lastHighlightTime = 0;

    function triggerTargetHighlight(targetEl) {
      if (!targetEl) return;
      let elToHighlight = targetEl;
      if (elToHighlight.classList && elToHighlight.classList.contains('inherited-methods-section')) {
        elToHighlight = elToHighlight.querySelector('.inherited-section-header') || elToHighlight;
      } else if (elToHighlight.tagName === 'A' || elToHighlight.tagName === 'SPAN') {
        const wrap = elToHighlight.closest('.inherited-topic-entry') ||
          elToHighlight.closest('.inherited-section-header') ||
          elToHighlight.closest('#Content > div') ||
          elToHighlight.closest('tr') ||
          elToHighlight.closest('.CTopic') ||
          elToHighlight;
        elToHighlight = wrap;
      }

      const now = Date.now();
      // Remove any lingering browser focus ring from anchor tags or buttons
      if (document.activeElement && document.activeElement !== document.body &&
        document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        try {
          document.activeElement.blur();
        } catch (e) { }
      }

      // Prevent double animation / overlapping if triggered repeatedly within 1.2s
      if (lastHighlightEl === elToHighlight && (now - lastHighlightTime) < 1200) {
        return;
      }
      lastHighlightEl = elToHighlight;
      lastHighlightTime = now;

      document.querySelectorAll('.doc-target-highlight').forEach(function (prev) {
        if (prev !== elToHighlight) {
          prev.classList.remove('doc-target-highlight');
          if (prev._hlTimer) {
            clearTimeout(prev._hlTimer);
            delete prev._hlTimer;
          }
        }
      });

      elToHighlight.classList.remove('doc-target-highlight');
      // Force synchronous reflow so browser plays the keyframe animation cleanly
      void elToHighlight.offsetWidth;
      elToHighlight.classList.add('doc-target-highlight');

      if (elToHighlight._hlTimer) {
        clearTimeout(elToHighlight._hlTimer);
      }
      elToHighlight._hlTimer = setTimeout(function () {
        elToHighlight.classList.remove('doc-target-highlight');
        delete elToHighlight._hlTimer;
        if (lastHighlightEl === elToHighlight) {
          lastHighlightEl = null;
        }
      }, 1650);
    }

    function checkAndCorrectScroll() {
      if (!pendingTargetEl) {
        onManualScrollDone();
        return;
      }
      const targetEl = pendingTargetEl;
      const currentScroll = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
      const adjustedY = getTargetScrollY(targetEl);
      if (Math.abs(adjustedY - currentScroll) > 6) {
        performScroll(adjustedY, true);
        pendingTargetEl = null;
        setTimeout(onManualScrollDone, 60);
      } else {
        onManualScrollDone();
      }
    }

    function scrollToElement(targetEl) {
      if (!targetEl) return;
      if (targetEl === document.body || targetEl === document.documentElement) {
        performScroll(0);
        return;
      }
      expandAllRetractedAncestors(targetEl);
      const targetY = getTargetScrollY(targetEl);
      const currentScroll = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
      const distance = Math.abs(currentScroll - targetY);

      pendingTargetEl = targetEl;
      startManualScroll(Math.min(2400, Math.max(600, distance * 0.15 + 400)));
      performScroll(targetY);

      triggerTargetHighlight(targetEl);
    }

    let lastActiveTocLink = null;
    let lastTocUserInteract = 0;
    if (tocSidebar) {
      if (window._uvmTocWheelHandler) {
        tocSidebar.removeEventListener('wheel', window._uvmTocWheelHandler);
      }
      window._uvmTocWheelHandler = function (e) {
        lastTocUserInteract = Date.now();
        if (e.ctrlKey) return;
        const compact = isCompactTocMode();
        if (compact && (!tocInner || !tocInner.contains(e.target))) return;
        const scrollBox = compact ? tocInner : tocSidebar;
        if (!scrollBox) return;

        const maxScroll = scrollBox.scrollHeight - scrollBox.clientHeight;
        if (maxScroll <= 1) {
          e.preventDefault();
          return;
        }
        if ((e.deltaY < 0 && scrollBox.scrollTop <= 0) ||
          (e.deltaY > 0 && scrollBox.scrollTop >= maxScroll - 1)) {
          e.preventDefault();
        }
      };
      tocSidebar.addEventListener('wheel', window._uvmTocWheelHandler, { passive: false });

      if (window._uvmTocTouchMoveHandler) {
        tocSidebar.removeEventListener('touchmove', window._uvmTocTouchMoveHandler);
      }
      window._uvmTocTouchMoveHandler = function (e) {
        lastTocUserInteract = Date.now();
        const compact = isCompactTocMode();
        if (compact && (!tocInner || !tocInner.contains(e.target))) return;
        const scrollBox = compact ? tocInner : tocSidebar;
        if (scrollBox && scrollBox.scrollHeight <= scrollBox.clientHeight + 1) {
          e.preventDefault();
        }
      };
      tocSidebar.addEventListener('touchmove', window._uvmTocTouchMoveHandler, { passive: false });
    }

    function scrollTocToItem(linkEl, opts) {
      if (!linkEl || !tocSidebar) return;
      if (linkEl.offsetParent === null) return;
      const scrollBox = (window.innerWidth <= 1000 && tocInner) ? tocInner : tocSidebar;
      const options = opts || {};
      if (!options.force && (Date.now() - lastTocUserInteract < 1500 || scrollBox.matches(':hover'))) {
        return;
      }
      const sidebarRect = scrollBox.getBoundingClientRect();
      const linkRect = linkEl.getBoundingClientRect();
      if (linkRect.height === 0 || sidebarRect.height === 0) return;

      const pad = 16;
      const isAbove = linkRect.top < sidebarRect.top + pad;
      const isBelow = linkRect.bottom > sidebarRect.bottom - pad;
      if (!isAbove && !isBelow) return;

      const currentScroll = scrollBox.scrollTop;
      let targetOffset;
      if (options.center) {
        targetOffset = linkRect.top - sidebarRect.top + currentScroll - (sidebarRect.height / 2) + (linkRect.height / 2);
      } else if (isAbove) {
        targetOffset = currentScroll + (linkRect.top - sidebarRect.top) - pad;
      } else {
        targetOffset = currentScroll + (linkRect.bottom - sidebarRect.bottom) + pad;
      }
      targetOffset = Math.max(0, targetOffset);

      if (options.smooth) {
        try {
          scrollBox.scrollTo({ top: targetOffset, behavior: 'smooth' });
        } catch (e) {
          scrollBox.scrollTop = targetOffset;
        }
      } else {
        scrollBox.scrollTop = targetOffset;
      }
    }

    function setMobileTocOpen(isOpen) {
      if (!tocSidebar || !mobileTriggerBtn) return;
      const nextState = !!isOpen && isCompactTocMode();
      tocSidebar.classList.toggle('toc-mobile-open', nextState);
      mobileTriggerBtn.setAttribute('aria-expanded', nextState ? 'true' : 'false');
      if (nextState && lastActiveTocLink) {
        requestAnimationFrame(function () {
          scrollTocToItem(lastActiveTocLink, { force: true, smooth: false, center: true });
        });
      }
    }

    if (mobileTriggerBtn) {
      mobileTriggerBtn.onclick = function (e) {
        e.stopPropagation();
        setMobileTocOpen(!tocSidebar.classList.contains('toc-mobile-open'));
      };
    }

    if (window._uvmTocMobileDocClickHandler) {
      document.removeEventListener('click', window._uvmTocMobileDocClickHandler);
    }
    window._uvmTocMobileDocClickHandler = function (e) {
      if (tocSidebar.classList.contains('toc-mobile-open') && !tocSidebar.contains(e.target)) {
        setMobileTocOpen(false);
      }
    };
    document.addEventListener('click', window._uvmTocMobileDocClickHandler);

    if (window._uvmTocMobileKeyHandler) {
      document.removeEventListener('keydown', window._uvmTocMobileKeyHandler);
    }
    window._uvmTocMobileKeyHandler = function (e) {
      if (e.key === 'Escape' && tocSidebar.classList.contains('toc-mobile-open')) {
        setMobileTocOpen(false);
        if (mobileTriggerBtn) mobileTriggerBtn.focus();
      }
    };
    document.addEventListener('keydown', window._uvmTocMobileKeyHandler);

    if (window._uvmTocMobileResizeHandler) {
      window.removeEventListener('resize', window._uvmTocMobileResizeHandler);
    }
    window._uvmTocMobileResizeHandler = function () {
      if (!isCompactTocMode() && tocSidebar.classList.contains('toc-mobile-open')) {
        setMobileTocOpen(false);
      }
      updatePinnedState();
    };
    window.addEventListener('resize', window._uvmTocMobileResizeHandler, { passive: true });

    function resolveScrollContainer(el) {
      if (!el || !el.closest) return el;
      if (el.classList && (el.classList.contains('inherited-methods-section') || el.classList.contains('Summary'))) return el;
      const inhEntry = el.closest('.inherited-topic-entry');
      if (inhEntry) return inhEntry;
      const inhSec = el.closest('.inherited-methods-section');
      if (inhSec) return inhSec;
      const summarySec = el.closest('.Summary');
      if (summarySec) return summarySec;
      return el.closest('#Content > div') || el.closest('.CTopic') || el;
    }

    // Click on TOC link
    const tocLinks = tocNav.querySelectorAll('.doc-toc-link');
    tocLinks.forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        const targetId = link.getAttribute('data-target-id');
        const target = document.getElementById(targetId) || document.querySelector('[data-doc-topic="' + targetId + '"]');

        tocLinks.forEach(function (l) { l.classList.remove('active'); });
        link.classList.add('active');
        lastActiveTocLink = link;
        updateMobileCurrentLabel((link.textContent || '').trim());
        setMobileTocOpen(false);

        const parentGroupBlock = link.closest('.doc-toc-group-block');
        if (parentGroupBlock && parentGroupBlock.classList.contains('collapsed')) {
          parentGroupBlock.classList.remove('collapsed');
          updateToggleAllBtn();
        }

        const inhSecId = link.getAttribute('data-inherited-section-id');
        if (inhSecId) {
          const inhSec = document.getElementById(inhSecId);
          if (inhSec && typeof inhSec._ensureExpandedAndRendered === 'function') {
            inhSec._ensureExpandedAndRendered(function () {
              requestAnimationFrame(function () {
                const resolvedTarget = document.getElementById(targetId);
                if (resolvedTarget) {
                  scrollToElement(resolvedTarget);
                }
              });
            });
            return;
          }
        }

        if (target) {
          scrollToElement(target);
          const semanticAnchor = link.getAttribute('data-anchor') || target.getAttribute('data-anchor') ||
            (targetId && !targetId.startsWith('doc-nav-item-') && targetId !== 'doc-nav-main' ? targetId : '');
          const realId = semanticAnchor || target.id || targetId;
          try {
            history.replaceState(null, null, '#' + realId);
          } catch (err) { }
          if (window.parent && window.parent !== window) {
            try {
              const docMatch = window.location.pathname.match(/(docs_view\/.*)$/);
              if (docMatch && realId) {
                const docRel = docMatch[1];
                window.parent.postMessage({ type: 'docNavigated', url: docRel + '#' + realId }, '*');
              }
            } catch (err) { }
          }
        }
      });
    });

    // Content in-page link click handling (bind once across TOC rebuilds)
    if (window._uvmTocContentClickHandler) {
      contentEl.removeEventListener('click', window._uvmTocContentClickHandler);
    }
    window._uvmTocContentClickHandler = function (e) {
      const link = e.target.closest('a[href*="#"]');
      if (!link) return;
      const href = link.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript:')) return;
      if (link.classList.contains('src-code-link') || href.includes('src_view/')) return;

      if (href.startsWith('#')) {
        const targetId = link.getAttribute('data-target-id') || href.substring(1);
        let target = findDocTargetElement(null, targetId);
        let inhSec = null;
        if (target) {
          const parentInh = target.closest ? target.closest('.inherited-methods-section') : null;
          if (parentInh) {
            inhSec = parentInh;
          }
        } else {
          inhSec = findMatchingInheritedSection(targetId);
        }

        if (target) {
          target = resolveScrollContainer(target);
        }

        if (inhSec && typeof inhSec._ensureExpandedAndRendered === 'function') {
          e.preventDefault();
          inhSec._ensureExpandedAndRendered(function () {
            const memberSafe = (targetId && targetId.includes('.')) ? targetId.slice(targetId.lastIndexOf('.') + 1).replace(/[^A-Za-z0-9_]/g, '_') : '';
            let resolvedTarget = document.getElementById(targetId);
            if (!resolvedTarget) {
              try {
                resolvedTarget = inhSec.querySelector('[data-anchor="' + CSS.escape(targetId) + '"]') ||
                  inhSec.querySelector('a[name="' + CSS.escape(targetId) + '"]') ||
                  document.querySelector('[data-anchor="' + CSS.escape(targetId) + '"]');
              } catch (err) { }
            }
            if (!resolvedTarget && memberSafe) {
              resolvedTarget = document.getElementById(inhSec.id + '-' + memberSafe);
            }
            if (!resolvedTarget) {
              resolvedTarget = target || inhSec;
            }
            if (resolvedTarget) {
              resolvedTarget = resolveScrollContainer(resolvedTarget);
              scrollToElement(resolvedTarget);
            }
          });
          return;
        }
        if (target) {
          e.preventDefault();
          scrollToElement(target);

          const semanticAnchor = target.getAttribute('data-anchor') ||
            (targetId && !targetId.startsWith('doc-nav-item-') && targetId !== 'doc-nav-main' ? targetId : '') ||
            (target.id && !target.id.startsWith('doc-nav-item-') && target.id !== 'doc-nav-main' ? target.id : '');
          const realId = semanticAnchor || target.id || target.getAttribute('data-doc-topic') || targetId;
          try {
            history.replaceState(null, null, '#' + realId);
          } catch (err) { }

          if (window.parent && window.parent !== window) {
            try {
              const docMatch = window.location.pathname.match(/(docs_view\/.*)$/);
              if (docMatch && realId) {
                const docRel = docMatch[1];
                window.parent.postMessage({ type: 'docNavigated', url: docRel + '#' + realId }, '*');
              }
            } catch (err) { }
          }

          if (tocNav && realId) {
            const mLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + (target.id || realId) + '"]') ||
              tocNav.querySelector('.doc-toc-link[data-anchor="' + CSS.escape(realId) + '"]');
            if (mLink) {
              tocLinks.forEach(function (l) { l.classList.remove('active'); });
              mLink.classList.add('active');
              const pB = mLink.closest('.doc-toc-group-block');
              if (pB && pB.classList.contains('collapsed')) {
                pB.classList.remove('collapsed');
                updateToggleAllBtn();
              }
              scrollTocToItem(mLink, { force: true, smooth: true, center: true });
            }
          }
        }
      }
    };
    contentEl.addEventListener('click', window._uvmTocContentClickHandler);

    // Group chevron toggles
    const chevronBtns = tocNav.querySelectorAll('.doc-toc-chevron-btn');
    chevronBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        const block = btn.closest('.doc-toc-group-block, .doc-toc-group-item');
        if (block) {
          block.classList.toggle('collapsed');
          updateToggleAllBtn();
        }
      });
    });

    const groupHeaders = tocNav.querySelectorAll('.doc-toc-group-header');
    groupHeaders.forEach(function (header) {
      header.addEventListener('click', function (e) {
        if (e.target.closest('.doc-toc-chevron-btn') || e.target.closest('.doc-toc-link')) return;
        const btn = header.querySelector('.doc-toc-chevron-btn');
        if (btn) btn.click();
      });
    });

    function updateToggleAllBtn() {
      if (!toggleAllBtn) return;
      const allBlocks = tocNav.querySelectorAll('.doc-toc-group-block');
      if (allBlocks.length === 0) return;
      const allCollapsed = Array.from(allBlocks).every(function (b) { return b.classList.contains('collapsed'); });
      const textSpan = toggleAllBtn.querySelector('.toc-toggle-text');
      const icon = toggleAllBtn.querySelector('.toc-toggle-icon');
      if (allCollapsed) {
        if (textSpan) textSpan.textContent = 'Expand all';
        if (icon) icon.innerHTML = '<polyline points="4 6 12 14 20 6"/>';
      } else {
        if (textSpan) textSpan.textContent = 'Collapse all';
        if (icon) icon.innerHTML = '<polyline points="4 14 12 6 20 14"/>';
      }
    }

    if (toggleAllBtn) {
      toggleAllBtn.onclick = function () {
        const allBlocks = tocNav.querySelectorAll('.doc-toc-group-block');
        const anyExpanded = Array.from(allBlocks).some(function (b) { return !b.classList.contains('collapsed'); });
        if (anyExpanded) {
          allBlocks.forEach(function (b) { b.classList.add('collapsed'); });
        } else {
          allBlocks.forEach(function (b) { b.classList.remove('collapsed'); });
        }
        updateToggleAllBtn();
      };
    }

    // ScrollSpy
    let scrollTimer = null;
    function updateScrollSpy() {
      if (isManualScrolling) return;

      const spyThreshold = getBreadcrumbsHeight() + (isCompactTocMode() ? 100 : 76);
      let activeItem = null;
      for (let i = 0; i < allNavItems.length; i++) {
        const item = allNavItems[i];
        const el = item.el || document.getElementById(item.id);
        if (!el || el.offsetParent === null) continue;
        const rect = el.getBoundingClientRect();
        if (rect.top <= spyThreshold) {
          activeItem = item;
        }
      }

      if (!activeItem && allNavItems.length > 0) {
        activeItem = allNavItems[0];
      }

      if (activeItem && activeItem.link) {
        updateMobileCurrentLabel((activeItem.link.textContent || activeItem.title || '').trim());
        let visualLink = activeItem.link;
        const parentBlock = activeItem.link.closest('.doc-toc-group-block');
        if (parentBlock && parentBlock.classList.contains('collapsed') && !activeItem.link.classList.contains('doc-toc-group-title')) {
          const groupTitleLink = parentBlock.querySelector('.doc-toc-group-title');
          if (groupTitleLink) visualLink = groupTitleLink;
        }

        const linkChanged = visualLink !== lastActiveTocLink;
        lastActiveTocLink = visualLink;

        tocLinks.forEach(function (link) {
          link.classList.toggle('active', link === visualLink);
        });

        if (linkChanged) {
          scrollTocToItem(visualLink, { smooth: false, center: false });

          if (window.parent && window.parent !== window) {
            try {
              window.parent.postMessage({
                type: 'docSectionChanged',
                anchor: activeItem.anchor || activeItem.id,
                id: activeItem.id,
                title: activeItem.title
              }, '*');
            } catch (err) { }
          }
        }
      }
    }

    if (window._uvmTocScrollEndHandler) {
      window.removeEventListener('scrollend', window._uvmTocScrollEndHandler);
    }
    window._uvmTocScrollEndHandler = function () {
      if (isManualScrolling) {
        clearTimeout(manualScrollTimer);
        checkAndCorrectScroll();
      }
    };
    window.addEventListener('scrollend', window._uvmTocScrollEndHandler);

    if (window._uvmTocScrollHandler) {
      window.removeEventListener('scroll', window._uvmTocScrollHandler);
    }
    window._uvmTocScrollHandler = function () {
      updatePinnedState();
      if (isManualScrolling) {
        clearTimeout(manualScrollTimer);
        manualScrollTimer = setTimeout(checkAndCorrectScroll, 160);
        return;
      }
      if (scrollTimer) return;
      scrollTimer = requestAnimationFrame(function () {
        updateScrollSpy();
        scrollTimer = null;
      });
    };
    window.addEventListener('scroll', window._uvmTocScrollHandler, { passive: true });

    function findDocTargetElement(anchor, targetId) {
      if (!anchor && !targetId) return null;
      const idToTry = targetId || anchor;
      const rawAnchor = anchor || targetId;

      // Special top-level anchors
      if (idToTry === 'MainTopic' || idToTry === 'Overview' || idToTry === 'doc-nav-main') {
        return document.getElementById('doc-nav-main') || document.getElementById('MainTopic') || document.body;
      }
      if (idToTry === 'Contents' || idToTry === 'doc-nav-contents') {
        return document.getElementById('doc-nav-contents') || document.querySelector('.ContentsSummary');
      }
      if (idToTry === 'Summary' || idToTry === 'doc-nav-summary') {
        return document.getElementById('doc-nav-summary') || document.querySelector('.ClassSummary, .Summary');
      }

      // Build list of string variants to search (handling decoded URL, backticks, percent-encoding)
      const variants = new Set();
      [idToTry, rawAnchor].forEach(str => {
        if (!str) return;
        variants.add(str);
        try {
          const dec = decodeURIComponent(str);
          variants.add(dec);
          variants.add(dec.replace(/^`/, ''));
          variants.add('`' + dec.replace(/^`/, ''));
          variants.add(dec.replace(/\s*#\([^)]*\)/g, ''));
        } catch (e) { }
        if (str.includes('%60')) {
          const unpct = str.replace(/%60/g, '`');
          variants.add(unpct);
          variants.add(unpct.replace(/^`/, ''));
        }
        if (str.includes('%23')) {
          const unpct = str.replace(/%23/g, '#');
          variants.add(unpct);
          variants.add(unpct.replace(/\s*#\([^)]*\)/g, ''));
        }
        variants.add(str.replace(/^`/, ''));
        variants.add('`' + str.replace(/^`/, ''));
        variants.add(str.replace(/\s*#\([^)]*\)/g, ''));
      });

      // 1. Direct getElementById with variants
      for (const v of variants) {
        try {
          const el = document.getElementById(v);
          if (el) return el;
        } catch (e) { }
      }

      // 2. Exact attribute matches on data-anchor, data-doc-topic, a[name]
      for (const v of variants) {
        try {
          const safe = CSS.escape(v);
          const el = document.querySelector(`[data-anchor="${safe}"]`) ||
            document.querySelector(`[data-doc-topic="${safe}"]`) ||
            document.querySelector(`a[name="${safe}"]`);
          if (el) return el;
        } catch (e) { }
        try {
          const safe = v.replace(/"/g, '\\"');
          const el = document.querySelector(`[data-anchor="${safe}"]`) ||
            document.querySelector(`[data-doc-topic="${safe}"]`) ||
            document.querySelector(`a[name="${safe}"]`);
          if (el) return el;
        } catch (e) { }
      }

      // 3. Fallback: linear scan of elements with data-anchor, data-doc-topic, or a[name]
      const candidates = document.querySelectorAll('[data-anchor], [data-doc-topic], a[name]');
      for (let i = 0; i < candidates.length; i++) {
        const c = candidates[i];
        const da = c.getAttribute('data-anchor') || '';
        const dt = c.getAttribute('data-doc-topic') || '';
        const nm = c.getAttribute('name') || '';
        const daClean = da.replace(/\s*#\([^)]*\)/g, '');
        for (const v of variants) {
          if (da === v || dt === v || nm === v || daClean === v) {
            return c;
          }
        }
      }

      // 4. Case-insensitive or stripped suffix fallback (e.g. "uvm_component.accept_tr" -> method "accept_tr")
      for (const v of variants) {
        const dotIdx = v.lastIndexOf('.');
        if (dotIdx !== -1) {
          const shortName = v.slice(dotIdx + 1);
          for (let i = 0; i < candidates.length; i++) {
            const c = candidates[i];
            const da = c.getAttribute('data-anchor') || '';
            const nm = c.getAttribute('name') || '';
            if (da === shortName || nm === shortName || da.endsWith('.' + shortName)) {
              return c;
            }
          }
        }
      }

      return null;
    }

    // Cross-frame scrollToSection listener (register once across TOC rebuilds)
    if (!window._uvmTocScrollMsgRegistered) {
      window._uvmTocScrollMsgRegistered = true;
      registerMessageHandler(function (data) {
        if (data.type === 'scrollToSection') {
          let anchor = data.anchor;
          let targetId = data.id || anchor;
          const navToken = data.navToken;

          if (wildcardManifest && wildcardManifest.variants) {
            const wResolved = resolveWildcardTarget(targetId) || resolveWildcardTarget(anchor);
            if (wResolved) {
              applyWildcardVariant(wResolved.variant ? wResolved.variant.name : '', false);
              if (wResolved.resolvedId) {
                anchor = wResolved.resolvedId;
                targetId = wResolved.resolvedId;
              }
            } else if (targetId === 'MainTopic' && currentWildcardVariant) {
              applyWildcardVariant('', false);
            }
          }

          // 1. Prioritize inherited methods / classes explorer if anchor matches
          const inhSec = findMatchingInheritedSection(targetId) || findMatchingInheritedSection(anchor);

          if (inhSec && typeof inhSec._ensureExpandedAndRendered === 'function') {
            pendingSectionScroll = null;
            inhSec._ensureExpandedAndRendered(function () {
              const memberSafe = (targetId && targetId.includes('.'))
                ? targetId.slice(targetId.lastIndexOf('.') + 1).replace(/[^A-Za-z0-9_]/g, '_')
                : (targetId ? targetId.replace(/[^A-Za-z0-9_]/g, '_') : '');

              let resolvedTarget = document.getElementById(targetId);
              if (!resolvedTarget) {
                try {
                  resolvedTarget = inhSec.querySelector('[data-origin-anchor="' + CSS.escape(targetId) + '"]') ||
                    inhSec.querySelector('[data-anchor="' + CSS.escape(targetId) + '"]') ||
                    inhSec.querySelector('a[name="' + CSS.escape(targetId) + '"]') ||
                    document.querySelector('[data-origin-anchor="' + CSS.escape(targetId) + '"]') ||
                    document.querySelector('[data-anchor="' + CSS.escape(targetId) + '"]');
                } catch (err) { }
              }
              if (!resolvedTarget && memberSafe) {
                resolvedTarget = document.getElementById(inhSec.id + '-' + memberSafe) ||
                  inhSec.querySelector('.inherited-topic-entry[id$="-' + CSS.escape(memberSafe) + '"]') ||
                  inhSec.querySelector('[data-member-name="' + CSS.escape(memberSafe) + '"]');
              }
              if (!resolvedTarget) {
                resolvedTarget = inhSec.querySelector('.inherited-topic-entry[data-origin-class="' + CSS.escape(targetId) + '"]');
              }
              if (!resolvedTarget) {
                resolvedTarget = inhSec;
              }
              if (resolvedTarget) {
                resolvedTarget = resolveScrollContainer(resolvedTarget);
              }

              requestAnimationFrame(function () {
                setTimeout(function () {
                  expandAllRetractedAncestors(resolvedTarget);
                  scrollToElement(resolvedTarget);
                  sendScrollAck(navToken, anchor, targetId);
                  const liveTocNav = document.getElementById('doc-toc-nav');
                  if (liveTocNav) {
                    const targetNavId = resolvedTarget.id || resolvedTarget.getAttribute('data-doc-topic');
                    const targetAnchor = resolvedTarget.getAttribute('data-anchor') || anchor || targetId;
                    const mLink = (memberSafe && liveTocNav.querySelector('.doc-toc-link[data-target-id="' + inhSec.id + '-' + memberSafe + '"]')) ||
                      (targetNavId && liveTocNav.querySelector('.doc-toc-link[data-target-id="' + targetNavId + '"]')) ||
                      (targetAnchor && liveTocNav.querySelector('.doc-toc-link[data-anchor="' + CSS.escape(targetAnchor) + '"]')) ||
                      (targetId && liveTocNav.querySelector('.doc-toc-link[data-anchor="' + CSS.escape(targetId) + '"]')) ||
                      liveTocNav.querySelector('.doc-toc-link[data-target-id="' + inhSec.id + '"]');
                    if (mLink) {
                      liveTocNav.querySelectorAll('.doc-toc-link').forEach(function (l) { l.classList.remove('active'); });
                      mLink.classList.add('active');
                      const pB = mLink.closest('.doc-toc-group-block');
                      if (pB && pB.classList.contains('collapsed')) {
                        pB.classList.remove('collapsed');
                      }
                      scrollTocToItem(mLink, { force: true, smooth: true, center: true });
                    }
                  }
                }, 40);
              });
            });
            return;
          }

          // 2. Otherwise find native element on page
          let target = findDocTargetElement(anchor, targetId);
          if (target) {
            pendingSectionScroll = null;
            target = resolveScrollContainer(target);
            expandAllRetractedAncestors(target);
            requestAnimationFrame(function () {
              setTimeout(function () {
                scrollToElement(target);
                sendScrollAck(navToken, anchor, targetId);
                const liveTocNav = document.getElementById('doc-toc-nav');
                if (liveTocNav) {
                  const targetNavId = target.id || target.getAttribute('data-doc-topic');
                  const targetAnchor = target.getAttribute('data-anchor') || anchor || targetId;
                  const mLink = (targetNavId && liveTocNav.querySelector('.doc-toc-link[data-target-id="' + targetNavId + '"]')) ||
                    (targetAnchor && liveTocNav.querySelector('.doc-toc-link[data-anchor="' + CSS.escape(targetAnchor) + '"]')) ||
                    (targetId && liveTocNav.querySelector('.doc-toc-link[data-anchor="' + CSS.escape(targetId) + '"]'));
                  if (mLink) {
                    liveTocNav.querySelectorAll('.doc-toc-link').forEach(function (l) { l.classList.remove('active'); });
                    mLink.classList.add('active');
                    const pB = mLink.closest('.doc-toc-group-block');
                    if (pB && pB.classList.contains('collapsed')) {
                      pB.classList.remove('collapsed');
                    }
                    scrollTocToItem(mLink, { force: true, smooth: true, center: true });
                  }
                }
              }, 40);
            });
          } else if (targetId || anchor) {
            // Inherited sections may not be injected yet (e.g. deferred uvm_symbol_quick.js)
            pendingSectionScroll = { anchor: anchor, id: targetId, navToken: navToken };
          }
        }
      });
    }

    function handleHashNav(hashVal) {
      if (!hashVal) return;
      const raw = decodeURIComponent(hashVal.replace(/^#/, ''));
      if (!raw) return;
      setTimeout(function () {
        window.postMessage({ type: 'scrollToSection', anchor: raw, id: raw }, '*');
      }, 160);
    }

    if (window.location.hash) handleHashNav(window.location.hash);
    window.addEventListener('hashchange', function () { handleHashNav(window.location.hash); });
    window.addEventListener('load', function () { if (window.location.hash) handleHashNav(window.location.hash); });
    setTimeout(function () {
      updateScrollSpy();
      updatePinnedState();
    }, 120);
  }

  // =========================================================================
  // Scroll Position & Reading Level Preserver (on resize, split toggle, reflow)
  // =========================================================================

  let activeAnchorEl = null;
  let activeAnchorOffset = 0;
  let activeScrollRatio = 0;
  let isAnchorUpdating = false;

  function findTopmostVisibleElement() {
    // 1. Check headings and section landmarks first (invariant height, perfect anchors)
    const headings = document.querySelectorAll(
      '.CTitle, .STitle, h1, h2, h3, .topo-header, .studio-header, .sim-header, .doc-source-banner, .example-source-banner, .file-code-pane.active tr, .sv-code-table tr'
    );
    let bestEl = null;
    let minDistance = Infinity;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 800;

    const topTarget = getBreadcrumbsHeight() + 24;
    for (let i = 0; i < headings.length; i++) {
      const el = headings[i];
      const rect = el.getBoundingClientRect();
      if (rect.top >= -40 && rect.top <= viewportHeight * 0.6) {
        const dist = Math.abs(rect.top - topTarget);
        if (dist < minDistance) {
          minDistance = dist;
          bestEl = el;
        }
      }
    }
    if (bestEl) return bestEl;

    // 2. Fallback to compact content blocks
    const blocks = document.querySelectorAll('.CTopic, .CBody > p, .topo-card, .doc-source-banner');
    for (let i = 0; i < blocks.length; i++) {
      const el = blocks[i];
      const rect = el.getBoundingClientRect();
      if (rect.bottom > 20 && rect.top <= viewportHeight * 0.5) {
        return el;
      }
    }
    return null;
  }

  function saveScrollAnchor() {
    if (isAnchorUpdating) return;
    const scrollEl = document.scrollingElement || document.documentElement || document.body;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    const maxScroll = Math.max(1, scrollEl.scrollHeight - window.innerHeight);
    activeScrollRatio = scrollY / maxScroll;

    const el = findTopmostVisibleElement();
    if (el) {
      activeAnchorEl = el;
      activeAnchorOffset = el.getBoundingClientRect().top;
    }
  }

  function restoreScrollAnchor() {
    isAnchorUpdating = true;
    const scrollEl = document.scrollingElement || document.documentElement || document.body;
    const currentScroll = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;

    // Force instantaneous non-animated repositioning to eliminate laggy/strange gliding transitions
    const docEl = document.documentElement;
    const prevScrollBehavior = docEl.style.scrollBehavior;
    docEl.style.scrollBehavior = 'auto';

    if (activeAnchorEl && activeAnchorEl.isConnected) {
      const rect = activeAnchorEl.getBoundingClientRect();
      const diff = rect.top - activeAnchorOffset;
      if (Math.abs(diff) > 1) {
        const targetY = Math.max(0, currentScroll + diff);
        window.scrollTo(0, targetY);
        if (scrollEl) scrollEl.scrollTop = targetY;
      }
    } else if (activeScrollRatio > 0) {
      const maxScroll = Math.max(1, scrollEl.scrollHeight - window.innerHeight);
      const targetY = Math.round(activeScrollRatio * maxScroll);
      window.scrollTo(0, targetY);
      if (scrollEl) scrollEl.scrollTop = targetY;
    }

    requestAnimationFrame(function () {
      docEl.style.scrollBehavior = prevScrollBehavior || '';
      isAnchorUpdating = false;
      saveScrollAnchor();
    });
  }

  function initScrollAnchor() {
    let lastWidth = window.innerWidth;

    function handleResize() {
      const currentWidth = window.innerWidth;
      if (Math.abs(currentWidth - lastWidth) < 2) return;
      lastWidth = currentWidth;
      restoreScrollAnchor();
    }

    window.addEventListener('resize', handleResize, { passive: true });

    let scrollAnchorRaf = null;
    window.addEventListener('scroll', function () {
      if (isAnchorUpdating) return;
      if (scrollAnchorRaf) return;
      scrollAnchorRaf = requestAnimationFrame(function () {
        saveScrollAnchor();
        scrollAnchorRaf = null;
      });
    }, { passive: true });

    setTimeout(saveScrollAnchor, 150);

    registerMessageHandler(function (data) {
      if (data.type === 'saveScrollAnchor') {
        saveScrollAnchor();
      } else if (data.type === 'restoreScrollAnchor') {
        restoreScrollAnchor();
      }
    });
  }

  // =========================================================================
  // Heading Anchors & Canonical Link Sharing
  // =========================================================================

  function initHeadingAnchors() {
    const LINK_ICON_SVG = '<svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>';
    const CHECK_ICON_SVG = '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>';

    function getHeadingAnchor(headingEl) {
      if (!headingEl) return '';
      if (headingEl.id && headingEl.id !== 'IFirstHeading') return headingEl.id;

      const inhWrap = headingEl.closest('.inherited-topic-entry');
      if (inhWrap) {
        const inhAnchor = inhWrap.getAttribute('data-anchor');
        if (inhAnchor) return inhAnchor;
      }

      const aTag = headingEl.querySelector('a[name], a[id]');
      if (aTag) {
        const name = aTag.getAttribute('name') || aTag.getAttribute('id');
        if (name && !name.startsWith('link')) return name;
      }

      const wrap = headingEl.closest('[data-anchor], [data-doc-topic], .CClass, .CMethod, .CGroup, .Summary');
      if (wrap) {
        const anchor = wrap.getAttribute('data-anchor');
        if (anchor) return anchor;
        const topicId = wrap.id || wrap.getAttribute('data-doc-topic');
        if (topicId) return topicId;
      }

      const cleanText = headingEl.textContent.trim();
      return cleanText ? encodeURIComponent(cleanText) : '';
    }

    function setupHeading(heading) {
      if (heading.querySelector('.heading-anchor-btn')) return;
      const isPageTitle = heading.tagName === 'H1' && !!heading.closest('#doc-nav-main, #MainTopic');
      const anchor = isPageTitle ? '' : getHeadingAnchor(heading);
      if (!isPageTitle && !anchor) return;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'heading-anchor-btn';
      btn.setAttribute('aria-label', isPageTitle ? 'Copy link to this page' : 'Copy link to this section');
      btn.setAttribute('title', isPageTitle ? 'Copy link to this page' : 'Copy link to this section');
      if (isPageTitle) {
        btn.setAttribute('data-page-link', '1');
      } else {
        btn.setAttribute('data-anchor', anchor);
      }
      btn.innerHTML = LINK_ICON_SVG;

      const tip = document.createElement('span');
      tip.className = 'anchor-copy-tooltip';
      tip.textContent = 'Link copied!';
      btn.appendChild(tip);

      const titleMain = heading.querySelector('.inherited-title-main');
      if (titleMain) {
        titleMain.appendChild(btn);
      } else {
        const metaEl = heading.querySelector('.inherited-title-meta');
        if (metaEl) {
          heading.insertBefore(btn, metaEl);
        } else {
          heading.appendChild(btn);
        }
      }
    }

    function scanHeadings(container) {
      const root = container || document;
      root.querySelectorAll('.CTitle, .STitle, .IHeading').forEach(setupHeading);
    }
    window._scanHeadingAnchors = scanHeadings;

    scanHeadings();
    setTimeout(scanHeadings, 150);

    document.addEventListener('click', function (e) {
      const btn = e.target.closest('.heading-anchor-btn');
      if (!btn) return;

      e.preventDefault();
      e.stopPropagation();
      try {
        btn.blur();
      } catch (err) { }

      const isPageLink = btn.getAttribute('data-page-link') === '1';
      let anchor = btn.getAttribute('data-anchor') || '';
      if (!isPageLink && !anchor) return;
      anchor = resolveWildcardCopyAnchor(anchor, isPageLink);

      const hash = anchor ? ('#' + anchor) : '';
      try {
        history.pushState(null, '', hash || (window.location.pathname + window.location.search));
      } catch (err) {
        if (hash) window.location.hash = hash;
      }

      let fullUrl = '';
      const isExample = window.location.pathname.includes('examples_view/') || window.location.href.includes('examples_view/');
      const exMatch = window.location.pathname.match(/(examples_view\/.*)$/);
      const docMatch = window.location.pathname.match(/(docs_view\/.*)$/);
      const exRel = exMatch ? exMatch[1] : '';
      const docRel = docMatch ? docMatch[1] : '';

      if (window.parent && window.parent !== window) {
        try {
          let parentBase = '';
          try {
            parentBase = (window.parent.location.origin || '') + (window.parent.location.pathname || '');
          } catch (err) {
            parentBase = window.location.href.split(isExample ? '/examples_view/' : '/docs_view/')[0] + '/index.html';
          }
          if (isExample) {
            const exClean = exRel.replace(/^examples_view\//, '');
            fullUrl = `${parentBase}#/example/${exClean}${hash}`;
            window.parent.postMessage({ type: 'exampleNavigated', url: exRel + hash }, '*');
          } else {
            const docClean = docRel.replace(/^docs_view\//, '');
            fullUrl = `${parentBase}#/doc/${docClean}${hash}`;
            window.parent.postMessage({ type: 'docNavigated', url: docRel + hash }, '*');
          }
        } catch (err) {
          fullUrl = window.location.href.split('#')[0] + hash;
        }
      } else {
        fullUrl = window.location.href.split('#')[0] + hash;
      }

      const tip = btn.querySelector('.anchor-copy-tooltip');
      copyText(fullUrl).then(function () {
        btn.classList.add('copied');
        btn.innerHTML = CHECK_ICON_SVG;
        if (tip) {
          tip.textContent = 'Link copied!';
          btn.appendChild(tip);
          tip.classList.add('show');
        }

        setTimeout(function () {
          btn.classList.remove('copied');
          btn.innerHTML = LINK_ICON_SVG;
          if (tip) {
            btn.appendChild(tip);
            tip.classList.remove('show');
          }
        }, 1800);
      }).catch(function (err) {
        console.error('Failed to copy link:', err);
      });
    });
  }

  // =========================================================================
  // Unified Code Viewer & Multi-File Code Studio Controller
  // Powers both multi-file studios (examples_view/) and source viewer (src_view/)
  // =========================================================================

  function initCodeStudio() {
    const studioTabBar = document.getElementById('studio-tab-bar');
    const studioTabs = document.querySelectorAll('.studio-tab');
    const codePanes = document.querySelectorAll('.file-code-pane');
    const studioFileSelect = document.getElementById('studio-file-select');
    const symSelect = document.getElementById('src-sym-select') || document.querySelector('.sym-jump-select');
    const studioCodeContainer = document.getElementById('studio-code-container') ||
      document.getElementById('src-code-container') ||
      document.querySelector('.code-container');
    const studioTabScrollLeft = document.getElementById('studio-tab-scroll-left');
    const studioTabScrollRight = document.getElementById('studio-tab-scroll-right');
    const btnCopyCode = document.getElementById('btn-copy-code') || document.getElementById('copy-src-btn');
    const btnDownloadRaw = document.getElementById('btn-download-raw');
    const btnCopyExampleLink = document.getElementById('btn-copy-example-link');
    const btnSplitSource = document.getElementById('btn-split-source');

    if (!studioTabBar && !document.getElementById('monaco-editor-pane') && !document.getElementById('raw-source-text')) return;

    let currentFileIdx = 0;
    const zipPayloadEl = document.getElementById('zip-payload');
    let filesList = [];
    try {
      if (zipPayloadEl && zipPayloadEl.getAttribute('data-zip')) {
        filesList = JSON.parse(zipPayloadEl.getAttribute('data-zip'));
      }
    } catch (e) { }

    let onFileTabSwitched = null;

    function getActivePane() {
      if (codePanes.length > 0) {
        return codePanes[currentFileIdx] || codePanes[0];
      }
      return document.querySelector('.sv-code-table') || studioCodeContainer;
    }

    function getActiveCodeText() {
      if (filesList[currentFileIdx] && filesList[currentFileIdx].content) {
        return filesList[currentFileIdx].content;
      }
      const rawTextEl = document.getElementById('raw-source-text');
      if (rawTextEl) {
        return rawTextEl.value;
      }
      const pane = getActivePane();
      if (pane) {
        const codeCells = Array.from(pane.querySelectorAll('.code'));
        if (codeCells.length > 0) {
          return codeCells.map(function (c) { return c.textContent; }).join('\n');
        }
      }
      return '';
    }

    function switchFileTab(idx) {
      const totalFiles = Math.max(filesList.length, studioTabs.length, codePanes.length);
      if (idx < 0 || idx >= totalFiles) return;
      currentFileIdx = idx;

      studioTabs.forEach(function (tab, i) {
        tab.classList.toggle('active', i === idx);
      });

      codePanes.forEach(function (pane, i) {
        pane.classList.toggle('active', i === idx);
      });

      if (studioFileSelect) {
        studioFileSelect.value = String(idx);
      }

      if (typeof onFileTabSwitched === 'function') {
        onFileTabSwitched(idx);
      }

      if (studioTabs[idx] && studioTabBar) {
        const tab = studioTabs[idx];
        const tabLeft = tab.offsetLeft;
        const tabRight = tabLeft + tab.offsetWidth;
        const viewLeft = studioTabBar.scrollLeft;
        const viewRight = viewLeft + studioTabBar.clientWidth;
        if (tabLeft < viewLeft || tabRight > viewRight) {
          const targetLeft = Math.max(0, tabLeft - (studioTabBar.clientWidth / 2) + (tab.offsetWidth / 2));
          try {
            studioTabBar.scrollTo({ left: targetLeft, behavior: 'smooth' });
          } catch (e) {
            studioTabBar.scrollLeft = targetLeft;
          }
        }
      }
    }

    studioTabs.forEach(function (tab, idx) {
      tab.addEventListener('click', function () { switchFileTab(idx); });
    });

    if (studioTabScrollLeft && studioTabBar) {
      studioTabScrollLeft.addEventListener('click', function () {
        studioTabBar.scrollBy({ left: -220, behavior: 'smooth' });
      });
    }
    if (studioTabScrollRight && studioTabBar) {
      studioTabScrollRight.addEventListener('click', function () {
        studioTabBar.scrollBy({ left: 220, behavior: 'smooth' });
      });
    }

    if (studioFileSelect) {
      studioFileSelect.addEventListener('change', function (e) {
        const idx = parseInt(e.target.value, 10);
        if (!isNaN(idx)) switchFileTab(idx);
      });
    }

    if (studioTabBar) {
      studioTabBar.addEventListener('wheel', function (e) {
        if (e.deltaY !== 0 && studioTabBar.scrollWidth > studioTabBar.clientWidth) {
          studioTabBar.scrollLeft += e.deltaY;
          e.preventDefault();
        }
      }, { passive: false });
    }

    // Smooth Line Scrolling & Centering helper
    let lastScrolledLine = null;
    let lastScrolledTime = 0;
    let monacoEditorInstance = null;
    let isMonacoActive = false;
    let monacoActiveLineDecorations = [];
    let pendingMonacoTargetLine = null;

    function revealAndHighlightLineInMonaco(lineNum) {
      const n = parseInt(String(lineNum || '').replace(/^#?L?/, ''), 10);
      if (!isMonacoActive || !monacoEditorInstance || isNaN(n) || n < 1) return;
      const model = monacoEditorInstance.getModel();
      const maxLine = model ? model.getLineCount() : n;
      const targetLine = Math.min(Math.max(1, n), maxLine);
      monacoEditorInstance.setPosition({ lineNumber: targetLine, column: 1 });
      monacoEditorInstance.revealLineInCenter(targetLine, (window.monaco && monaco.editor.ScrollType) ? monaco.editor.ScrollType.Smooth : 0);
      if (window.monaco) {
        monacoActiveLineDecorations = monacoEditorInstance.deltaDecorations(monacoActiveLineDecorations, [{
          range: new monaco.Range(targetLine, 1, targetLine, 1),
          options: {
            isWholeLine: true,
            className: 'monaco-active-line-highlight'
          }
        }]);
      }
    }

    function scrollToLine(lineHashOrNum) {
      if (!lineHashOrNum) return;
      const lineStr = String(lineHashOrNum).replace(/^#?L?/, '');
      const now = Date.now();
      if (lastScrolledLine === lineStr && (now - lastScrolledTime) < 400) {
        return;
      }
      const lineNum = parseInt(lineStr, 10);
      if (!isNaN(lineNum) && lineNum >= 1) {
        lastScrolledLine = lineStr;
        lastScrolledTime = now;
        if (isMonacoActive && monacoEditorInstance) {
          revealAndHighlightLineInMonaco(lineNum);
        } else {
          pendingMonacoTargetLine = lineNum;
          const pane = getActivePane();
          if (pane) {
            pane.querySelectorAll('tr.active-line').forEach(function (tr) {
              tr.classList.remove('active-line');
            });
            const targetRow = pane.querySelector(`tr#L${lineNum}`) ||
              pane.querySelector(`tr[data-line="${lineNum}"]`) ||
              (pane.querySelector(`td.ln[data-line="${lineNum}"]`) ? pane.querySelector(`td.ln[data-line="${lineNum}"]`).closest('tr') : null);
            if (targetRow) {
              targetRow.classList.add('active-line');
              scrollToRow(targetRow);
            }
          }
        }
        try {
          history.replaceState(null, '', `#L${lineStr}`);
        } catch (err) { }
      }
    }

    // Symbol Jump Select dropdown in source viewer
    if (symSelect) {
      symSelect.addEventListener('change', function (e) {
        const val = e.target.value;
        if (val) {
          scrollToLine(val);
        }
      });
    }

    // Line number click -> copy line deep-link & highlight
    document.querySelectorAll('.file-code-pane .ln a, .sv-code-table .ln a').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        const lineNum = a.textContent.trim();
        const targetRow = a.closest('tr');
        if (targetRow) {
          document.querySelectorAll('.file-code-pane tr.active-line, .sv-code-table tr.active-line').forEach(function (tr) {
            tr.classList.remove('active-line');
          });
          targetRow.classList.add('active-line');
        }

        let fullUrl = window.location.href.split('#')[0] + `#L${lineNum}`;
        let parentBase = '';
        try {
          if (window.parent && window.parent !== window && window.parent.location.pathname) {
            parentBase = (window.parent.location.origin || '') + window.parent.location.pathname;
          }
        } catch (err) { }

        const exMatch = window.location.pathname.match(/(examples_view\/.*)$/);
        const srcMatch = window.location.pathname.match(/(src_view\/.*)$/);

        if (exMatch) {
          const exClean = exMatch[1].replace(/^examples_view\//, '');
          if (!parentBase) {
            parentBase = window.location.href.split('/examples_view/')[0] + '/index.html';
          }
          fullUrl = `${parentBase}#/example/${exClean}?file=${currentFileIdx}#L${lineNum}`;
        } else if (srcMatch) {
          const srcClean = srcMatch[1].replace(/^src_view\//, '').replace(/\.html$/, '');
          if (!parentBase) {
            parentBase = window.location.href.split('/src_view/')[0] + '/index.html';
          }
          fullUrl = `${parentBase}#/src/${srcClean}#L${lineNum}`;
        }

        copyText(fullUrl).then(function () {
          const origText = a.textContent;
          a.textContent = '✓';
          setTimeout(function () { a.textContent = origText; }, 1200);
        });
      });
    });

    // Copy Code button (supports both multi-file studio and mono-file source view)
    if (btnCopyCode) {
      btnCopyCode.addEventListener('click', function () {
        let codeToCopy = '';
        if (filesList[currentFileIdx] && filesList[currentFileIdx].content) {
          codeToCopy = filesList[currentFileIdx].content;
        } else {
          const rawTextEl = document.getElementById('raw-source-text');
          if (rawTextEl) {
            codeToCopy = rawTextEl.value;
          } else {
            const activePane = codePanes[currentFileIdx] || codePanes[0] || document.querySelector('.file-code-pane') || document.querySelector('.sv-code-table');
            if (activePane) {
              const codeCells = Array.from(activePane.querySelectorAll('.code'));
              codeToCopy = codeCells.map(c => c.textContent).join('\n');
            }
          }
        }
        if (!codeToCopy) return;
        copyText(codeToCopy).then(function () {
          bindCopyFeedback(btnCopyCode, 'Copy Code', 'Copied!');
        });
      });
    }

    // Download Raw button
    if (btnDownloadRaw) {
      btnDownloadRaw.addEventListener('click', function (e) {
        const curFile = filesList[currentFileIdx];
        if (curFile && curFile.content) {
          e.preventDefault();
          const blob = new Blob([curFile.content], { type: 'text/plain;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = curFile.name.split('/').pop();
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
        // If not in filesList (e.g. single-file source view with a direct download link), let browser download native href
      });
    }

    if (btnCopyExampleLink) {
      btnCopyExampleLink.addEventListener('click', function () {
        let fullUrl = window.location.href;
        const exMatch = window.location.pathname.match(/(examples_view\/.*)$/);
        if (exMatch) {
          const exClean = exMatch[1].replace(/^examples_view\//, '');
          let parentBase = '';
          try {
            if (window.parent && window.parent !== window && window.parent.location.pathname) {
              parentBase = (window.parent.location.origin || '') + window.parent.location.pathname;
            }
          } catch (err) { }
          if (!parentBase) {
            parentBase = window.location.href.split('/examples_view/')[0] + '/index.html';
          }
          fullUrl = `${parentBase}#/example/${exClean}`;
        }
        copyText(fullUrl).then(function () {
          bindCopyFeedback(btnCopyExampleLink, 'Copy Link', 'Copied!');
        });
      });
    }

    if (btnSplitSource) {
      btnSplitSource.addEventListener('click', function () {
        const targetSrc = btnSplitSource.getAttribute('data-src-url') || 'src_view/base/uvm_component.svh.html#L44';
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ type: 'openSourceView', url: targetSrc }, '*');
        }
      });
    }

    // =======================================================================
    // Code Editor Tools Suite
    // (Find in file, Occurrence Highlighting, Go to Definition, Quick Info, Monaco)
    // =======================================================================

    function scrollToRow(targetRow) {
      if (!targetRow || !studioCodeContainer) return;
      const cRect = studioCodeContainer.getBoundingClientRect();
      const rRect = targetRow.getBoundingClientRect();
      const offsetTop = rRect.top - cRect.top + studioCodeContainer.scrollTop;
      studioCodeContainer.scrollTo({
        top: Math.max(0, offsetTop - (studioCodeContainer.clientHeight / 2)),
        behavior: 'smooth'
      });
    }

    // 1. Integrated Search Widget (Ctrl+F)
    let clearFindMatches = null;
    (function initCodeFindWidget() {
      const findWidget = document.getElementById('code-find-widget');
      const btnToggleFind = document.getElementById('btn-toggle-find');
      if (!findWidget) return;

      const findInput = document.getElementById('find-input');
      const findCount = document.getElementById('find-count');
      const findPrev = document.getElementById('find-prev');
      const findNext = document.getElementById('find-next');
      const findCase = document.getElementById('find-case-toggle') || document.getElementById('find-case');
      const findWord = document.getElementById('find-word-toggle') || document.getElementById('find-word');
      const findClose = document.getElementById('find-close');

      let currentMatches = [];
      let currentMatchIdx = -1;

      clearFindMatches = function () {
        const pane = getActivePane();
        if (!pane) return;
        pane.querySelectorAll('mark.find-match').forEach(function (m) {
          m.replaceWith(...m.childNodes);
        });
        pane.normalize();
        currentMatches = [];
        currentMatchIdx = -1;
        if (findCount) findCount.textContent = 'No results';
      };

      function showWidget() {
        findWidget.style.display = 'flex';
        findWidget.classList.add('visible');
        if (btnToggleFind) btnToggleFind.classList.add('active');
        if (findInput) {
          const sel = window.getSelection().toString().trim();
          if (sel && sel.length < 50 && !sel.includes('\n')) {
            findInput.value = sel;
          }
          findInput.focus();
          findInput.select();
          performSearch();
        }
      }

      function hideWidget() {
        findWidget.classList.remove('visible');
        findWidget.style.display = 'none';
        if (btnToggleFind) btnToggleFind.classList.remove('active');
        clearFindMatches();
      }

      function toggleWidget() {
        if (findWidget.classList.contains('visible')) {
          hideWidget();
        } else {
          showWidget();
        }
      }

      function highlightMatch(idx) {
        if (!currentMatches.length || idx < 0 || idx >= currentMatches.length) return;
        currentMatches.forEach(function (m) { m.classList.remove('find-match-current'); });
        const target = currentMatches[idx];
        target.classList.add('find-match-current');
        if (findCount) {
          findCount.textContent = (idx + 1) + ' of ' + currentMatches.length;
        }
        const row = target.closest('tr');
        if (row) scrollToRow(row);
      }

      function performSearch() {
        clearFindMatches();
        if (!findInput || !findInput.value) return;
        const query = findInput.value;
        const isCase = findCase && findCase.classList.contains('active');
        const isWord = findWord && findWord.classList.contains('active');

        let regex;
        try {
          let pattern = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          if (isWord) pattern = '\\b' + pattern + '\\b';
          regex = new RegExp(pattern, isCase ? 'g' : 'gi');
        } catch (e) {
          return;
        }

        const pane = getActivePane();
        if (!pane) return;
        const codeCells = pane.querySelectorAll('td.code, .code');

        codeCells.forEach(function (cell) {
          const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT, null, false);
          const textNodes = [];
          let n;
          while ((n = walker.nextNode())) {
            if (n.nodeValue && n.nodeValue.trim().length > 0) {
              textNodes.push(n);
            }
          }

          textNodes.forEach(function (node) {
            const text = node.nodeValue;
            regex.lastIndex = 0;
            const splits = [];
            let match;
            while ((match = regex.exec(text)) !== null) {
              splits.push({ start: match.index, end: match.index + match[0].length, val: match[0] });
              if (!regex.global) break;
            }

            if (splits.length > 0) {
              const frag = document.createDocumentFragment();
              let curr = 0;
              splits.forEach(function (s) {
                if (s.start > curr) {
                  frag.appendChild(document.createTextNode(text.substring(curr, s.start)));
                }
                const mark = document.createElement('mark');
                mark.className = 'find-match';
                mark.textContent = s.val;
                frag.appendChild(mark);
                currentMatches.push(mark);
                curr = s.end;
              });
              if (curr < text.length) {
                frag.appendChild(document.createTextNode(text.substring(curr)));
              }
              if (node.parentNode) {
                node.parentNode.replaceChild(frag, node);
              }
            }
          });
        });

        if (currentMatches.length > 0) {
          currentMatchIdx = 0;
          highlightMatch(currentMatchIdx);
        } else {
          if (findCount) findCount.textContent = '0 of 0';
        }
      }

      function nextMatch() {
        if (!currentMatches.length) return;
        currentMatchIdx = (currentMatchIdx + 1) % currentMatches.length;
        highlightMatch(currentMatchIdx);
      }

      function prevMatch() {
        if (!currentMatches.length) return;
        currentMatchIdx = (currentMatchIdx - 1 + currentMatches.length) % currentMatches.length;
        highlightMatch(currentMatchIdx);
      }

      if (btnToggleFind) btnToggleFind.addEventListener('click', toggleWidget);
      if (findClose) findClose.addEventListener('click', hideWidget);
      if (findNext) findNext.addEventListener('click', nextMatch);
      if (findPrev) findPrev.addEventListener('click', prevMatch);

      if (findCase) {
        findCase.addEventListener('click', function () {
          findCase.classList.toggle('active');
          performSearch();
        });
      }
      if (findWord) {
        findWord.addEventListener('click', function () {
          findWord.classList.toggle('active');
          performSearch();
        });
      }
      if (findInput) {
        findInput.addEventListener('input', performSearch);
        findInput.addEventListener('keydown', function (e) {
          if (e.key === 'Enter') {
            e.preventDefault();
            if (e.shiftKey) prevMatch();
            else nextMatch();
          } else if (e.key === 'Escape') {
            e.preventDefault();
            hideWidget();
          }
        });
      }

      window.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && (e.key === 'f' || e.key === 'F')) {
          if (document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') && document.activeElement !== findInput) {
            return;
          }
          e.preventDefault();
          showWidget();
        }
      });
    })();

    // 2. Occurrence Highlighter & Sequential Jump (Ctrl+D)
    let clearTokenOccurrences = null;
    (function initOccurrenceHighlighter() {
      if (!studioCodeContainer) return;
      let occurrences = [];
      let occIdx = -1;

      clearTokenOccurrences = function () {
        const pane = getActivePane();
        if (!pane) return;
        pane.querySelectorAll('.token-highlight').forEach(function (el) {
          el.classList.remove('token-highlight', 'token-active-jump');
        });
        occurrences = [];
        occIdx = -1;
      };

      function highlightToken(token, startEl) {
        clearTokenOccurrences();
        if (!token || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(token) || token.length < 2) return;
        const pane = getActivePane();
        if (!pane) return;

        const candidateSpans = pane.querySelectorAll('span');
        candidateSpans.forEach(function (span) {
          if (span.textContent.trim() === token) {
            span.classList.add('token-highlight');
            occurrences.push(span);
          }
        });

        if (startEl && occurrences.includes(startEl)) {
          occIdx = occurrences.indexOf(startEl);
        } else if (occurrences.length > 0) {
          occIdx = 0;
        }
      }

      studioCodeContainer.addEventListener('dblclick', function (e) {
        const target = e.target.closest('span');
        if (!target) return;
        const token = target.textContent.trim().replace(/^`/, '');
        if (token) highlightToken(token, target);
      });

      studioCodeContainer.addEventListener('click', function (e) {
        const target = e.target.closest('.code span');
        if (target && !e.ctrlKey && !e.metaKey) {
          const token = target.textContent.trim().replace(/^`/, '');
          if (token && (target.classList.contains('sv-ident') || target.classList.contains('sv-type') || target.classList.contains('sv-method') || target.classList.contains('sv-macro'))) {
            highlightToken(token, target);
          }
        } else if (!e.target.closest('.code')) {
          clearTokenOccurrences();
        }
      });

      window.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && (e.key === 'd' || e.key === 'D')) {
          if (occurrences.length > 0) {
            e.preventDefault();
            occurrences.forEach(function (o) { o.classList.remove('token-active-jump'); });
            occIdx = (occIdx + 1) % occurrences.length;
            const target = occurrences[occIdx];
            target.classList.add('token-active-jump');
            const row = target.closest('tr');
            if (row) scrollToRow(row);
          }
        } else if (e.key === 'Escape') {
          clearTokenOccurrences();
        }
      });
    })();

    // 3. Go to Definition (Ctrl+Click / F12) & Go to Implementation (Ctrl+F12)
    (function initDefinitionResolver() {
      if (!studioCodeContainer) return;
      let isCtrlDown = false;
      let hoveredToken = null;

      window.addEventListener('keydown', function (e) {
        if (e.key === 'Control' || e.key === 'Meta') {
          isCtrlDown = true;
          if (hoveredToken) hoveredToken.classList.add('ctrl-hoverable');
        }
      });

      window.addEventListener('keyup', function (e) {
        if (e.key === 'Control' || e.key === 'Meta') {
          isCtrlDown = false;
          document.querySelectorAll('.ctrl-hoverable').forEach(function (el) {
            el.classList.remove('ctrl-hoverable');
          });
        }
      });

      studioCodeContainer.addEventListener('mouseover', function (e) {
        const target = e.target.closest('.code span');
        if (target && isHoverableToken(target)) {
          hoveredToken = target;
          if (isCtrlDown) {
            target.classList.add('ctrl-hoverable');
          }
        }
      });

      studioCodeContainer.addEventListener('mouseout', function (e) {
        if (e.target === hoveredToken) {
          if (hoveredToken) hoveredToken.classList.remove('ctrl-hoverable');
          hoveredToken = null;
        }
      });

      function resolveSymbol(tokenName, isImplementation, contextEl) {
        const cleanToken = tokenName.trim().replace(/^`/, '');
        if (!cleanToken) return;

        const pane = getActivePane();

        // Step A: Local file lookup
        if (pane) {
          const rows = Array.from(pane.querySelectorAll('tr'));
          let targetRow = null;

          if (isImplementation) {
            for (let i = 0; i < rows.length; i++) {
              const text = rows[i].querySelector('.code') ? rows[i].querySelector('.code').textContent : '';
              const impRegex = new RegExp('(?:function|task)\\s+(?:\\w+\\s+)?\\w+::' + cleanToken + '\\b');
              if (impRegex.test(text)) {
                targetRow = rows[i];
                break;
              }
            }
          }

          if (!targetRow) {
            const escapedTok = cleanToken.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const declRegex = new RegExp('(?:^|\\s)(?:class|function|task|typedef|interface|module|package|covergroup)\\s+(?:\\w+\\s+)?' + escapedTok + '\\b|`define\\s+' + escapedTok + '\\b');
            const fwdClassRegex = /^\s*typedef\s+(?:interface\s+)?class\b/;
            for (let i = 0; i < rows.length; i++) {
              const text = rows[i].querySelector('.code') ? rows[i].querySelector('.code').textContent : '';
              if (fwdClassRegex.test(text) || /^\s*(?:extern|pure\s+virtual)\b/.test(text)) continue;
              if (declRegex.test(text)) {
                targetRow = rows[i];
                break;
              }
            }
          }

          if (targetRow) {
            const lineNum = targetRow.id ? targetRow.id.replace('L', '') : targetRow.getAttribute('data-line');
            if (lineNum) {
              scrollToLine(lineNum);
              targetRow.classList.add('active-line');
              return;
            }
          }
        }

        // Step B: Cross-file lookup in global UVM_SYMBOLS
        const owner = contextEl ? (contextEl.getAttribute('data-sym-owner') || '') : '';
        const base = contextEl ? (contextEl.getAttribute('data-sym-base') || '') : '';
        const symKind = contextEl ? (contextEl.getAttribute('data-sym-kind') || '') : '';
        const resolved = lookupUvmSymbol(cleanToken, owner, base, symKind);
        const sym = resolved ? (resolved.isAmbiguous ? resolved.primary : resolved) : null;
        if (sym && sym.file) {
          dispatchOpenSource('src_view/' + sym.file + '.html#L' + (sym.line || 1));
          return;
        }
      }

      studioCodeContainer.addEventListener('click', function (e) {
        if (e.ctrlKey || e.metaKey) {
          const target = e.target.closest('.code span');
          if (target) {
            e.preventDefault();
            e.stopPropagation();
            const token = target.textContent.trim();
            resolveSymbol(token, false, target);
          }
        }
      });

      window.addEventListener('keydown', function (e) {
        if (e.key === 'F12') {
          e.preventDefault();
          const sel = window.getSelection().toString().trim();
          let token = sel;
          if (!token && hoveredToken) {
            token = hoveredToken.textContent.trim();
          }
          if (token) {
            resolveSymbol(token, e.ctrlKey || e.metaKey, hoveredToken);
          }
        }
      });
    })();

    // 4. Quick Info Hover Popover
    (function initQuickInfoHover() {
      const quickInfo = document.getElementById('code-quick-info');
      if (!quickInfo || !studioCodeContainer) return;

      let hoverTimer = null;
      let currentTokenEl = null;

      function hideTooltip() {
        clearTimeout(hoverTimer);
        quickInfo.classList.remove('visible');
        quickInfo.style.display = 'none';
        currentTokenEl = null;
      }

      function showTooltip(target, token) {
        if (!getUvmSymbols()) {
          ensureUvmSymbolsLoaded(function () {
            if (currentTokenEl === target) showTooltip(target, token);
          });
          return;
        }
        const cleanToken = token.trim().replace(/^`/, '');
        const owner = target.getAttribute('data-sym-owner') || '';
        const base = target.getAttribute('data-sym-base') || '';
        const symKind = target.getAttribute('data-sym-kind') || '';
        const resolved = lookupUvmSymbol(cleanToken, owner, base, symKind);
        if (!resolved) {
          hideTooltip();
          return;
        }

        const primary = resolved.isAmbiguous ? resolved.primary : resolved;
        const entry = primary.entry || {};
        const typeKind = primary.type || 'symbol';
        let sigSnippet = '';
        if (entry.params || entry.extends) {
          sigSnippet = `<div class="qi-signature"><code>${escapeHtml(typeKind)} ${escapeHtml(cleanToken)}${entry.params ? ' #(' + escapeHtml(entry.params) + ')' : ''}${entry.extends ? ' extends ' + escapeHtml(entry.extends) : ''}</code></div>`;
        } else if (resolved.isAmbiguous) {
          const preview = resolved.candidates.slice(0, 3).map(c => c.class).join(', ');
          sigSnippet = `<div class="qi-signature"><code>${escapeHtml(primary.kind || typeKind)} ${escapeHtml(cleanToken)}() — ${resolved.candidates.length} classes (${escapeHtml(preview)}${resolved.candidates.length > 3 ? ', ...' : ''})</code></div>`;
        } else if (primary.ownerClass && (primary.kind === 'function' || primary.kind === 'task' || typeKind === 'function' || typeKind === 'task' || typeKind === 'method')) {
          sigSnippet = `<div class="qi-signature"><code>${primary.ret ? escapeHtml(primary.ret) + ' ' : ''}${escapeHtml(primary.ownerClass)}::${escapeHtml(cleanToken)}()</code></div>`;
        } else if (entry.signature) {
          sigSnippet = `<div class="qi-signature"><code>${escapeHtml(entry.signature)}</code></div>`;
        }

        const docText = primary.doc ? `<div class="qi-doc">${escapeHtml(primary.doc)}</div>` : '';
        const fileLoc = primary.file ? `${primary.file}:${primary.line || 1}` : '';
        const srcUrl = primary.file ? `src_view/${primary.file}.html#L${primary.line || 1}` : '';
        const docUrl = primary.doc_url || '';

        quickInfo.innerHTML = `
          <div class="qi-header">
            <span class="qi-badge qi-${escapeHtml(typeKind)}">${escapeHtml(typeKind)}</span>
            <span class="qi-title">${escapeHtml(cleanToken)}</span>
          </div>
          ${sigSnippet}
          ${docText}
          <div class="qi-actions">
            ${srcUrl ? `<a href="#" class="qi-link qi-def-link" data-src-url="${escapeHtml(srcUrl)}">Go to Definition (F12)</a>` : ''}
            ${docUrl ? `<span class="qi-sep">•</span><a href="#" class="qi-link qi-doc-link" data-doc-url="${escapeHtml(docUrl)}">View Docs</a>` : ''}
            ${fileLoc ? `<span class="qi-sep">•</span><span class="qi-file">${escapeHtml(fileLoc)}</span>` : ''}
          </div>
        `;

        quickInfo.style.display = 'block';
        const tRect = target.getBoundingClientRect();
        const cRect = studioCodeContainer.getBoundingClientRect();

        let top = tRect.top - cRect.top - quickInfo.offsetHeight - 8;
        if (top < 10) {
          top = tRect.bottom - cRect.top + 8;
        }
        let left = tRect.left - cRect.left;
        if (left + 320 > cRect.width) {
          left = Math.max(10, cRect.width - 330);
        }

        quickInfo.style.top = top + 'px';
        quickInfo.style.left = Math.max(10, left) + 'px';
        quickInfo.classList.add('visible');
        currentTokenEl = target;

        const defLink = quickInfo.querySelector('.qi-def-link');
        if (defLink && srcUrl) {
          defLink.addEventListener('click', function (ev) {
            ev.preventDefault();
            dispatchOpenSource(srcUrl);
          });
        }
        const docLinkEl = quickInfo.querySelector('.qi-doc-link');
        if (docLinkEl && docUrl) {
          docLinkEl.addEventListener('click', function (ev) {
            ev.preventDefault();
            dispatchOpenDoc(docUrl, cleanToken, primary.ownerClass || '');
          });
        }
      }

      studioCodeContainer.addEventListener('mouseover', function (e) {
        const target = e.target.closest('.code span');
        if (target && isHoverableToken(target)) {
          const token = target.textContent.trim();
          clearTimeout(hoverTimer);
          hoverTimer = setTimeout(function () {
            showTooltip(target, token);
          }, 250);
        }
      });

      studioCodeContainer.addEventListener('mouseout', function (e) {
        if (e.relatedTarget && (e.relatedTarget.closest('#code-quick-info') || e.relatedTarget === currentTokenEl)) {
          return;
        }
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(hideTooltip, 200);
      });

      quickInfo.addEventListener('mouseleave', function () {
        hideTooltip();
      });

      studioCodeContainer.addEventListener('scroll', hideTooltip, { passive: true });
      window.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') hideTooltip();
      });
    })();

    // 5. Monaco Editor Dynamic Loader & Deep UVM/SystemVerilog IDE Integration
    (function initMonacoLoader() {
      const btnToggleMonaco = document.getElementById('btn-toggle-monaco');
      const monacoPane = document.getElementById('monaco-editor-pane');
      const fallbackPre = document.getElementById('monaco-fallback-pre');
      if (!btnToggleMonaco || !monacoPane) return;

      const MONACO_STATE_KEY = 'uvm_monaco_active';
      const MONACO_STICKY_KEY = 'uvm_monaco_sticky_scroll';

      function getActiveFileName() {
        if (filesList[currentFileIdx] && filesList[currentFileIdx].name) {
          return filesList[currentFileIdx].name;
        }
        const activeTab = studioTabs[currentFileIdx];
        if (activeTab) {
          const df = activeTab.getAttribute('data-file') || activeTab.textContent.trim();
          if (df) return df;
        }
        return window.location.pathname.replace(/\.html$/i, '');
      }

      function detectMonacoLanguage(filename) {
        const clean = String(filename || '').split('/').pop().split('\\').pop().toLowerCase();
        if (!clean) return 'uvm-systemverilog';
        if (clean === 'makefile' || clean.startsWith('makefile.') || clean.endsWith('.mk')) return 'makefile';
        if (clean.endsWith('.c') || clean.endsWith('.h')) return 'c';
        if (clean.endsWith('.cpp') || clean.endsWith('.cc') || clean.endsWith('.cxx') || clean.endsWith('.hpp') || clean.endsWith('.hh')) return 'cpp';
        if (clean.endsWith('.py')) return 'python';
        if (clean.endsWith('.json')) return 'json';
        if (clean.endsWith('.md')) return 'markdown';
        if (clean.endsWith('.sh') || clean.endsWith('.bash')) return 'shell';
        if (clean.endsWith('.tcl') || clean.endsWith('.do')) return 'tcl';
        return 'uvm-systemverilog';
      }

      let monacoLoadingState = 'idle'; // 'idle' | 'loading' | 'ready'
      const monacoLoadQueue = [];
      let monacoActivationSeq = 0;

      function loadMonacoScript(onSuccess, onError) {
        if (window.monaco) {
          monacoLoadingState = 'ready';
          onSuccess();
          return;
        }
        monacoLoadQueue.push({ onSuccess: onSuccess, onError: onError || function () { } });
        if (monacoLoadingState === 'loading') return;
        monacoLoadingState = 'loading';

        function flushSuccess() {
          monacoLoadingState = 'ready';
          while (monacoLoadQueue.length > 0) {
            const cb = monacoLoadQueue.shift();
            try { cb.onSuccess(); } catch (e) { console.error('[Monaco] Activation error:', e); }
          }
        }
        function flushError() {
          monacoLoadingState = 'idle';
          while (monacoLoadQueue.length > 0) {
            const cb = monacoLoadQueue.shift();
            try { cb.onError(); } catch (e) { console.error('[Monaco] Load error:', e); }
          }
        }

        if (window.require && window.require.config) {
          window.require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
          window.require(['vs/editor/editor.main'], flushSuccess, flushError);
          return;
        }
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js';
        script.onload = function () {
          window.require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
          window.require(['vs/editor/editor.main'], flushSuccess, flushError);
        };
        script.onerror = flushError;
        document.head.appendChild(script);
      }

      function defineUvmMonacoThemes() {
        if (window.__uvmMonacoThemesDefined || !window.monaco) return;
        window.__uvmMonacoThemesDefined = true;

        monaco.editor.defineTheme('uvm-light', {
          base: 'vs',
          inherit: true,
          rules: [
            { token: 'keyword.control', foreground: 'cf222e', fontStyle: 'bold' },
            { token: 'keyword.decl', foreground: 'd73a49', fontStyle: 'bold' },
            { token: 'type.builtin', foreground: '0969da' },
            { token: 'type.uvm', foreground: '0550ae', fontStyle: 'bold' },
            { token: 'keyword.qualifier', foreground: '8250df', fontStyle: 'italic' },
            { token: 'constant', foreground: '0550ae', fontStyle: 'bold' },
            { token: 'entity.name.macro', foreground: 'bc4c00', fontStyle: 'bold' },
            { token: 'keyword.preproc', foreground: '8250df', fontStyle: 'bold' },
            { token: 'support.function.system', foreground: 'b35900', fontStyle: 'bold' },
            { token: 'entity.name.function', foreground: '6f42c1' },
            { token: 'string', foreground: '0a3069' },
            { token: 'string.escape', foreground: 'cf222e', fontStyle: 'bold' },
            { token: 'comment', foreground: '57606a', fontStyle: 'italic' },
            { token: 'comment.tag', foreground: 'b08800', fontStyle: 'bold' },
            { token: 'number', foreground: '0969da' },
            { token: 'operators', foreground: '24292f' },
            { token: 'delimiter', foreground: '24292f' },
            { token: 'identifier', foreground: '24292f' }
          ],
          colors: {
            'editor.background': '#f8f9fa',
            'editor.foreground': '#202124',
            'editorGutter.background': '#f1f3f4',
            'editorLineNumber.foreground': '#6e7781',
            'editorLineNumber.activeForeground': '#1a73e8',
            'editor.lineHighlightBackground': '#f1f3f4',
            'editor.selectionBackground': '#d2e3fc',
            'editorCursor.foreground': '#1a73e8'
          }
        });

        monaco.editor.defineTheme('uvm-dark', {
          base: 'vs-dark',
          inherit: true,
          rules: [
            { token: 'keyword.control', foreground: 'ff7b72', fontStyle: 'bold' },
            { token: 'keyword.decl', foreground: 'ff7b72', fontStyle: 'bold' },
            { token: 'type.builtin', foreground: '79c0ff' },
            { token: 'type.uvm', foreground: '58a6ff', fontStyle: 'bold' },
            { token: 'keyword.qualifier', foreground: 'd2a8ff', fontStyle: 'italic' },
            { token: 'constant', foreground: '79c0ff', fontStyle: 'bold' },
            { token: 'entity.name.macro', foreground: 'ffab70', fontStyle: 'bold' },
            { token: 'keyword.preproc', foreground: 'd2a8ff', fontStyle: 'bold' },
            { token: 'support.function.system', foreground: 'f0883e', fontStyle: 'bold' },
            { token: 'entity.name.function', foreground: 'bc8cff' },
            { token: 'string', foreground: 'a5d6ff' },
            { token: 'string.escape', foreground: 'ff7b72', fontStyle: 'bold' },
            { token: 'comment', foreground: '8b949e', fontStyle: 'italic' },
            { token: 'comment.tag', foreground: 'e3b341', fontStyle: 'bold' },
            { token: 'number', foreground: '79c0ff' },
            { token: 'operators', foreground: 'e6edf3' },
            { token: 'delimiter', foreground: 'e6edf3' },
            { token: 'identifier', foreground: 'e6edf3' }
          ],
          colors: {
            'editor.background': '#232529',
            'editor.foreground': '#e8eaed',
            'editorGutter.background': '#1b1c1f',
            'editorLineNumber.foreground': '#80868b',
            'editorLineNumber.activeForeground': '#8ab4f8',
            'editor.lineHighlightBackground': '#2e3035',
            'editor.selectionBackground': '#264f78',
            'editorCursor.foreground': '#8ab4f8'
          }
        });
      }

      function registerUvmSystemVerilogLanguage() {
        if (window.__uvmSvMonarchRegistered || !window.monaco) return;
        window.__uvmSvMonarchRegistered = true;

        monaco.languages.register({
          id: 'uvm-systemverilog',
          extensions: ['.sv', '.svh', '.v', '.vh'],
          aliases: ['UVM SystemVerilog', 'uvm-systemverilog']
        });

        monaco.languages.setLanguageConfiguration('uvm-systemverilog', {
          comments: {
            lineComment: '//',
            blockComment: ['/*', '*/']
          },
          brackets: [
            ['{', '}'],
            ['[', ']'],
            ['(', ')']
          ],
          autoClosingPairs: [
            { open: '{', close: '}' },
            { open: '[', close: ']' },
            { open: '(', close: ')' },
            { open: '"', close: '"' }
          ],
          surroundingPairs: [
            { open: '{', close: '}' },
            { open: '[', close: ']' },
            { open: '(', close: ')' },
            { open: '"', close: '"' }
          ]
        });

        const syms = getUvmSymbols() || {};
        const uvmTypesSet = new Set([
          'uvm_pkg',
          ...Object.keys(syms.classes || {}),
          ...Object.keys(syms.types || {})
        ]);
        const uvmConstantsSet = new Set([
          'null', 'this', 'super', '$root', '$unit',
          'UVM_NONE', 'UVM_LOW', 'UVM_MEDIUM', 'UVM_HIGH', 'UVM_FULL', 'UVM_DEBUG',
          'UVM_INFO', 'UVM_WARNING', 'UVM_ERROR', 'UVM_FATAL',
          'UVM_NO_ACTION', 'UVM_DISPLAY', 'UVM_LOG', 'UVM_COUNT', 'UVM_EXIT', 'UVM_CALL', 'UVM_STOP', 'UVM_RM_RECORD',
          'UVM_ALL_ON', 'UVM_DEFAULT', 'UVM_PASSIVE', 'UVM_ACTIVE',
          'UVM_COPY', 'UVM_COMPARE', 'UVM_PRINT', 'UVM_RECORD', 'UVM_PACK', 'UVM_UNPACK',
          'UVM_NOCOPY', 'UVM_NOCOMPARE', 'UVM_NOPRINT', 'UVM_NORECORD', 'UVM_NOPACK',
          'UVM_REFERENCE', 'UVM_PHYSICAL', 'UVM_ABSTRACT', 'UVM_READ', 'UVM_WRITE',
          'UVM_HEX', 'UVM_DEC', 'UVM_BIN', 'UVM_OCT', 'UVM_STRING', 'UVM_TIME',
          'UVM_TLM_READ_COMMAND', 'UVM_TLM_WRITE_COMMAND', 'UVM_TLM_IGNORE_COMMAND',
          'UVM_TLM_OK_RESPONSE', 'UVM_TLM_INCOMPLETE_RESPONSE', 'UVM_TLM_GENERIC_ERROR_RESPONSE',
          'UVM_TLM_ADDRESS_ERROR_RESPONSE', 'UVM_TLM_COMMAND_ERROR_RESPONSE',
          'UVM_TLM_BURST_ERROR_RESPONSE', 'UVM_TLM_BYTE_ENABLE_ERROR_RESPONSE',
          'UVM_TLM_ACCEPTED', 'UVM_TLM_UPDATED', 'UVM_TLM_COMPLETED',
          ...Object.keys(syms.constants || {})
        ]);
        // Only unambiguous UVM lifecycle/API methods (never pollute local variables like data/addr/name/size/status)
        const uvmMethodsSet = new Set([
          'build_phase', 'connect_phase', 'end_of_elaboration_phase',
          'start_of_simulation_phase', 'run_phase', 'pre_reset_phase', 'reset_phase',
          'post_reset_phase', 'pre_configure_phase', 'configure_phase',
          'post_configure_phase', 'pre_main_phase', 'main_phase', 'post_main_phase',
          'pre_shutdown_phase', 'shutdown_phase', 'post_shutdown_phase',
          'extract_phase', 'check_phase', 'report_phase', 'final_phase',
          'phase_started', 'phase_ready_to_end', 'phase_ended',
          'raise_objection', 'drop_objection', 'set_drain_time',
          'start_item', 'finish_item', 'start', 'body', 'pre_body', 'post_body',
          'create', 'get_type', 'type_id', 'run_test',
          'set_config_int', 'set_config_string', 'set_config_object',
          'get_config_int', 'get_config_string', 'get_config_object',
          'set_report_verbosity_level', 'set_report_id_verbosity',
          'set_report_severity_action', 'set_report_id_action',
          'print', 'clone', 'copy', 'compare', 'pack', 'unpack', 'record',
          'sprint', 'convert2string', 'do_print', 'do_copy', 'do_compare',
          'do_pack', 'do_unpack', 'do_record', 'sample', 'get_full_name',
          'get_name', 'get_parent', 'get_num_children', 'lookup',
          'b_transport', 'nb_transport_fw', 'nb_transport_bw', 'can_put', 'can_get',
          'try_put', 'try_get', 'put', 'get', 'peek', 'try_peek', 'write'
        ]);

        monaco.languages.setMonarchTokensProvider('uvm-systemverilog', {
          defaultToken: 'identifier',
          controlKeywords: [
            'begin', 'end', 'if', 'else', 'case', 'casex', 'casez', 'default', 'endcase',
            'for', 'foreach', 'while', 'do', 'repeat', 'forever', 'return',
            'break', 'continue', 'wait', 'wait_order', 'fork', 'join',
            'join_any', 'join_none', 'disable', 'randcase', 'randsequence',
            'expect', 'matches'
          ],
          declKeywords: [
            'class', 'endclass', 'module', 'endmodule', 'interface', 'endinterface',
            'package', 'endpackage', 'program', 'endprogram', 'function', 'endfunction',
            'task', 'endtask', 'extends', 'implements', 'typedef', 'enum', 'struct',
            'union', 'covergroup', 'endgroup', 'property', 'endproperty', 'sequence',
            'endsequence', 'generate', 'endgenerate', 'clocking', 'endclocking',
            'import', 'export', 'checker', 'endchecker', 'config', 'endconfig',
            'primitive', 'endprimitive', 'table', 'endtable', 'specify', 'endspecify',
            'bind', 'alias', 'assign', 'deassign', 'force', 'release', 'defparam',
            'design', 'instance', 'cell', 'use', 'liblist', 'library', 'nettype',
            'initial', 'final', 'always', 'always_comb', 'always_ff', 'always_latch',
            'cover', 'coverpoint', 'cross', 'bins', 'binsof', 'illegal_bins', 'ignore_bins',
            'assert', 'assume', 'restrict', 'constraint', 'solve', 'before', 'with',
            'inside', 'dist', 'tagged', 'accept_tr', 'reject_on', 'sync_accept_on',
            'sync_reject_on', 'first_match', 'throughout', 'within', 'intersect',
            'nexttime', 's_nexttime', 'always_s', 's_always', 'eventually', 's_eventually',
            'until', 's_until', 'until_with', 's_until_with'
          ],
          builtinTypes: [
            'bit', 'logic', 'reg', 'wire', 'tri', 'tri0', 'tri1', 'wand', 'wor',
            'triand', 'trior', 'trireg', 'uwire', 'supply0', 'supply1',
            'byte', 'shortint', 'int', 'longint', 'integer', 'time',
            'shortreal', 'real', 'realtime', 'string', 'chandle', 'event', 'void',
            'signed', 'unsigned', 'type', 'var'
          ],
          qualifiers: [
            'virtual', 'local', 'protected', 'pure', 'static', 'const',
            'automatic', 'rand', 'randc', 'ref', 'input', 'output', 'inout',
            'extern', 'packed', 'untyped', 'interconnect', 'modport',
            'priority', 'unique', 'unique0', 'soft', 'strong', 'weak',
            'weak0', 'weak1', 'pull0', 'pull1', 'pulldown', 'pullup',
            'highz0', 'highz1', 'small', 'medium', 'large', 'scalared',
            'vectored', 'pulsestyle_onevent', 'pulsestyle_ondetect',
            'showcancelled', 'noshowcancelled', 'edge', 'posedge', 'negedge'
          ],
          preprocDirectives: [
            '`define', '`undef', '`ifdef', '`ifndef', '`else', '`elsif', '`endif',
            '`include', '`timescale', '`default_nettype', '`line', '`resetall',
            '`celldefine', '`endcelldefine', '`protect', '`endprotect'
          ],
          constants: Array.from(uvmConstantsSet),
          uvmTypes: Array.from(uvmTypesSet),
          uvmMethods: Array.from(uvmMethodsSet),
          tokenizer: {
            root: [
              [/\/\*/, 'comment', '@comment_block'],
              [/\/\/$/, 'comment'],
              [/\/\//, 'comment', '@comment_line'],
              [/"/, 'string', '@string'],
              [/`[a-zA-Z_][a-zA-Z0-9_]*/, {
                cases: {
                  '@preprocDirectives': 'keyword.preproc',
                  '@default': 'entity.name.macro'
                }
              }],
              [/\$[a-zA-Z_][a-zA-Z0-9_$]*/, {
                cases: {
                  '@constants': 'constant',
                  '@default': 'support.function.system'
                }
              }],
              [/\b\d+\s*'[sS]?[bBoOdDhH]\s*[0-9a-fA-F_xzXZ]+\b/, 'number'],
              [/'[01xzXZ]\b/, 'number'],
              [/'[sS]?[bBoOdDhH]\s*[0-9a-fA-F_xzXZ]+\b/, 'number'],
              [/'(?=\{|\()/, 'operators'],
              [/\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?:fs|ps|ns|us|ms|s)?\b/, 'number'],
              [/(\.)([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*\()/, ['delimiter', 'entity.name.function']],
              [/([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*\()/, {
                cases: {
                  '@controlKeywords': 'keyword.control',
                  '@declKeywords': 'keyword.decl',
                  '@builtinTypes': 'type.builtin',
                  '@qualifiers': 'keyword.qualifier',
                  '@constants': 'constant',
                  '@uvmTypes': 'type.uvm',
                  '@default': 'entity.name.function'
                }
              }],
              [/\b(?:uvm|ovm)_[a-zA-Z0-9_]*\b/, {
                cases: {
                  '@constants': 'constant',
                  '@uvmMethods': 'entity.name.function',
                  '@default': 'type.uvm'
                }
              }],
              [/[a-zA-Z_][a-zA-Z0-9_]*/, {
                cases: {
                  '@controlKeywords': 'keyword.control',
                  '@declKeywords': 'keyword.decl',
                  '@builtinTypes': 'type.builtin',
                  '@qualifiers': 'keyword.qualifier',
                  '@constants': 'constant',
                  '@uvmTypes': 'type.uvm',
                  '@uvmMethods': 'entity.name.function',
                  '@default': 'identifier'
                }
              }],
              [/[{}()\[\]]/, '@brackets'],
              [/[;,.::@#?]/, 'delimiter'],
              [/[=<>!~&|+\-*/%^]+/, 'operators']
            ],
            comment_line: [
              [/\b(?:TODO|FIXME|NOTE|IMPORTANT|WARNING|TIP|BUG|CLASS|FUNCTION|TASK|MACRO|GROUP)\b:?$/, 'comment.tag', '@pop'],
              [/@(?:param|return|see)\b:?$/, 'comment.tag', '@pop'],
              [/\b(?:TODO|FIXME|NOTE|IMPORTANT|WARNING|TIP|BUG|CLASS|FUNCTION|TASK|MACRO|GROUP)\b:?/, 'comment.tag'],
              [/@(?:param|return|see)\b:?/, 'comment.tag'],
              [/[^A-Za-z@]+$/, 'comment', '@pop'],
              [/[A-Za-z]+$/, 'comment', '@pop'],
              [/@$/, 'comment', '@pop'],
              [/[^A-Za-z@]+|[A-Za-z]+|@/, 'comment']
            ],
            comment_block: [
              [/\b(?:TODO|FIXME|NOTE|IMPORTANT|WARNING|TIP|BUG|CLASS|FUNCTION|TASK|MACRO|GROUP)\b:?/, 'comment.tag'],
              [/@(?:param|return|see)\b:?/, 'comment.tag'],
              [/\*\//, 'comment', '@pop'],
              [/[^*A-Za-z@]+|\*|[A-Za-z]+|@/, 'comment']
            ],
            string: [
              [/%[0-9]*[a-zA-Z%]$/, 'string.escape', '@pop'],
              [/\\[ntrbfv"'\\]$/, 'string.escape', '@pop'],
              [/\\x[0-9a-fA-F]{1,2}$/, 'string.escape', '@pop'],
              [/\\[0-7]{1,3}$/, 'string.escape', '@pop'],
              [/%[0-9]*[a-zA-Z%]/, 'string.escape'],
              [/\\[ntrbfv"'\\]/, 'string.escape'],
              [/\\x[0-9a-fA-F]{1,2}/, 'string.escape'],
              [/\\[0-7]{1,3}/, 'string.escape'],
              [/[^\\"%]+$|%$/, 'string', '@pop'],
              [/[^\\"%]+|%/, 'string'],
              [/"/, 'string', '@pop']
            ]
          }
        });
      }

      const NON_UVM_MONACO_TOKEN_PREFIXES = [
        'comment', 'string', 'number', 'keyword.', 'type.builtin', 'support.function.system', 'operators'
      ];

      function isMonacoTokenIgnoredAt(model, position) {
        if (!model || !position || !window.monaco || !monaco.editor || !monaco.editor.tokenize) return false;
        try {
          const langId = model.getLanguageId ? model.getLanguageId() : 'uvm-systemverilog';
          if (langId !== 'uvm-systemverilog') return true;
          const lineContent = model.getLineContent(position.lineNumber) || '';
          const tokensArr = monaco.editor.tokenize(lineContent, langId);
          const lineTokens = tokensArr && tokensArr[0];
          if (!lineTokens || !lineTokens.length) return false;
          const col0 = Math.max(0, position.column - 1);
          let tokType = '';
          for (let i = lineTokens.length - 1; i >= 0; i--) {
            if (lineTokens[i].offset <= col0) {
              tokType = lineTokens[i].type || '';
              break;
            }
          }
          for (let k = 0; k < NON_UVM_MONACO_TOKEN_PREFIXES.length; k++) {
            if (tokType.startsWith(NON_UVM_MONACO_TOKEN_PREFIXES[k])) return true;
          }
        } catch (err) { }
        return false;
      }

      function buildMonacoLocalTypeContext(model, upToLine) {
        const syms = getUvmSymbols() || {};
        const uvmClasses = syms.classes || {};
        const uvmTypes = syms.types || {};
        const classBaseMap = {};
        const varTypes = {};
        const sources = [];
        if (Array.isArray(filesList)) {
          filesList.forEach(function (f) {
            if (f && f.content && /\.(?:svh?|vh?)$/i.test(f.name || '')) {
              sources.push({ text: f.content, limit: Infinity });
            }
          });
        }
        if (model) {
          sources.push({ text: model.getValue(), limit: upToLine || Infinity });
        }

        const rawParents = {};
        sources.forEach(function (src) {
          const lines = src.text.split('\n');
          const max = Math.min(lines.length, src.limit);
          for (let i = 0; i < max; i++) {
            let clean = lines[i].replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/, '').replace(/"[^"]*"/g, '""');
            if (/\btypedef\b/.test(clean)) continue;
            if (/^\s*(?:virtual\s+)?class\b/.test(clean) && !clean.includes(';')) {
              let j = i + 1;
              while (j < max && j <= i + 6 && !clean.includes(';')) {
                clean += ' ' + lines[j].replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/, '').replace(/"[^"]*"/g, '""');
                j++;
              }
            }
            const mCls = clean.match(/\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:#\s*\([^)]*\)\s*)?extends\s+([A-Za-z_][A-Za-z0-9_]*)/);
            if (mCls) {
              rawParents[mCls[1]] = mCls[2];
            }
          }
        });
        Object.keys(rawParents).forEach(function (c) {
          let curr = rawParents[c];
          const seen = new Set([c]);
          while (curr && !seen.has(curr)) {
            if (uvmClasses[curr]) {
              classBaseMap[c] = curr;
              break;
            }
            seen.add(curr);
            curr = rawParents[curr];
          }
        });

        let currentUvmBase = '';
        let currentClassName = '';
        let inOutOfBlockMethod = false;
        if (model) {
          const maxLine = Math.min(model.getLineCount(), upToLine || model.getLineCount());
          for (let i = 1; i <= maxLine; i++) {
            let clean = (model.getLineContent(i) || '').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/, '').replace(/"[^"]*"/g, '""');
            if (/^\s*endclass\b/.test(clean)) {
              currentUvmBase = '';
              currentClassName = '';
              inOutOfBlockMethod = false;
              continue;
            }
            if (inOutOfBlockMethod && /^\s*end(?:function|task)\b/.test(clean)) {
              currentUvmBase = '';
              currentClassName = '';
              inOutOfBlockMethod = false;
              continue;
            }
            if (!/\btypedef\b/.test(clean) && /^\s*(?:virtual\s+)?class\b/.test(clean)) {
              let j = i + 1;
              while (j <= maxLine && j <= i + 6 && !clean.includes(';')) {
                clean += ' ' + (model.getLineContent(j) || '').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/, '').replace(/"[^"]*"/g, '""');
                j++;
              }
              const mCls = clean.match(/\bclass\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*#\s*\([^)]*\))?(?:\s+extends\s+([A-Za-z_][A-Za-z0-9_]*))?/);
              if (mCls) {
                currentClassName = mCls[1];
                inOutOfBlockMethod = false;
                const knownParent = syms.classParents && syms.classParents[mCls[1]] ? syms.classParents[mCls[1]].parent : '';
                currentUvmBase = (mCls[2] && uvmClasses[mCls[2]]) ? mCls[2] : (knownParent || classBaseMap[mCls[1]] || '');
                continue;
              }
            }
            if (!currentClassName && /^\s*(?:virtual\s+|static\s+|protected\s+|local\s+)*(?:function|task)\b/.test(clean)) {
              const mOut = clean.match(/\b(?:function|task)\b[^;()]*?\b([A-Za-z_][A-Za-z0-9_]*)\s*::\s*[A-Za-z_][A-Za-z0-9_]*\s*(?:\(|;)/);
              if (mOut) {
                currentClassName = mOut[1];
                inOutOfBlockMethod = true;
                const knownParent = syms.classParents && syms.classParents[mOut[1]] ? syms.classParents[mOut[1]].parent : '';
                currentUvmBase = knownParent || classBaseMap[mOut[1]] || '';
              }
            }
            const varRe = /\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:#\s*\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\b/g;
            let mv;
            while ((mv = varRe.exec(clean)) !== null) {
              const tname = mv[1];
              const vname = mv[2];
              if (uvmClasses[tname] || uvmTypes[tname] || classBaseMap[tname]) {
                varTypes[vname] = tname;
              }
            }
          }
        }
        return { classBaseMap: classBaseMap, varTypes: varTypes, currentUvmBase: currentUvmBase, currentClassName: currentClassName };
      }

      function extractMonacoSymbolContext(model, position) {
        if (!model || !position) return null;
        if (isMonacoTokenIgnoredAt(model, position)) return null;
        const word = model.getWordAtPosition(position);
        if (!word) return null;
        const lineContent = model.getLineContent(position.lineNumber) || '';
        const hasBacktick = word.startColumn > 1 && lineContent.charAt(word.startColumn - 2) === '`';
        const clean = word.word.replace(/^`/, '');
        const syms = getUvmSymbols() || {};
        const beforeWord = lineContent.slice(0, Math.max(0, word.startColumn - 1));
        const afterWord = lineContent.slice(Math.max(0, word.endColumn - 1)).trimStart();

        let ownerClass = '';
        let baseClass = '';
        let symKind = hasBacktick ? 'macro' : '';

        const scopeMatch = beforeWord.match(/([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:#\s*\([^)]*\)\s*)?::\s*$/);
        const dotChainMatch = !scopeMatch ? beforeWord.match(/([a-zA-Z_][a-zA-Z0-9_]*(?:\s*\.\s*[a-zA-Z_][a-zA-Z0-9_]*)*)\s*\.\s*$/) : null;
        const dotMatch = dotChainMatch ? [dotChainMatch[0], dotChainMatch[1].split('.').pop().trim()] : null;

        if (afterWord.startsWith('(') || scopeMatch || dotMatch) {
          if (!symKind && !(syms.classes && syms.classes[clean]) && !(syms.types && syms.types[clean])) {
            symKind = 'method';
          }
        }

        if (scopeMatch || dotMatch) {
          const lctx = buildMonacoLocalTypeContext(model, position.lineNumber);
          if (scopeMatch) {
            const qual = scopeMatch[1];
            if (qual === 'type_id') {
              const outerM = beforeWord.match(/([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:#\s*\([^)]*\)\s*)?::\s*type_id\s*::\s*$/);
              const outerBase = outerM ? (lctx.classBaseMap[outerM[1]] || outerM[1]) : '';
              ownerClass = ['uvm_component', 'uvm_test', 'uvm_env', 'uvm_agent', 'uvm_driver', 'uvm_monitor', 'uvm_scoreboard', 'uvm_sequencer'].includes(outerBase)
                ? 'uvm_component_registry'
                : 'uvm_object_registry';
            } else if (syms.classes && syms.classes[qual]) {
              ownerClass = qual;
            } else if (lctx.classBaseMap[qual]) {
              baseClass = lctx.classBaseMap[qual];
            } else {
              ownerClass = qual;
            }
          } else if (dotChainMatch) {
            const parts = dotChainMatch[1].split('.').map(function (s) { return s.trim(); }).filter(Boolean);
            let curType = '';
            const first = parts[0];
            if (first === 'super') {
              curType = lctx.currentUvmBase;
            } else if (first === 'this') {
              curType = (lctx.currentClassName && syms.classes && syms.classes[lctx.currentClassName])
                ? lctx.currentClassName
                : lctx.currentUvmBase;
            } else if (lctx.varTypes[first]) {
              curType = lctx.varTypes[first];
            } else if (lctx.currentClassName || lctx.currentUvmBase) {
              const startCls = (lctx.currentClassName && syms.classes && syms.classes[lctx.currentClassName])
                ? lctx.currentClassName
                : lctx.currentUvmBase;
              const fld = resolveUvmClassField(startCls, first, syms);
              if (fld && fld.var_type) {
                curType = fld.var_type;
              }
            }
            if (!curType && syms.vars && syms.vars[first]) {
              curType = syms.vars[first].var_type || syms.vars[first].class || '';
            }
            for (let pi = 1; pi < parts.length && curType; pi++) {
              const stepCls = (syms.classes && syms.classes[curType]) ? curType : (lctx.classBaseMap[curType] || '');
              const fld = stepCls ? resolveUvmClassField(stepCls, parts[pi], syms) : null;
              curType = (fld && fld.var_type) ? fld.var_type : '';
            }
            if (first === 'super' && parts.length === 1) {
              baseClass = curType;
            } else if (curType) {
              if (syms.classes && syms.classes[curType]) ownerClass = curType;
              else if (lctx.classBaseMap[curType]) baseClass = lctx.classBaseMap[curType];
              else baseClass = curType;
            }
          }
        } else if (!hasBacktick) {
          const lctx = buildMonacoLocalTypeContext(model, position.lineNumber);
          if (clean === 'new') {
            if (/\bfunction\b/.test(beforeWord)) {
              if (lctx.currentClassName && syms.classes && syms.classes[lctx.currentClassName]) {
                ownerClass = lctx.currentClassName;
              } else if (lctx.currentUvmBase) {
                baseClass = lctx.currentUvmBase;
              }
            } else {
              const assignM = beforeWord.match(/([A-Za-z_][A-Za-z0-9_]*)\s*=\s*$/);
              if (assignM && lctx.varTypes[assignM[1]]) {
                const vt = lctx.varTypes[assignM[1]];
                if (syms.classes && syms.classes[vt]) ownerClass = vt;
                else if (lctx.classBaseMap[vt]) baseClass = lctx.classBaseMap[vt];
                else ownerClass = vt;
              }
            }
          } else if (lctx.currentClassName && syms.classes && syms.classes[lctx.currentClassName]) {
            baseClass = lctx.currentClassName;
          } else if (lctx.currentUvmBase) {
            baseClass = lctx.currentUvmBase;
          }
        }

        return {
          word: word,
          clean: clean,
          ownerClass: ownerClass,
          baseClass: baseClass,
          symKind: symKind
        };
      }

      function getMonacoCursorScreenAnchor(position) {
        const rect = monacoPane.getBoundingClientRect();
        let top = rect.top + 40;
        let left = rect.left + 40;
        try {
          const pos = monacoEditorInstance && position ? monacoEditorInstance.getScrolledVisiblePosition(position) : null;
          if (pos) {
            top = rect.top + pos.top;
            left = rect.left + pos.left;
          }
        } catch (err) { }
        return {
          getBoundingClientRect: function () {
            return { top: top, bottom: top + 18, left: left, right: left + 40, width: 40, height: 18 };
          }
        };
      }

      function openUvmDocFromMonaco(cleanToken, ownerClass, baseClass, symKind, position, explicitDocUrl) {
        const resolved = lookupUvmSymbol(cleanToken, ownerClass, baseClass, symKind);
        if (resolved && resolved.isAmbiguous) {
          showSymbolDisambigPopover(getMonacoCursorScreenAnchor(position), resolved);
          return true;
        }
        if (resolved) {
          dispatchOpenDoc(explicitDocUrl || resolved.doc_url || undefined, cleanToken, resolved.ownerClass || ownerClass);
          return true;
        }
        if (explicitDocUrl) {
          dispatchOpenDoc(explicitDocUrl, cleanToken, ownerClass);
          return true;
        }
        return false;
      }

      function findLocalSymbolLineInModel(model, cleanToken) {
        if (!model || !cleanToken) return null;
        const escaped = cleanToken.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const impRegex = new RegExp('(?:function|task)\\s+(?:\\w+\\s+)?\\w+::' + escaped + '\\b');
        const declRegex = new RegExp('^\\s*(?:virtual\\s+|local\\s+|protected\\s+|static\\s+)*(?:class|function|task|typedef|interface|module|package|covergroup|constraint)\\b[^;\\n]*\\b' + escaped + '\\b|^\\s*`define\\s+' + escaped + '\\b');
        const fwdClassRegex = /^\s*typedef\s+(?:interface\s+)?class\b/;
        const lineCount = model.getLineCount();
        for (let i = 1; i <= lineCount; i++) {
          const lineText = model.getLineContent(i);
          if (fwdClassRegex.test(lineText) || /^\s*(?:extern|pure\s+virtual)\b/.test(lineText)) continue;
          if (impRegex.test(lineText) || declRegex.test(lineText)) {
            return i;
          }
        }
        return null;
      }

      function openUvmDefFromMonaco(cleanToken, ownerClass, baseClass, symKind, model) {
        const localLine = findLocalSymbolLineInModel(model, cleanToken);
        const resolved = lookupUvmSymbol(cleanToken, ownerClass, baseClass, symKind);
        const sym = resolved ? (resolved.isAmbiguous ? resolved.primary : resolved) : null;
        if (sym && sym.file) {
          if (window.location.pathname.includes(sym.file + '.html')) {
            revealAndHighlightLineInMonaco(sym.line || localLine || 1);
          } else {
            dispatchOpenSource('src_view/' + sym.file + '.html#L' + (sym.line || 1));
          }
          return true;
        }
        if (localLine) {
          revealAndHighlightLineInMonaco(localLine);
          return true;
        }
        return false;
      }

      function setupMonacoLanguageProviders() {
        if (window.__monacoProvidersRegistered || !window.monaco || !getUvmSymbols()) return;
        window.__monacoProvidersRegistered = true;

        monaco.editor.registerCommand('uvm.openDoc', function (accessor, rawArgs) {
          let args = rawArgs;
          if (typeof args === 'string') {
            try { args = JSON.parse(args); } catch (e) { args = {}; }
          }
          args = args || {};
          const pos = (args.lineNumber && args.column)
            ? { lineNumber: args.lineNumber, column: args.column }
            : (monacoEditorInstance ? monacoEditorInstance.getPosition() : null);
          openUvmDocFromMonaco(args.symbol || '', args.ownerClass || '', args.baseClass || '', args.symKind || '', pos, args.docUrl || '');
        });

        monaco.editor.registerCommand('uvm.openSource', function (accessor, rawArgs) {
          let args = rawArgs;
          if (typeof args === 'string') {
            try { args = JSON.parse(args); } catch (e) { args = {}; }
          }
          args = args || {};
          if (args.file && window.location.pathname.includes(args.file + '.html')) {
            revealAndHighlightLineInMonaco(args.line || 1);
          } else if (args.srcUrl) {
            dispatchOpenSource(args.srcUrl);
          } else if (args.file) {
            dispatchOpenSource('src_view/' + args.file + '.html#L' + (args.line || 1));
          }
        });

        monaco.languages.registerHoverProvider('uvm-systemverilog', {
          provideHover: function (model, position) {
            const ctx = extractMonacoSymbolContext(model, position);
            if (!ctx) return null;
            const resolved = lookupUvmSymbol(ctx.clean, ctx.ownerClass, ctx.baseClass, ctx.symKind);
            if (!resolved) return null;
            const sym = resolved.isAmbiguous ? resolved.primary : resolved;
            const entry = sym.entry || {};
            const typeLabel = (sym.type || 'symbol').toUpperCase();
            const titleText = `${sym.ownerClass ? sym.ownerClass + '::' : ''}${ctx.clean}`;
            const contents = [
              { value: `**[${typeLabel}]** \`${titleText}\`` }
            ];
            if (entry.params || entry.extends) {
              contents.push({ value: `\`\`\`systemverilog\n${sym.type || 'class'} ${ctx.clean}${entry.params ? ' #(' + entry.params + ')' : ''}${entry.extends ? ' extends ' + entry.extends : ''}\n\`\`\`` });
            } else if (entry.signature) {
              contents.push({ value: `\`\`\`systemverilog\n${entry.signature}\n\`\`\`` });
            }
            if (resolved.isAmbiguous && resolved.candidates) {
              const preview = resolved.candidates.slice(0, 3).map(function (c) { return c.class; }).join(', ');
              contents.push({ value: `*Defined in ${resolved.candidates.length} classes:* ${preview}${resolved.candidates.length > 3 ? ', ...' : ''}` });
            }
            if (sym.file) {
              contents.push({ value: `*Source:* \`${sym.file}:${sym.line || 1}\`` });
            }
            if (sym.doc) {
              contents.push({ value: sym.doc });
            }

            const actions = [];
            if (sym.doc_url || resolved.isAmbiguous) {
              const docArgs = encodeURIComponent(JSON.stringify({
                symbol: ctx.clean,
                docUrl: sym.doc_url || '',
                ownerClass: sym.ownerClass || ctx.ownerClass || '',
                baseClass: ctx.baseClass || '',
                symKind: ctx.symKind || '',
                lineNumber: position.lineNumber,
                column: position.column
              }));
              actions.push(`[View Docs](command:uvm.openDoc?${docArgs})`);
            }
            if (sym.file) {
              const srcArgs = encodeURIComponent(JSON.stringify({
                file: sym.file,
                line: sym.line || 1,
                srcUrl: `src_view/${sym.file}.html#L${sym.line || 1}`
              }));
              actions.push(`[Go to Definition (F12)](command:uvm.openSource?${srcArgs})`);
            }
            if (actions.length > 0) {
              contents.push({
                value: actions.join(' &nbsp;|&nbsp; '),
                isTrusted: true
              });
            }
            return {
              range: new monaco.Range(position.lineNumber, ctx.word.startColumn, position.lineNumber, ctx.word.endColumn),
              contents: contents
            };
          }
        });

        monaco.languages.registerDefinitionProvider('uvm-systemverilog', {
          provideDefinition: function (model, position) {
            const ctx = extractMonacoSymbolContext(model, position);
            if (!ctx) return null;
            const localLine = findLocalSymbolLineInModel(model, ctx.clean);
            if (localLine) {
              return {
                uri: model.uri,
                range: new monaco.Range(localLine, 1, localLine, 1)
              };
            }
            const resolved = lookupUvmSymbol(ctx.clean, ctx.ownerClass, ctx.baseClass, ctx.symKind);
            const sym = resolved ? (resolved.isAmbiguous ? resolved.primary : resolved) : null;
            if (sym && sym.file && window.location.pathname.includes(sym.file + '.html')) {
              return {
                uri: model.uri,
                range: new monaco.Range(sym.line || 1, 1, sym.line || 1, 1)
              };
            }
            return null;
          }
        });

        monaco.languages.registerDocumentSymbolProvider('uvm-systemverilog', {
          provideDocumentSymbols: function (model) {
            const lineCount = model.getLineCount();
            const roots = [];
            const stack = [];
            let inBlockComment = false;

            const startPatterns = [
              { kind: monaco.languages.SymbolKind.Class, re: /^\s*(?:virtual\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)/, endRe: /^\s*endclass\b/ },
              { kind: monaco.languages.SymbolKind.Interface, re: /^\s*interface\s+(?:automatic\s+)?([a-zA-Z_][a-zA-Z0-9_]*)/, endRe: /^\s*endinterface\b/ },
              { kind: monaco.languages.SymbolKind.Module, re: /^\s*module\s+(?:automatic\s+)?([a-zA-Z_][a-zA-Z0-9_]*)/, endRe: /^\s*endmodule\b/ },
              { kind: monaco.languages.SymbolKind.Package, re: /^\s*package\s+(?:automatic\s+)?([a-zA-Z_][a-zA-Z0-9_]*)/, endRe: /^\s*endpackage\b/ },
              { kind: monaco.languages.SymbolKind.Function, re: /^\s*(?:(?:virtual|local|protected|static|pure|extern)\s+)*function\s+(?:automatic\s+)?(?:[\w:<>#\[\]\s]+\s+)?([a-zA-Z_][a-zA-Z0-9_:]*)\s*\(/, endRe: /^\s*endfunction\b/ },
              { kind: monaco.languages.SymbolKind.Method, re: /^\s*(?:(?:virtual|local|protected|static|pure|extern)\s+)*task\s+(?:automatic\s+)?([a-zA-Z_][a-zA-Z0-9_:]*)\s*(?:\(|;)/, endRe: /^\s*endtask\b/ },
              { kind: monaco.languages.SymbolKind.Struct, re: /^\s*covergroup\s+([a-zA-Z_][a-zA-Z0-9_]*)/, endRe: /^\s*endgroup\b/ }
            ];

            for (let i = 1; i <= lineCount; i++) {
              let line = model.getLineContent(i);
              if (inBlockComment) {
                const endIdx = line.indexOf('*/');
                if (endIdx !== -1) {
                  inBlockComment = false;
                  line = line.slice(endIdx + 2);
                } else {
                  continue;
                }
              }
              const blkStart = line.indexOf('/*');
              if (blkStart !== -1 && line.indexOf('*/', blkStart + 2) === -1) {
                inBlockComment = true;
                line = line.slice(0, blkStart);
              }
              line = line.replace(/\/\*[\s\S]*?\*\//g, '').replace(/"(?:[^"\\]|\\.)*"/g, '""').replace(/\/\/.*$/, '');
              if (!line.trim()) continue;

              if (stack.length > 0 && stack[stack.length - 1].endRe.test(line)) {
                const top = stack.pop();
                top.symbol.range = new monaco.Range(top.startLine, 1, i, model.getLineMaxColumn(i));
                continue;
              }

              if (/\btypedef\b/.test(line) && /\bclass\b/.test(line)) continue;
              if (/^\s*(?:import|export)\s+"DPI/i.test(line)) continue;

              let matched = false;
              for (let p = 0; p < startPatterns.length; p++) {
                const pat = startPatterns[p];
                const m = line.match(pat.re);
                if (m && m[1]) {
                  const symNode = {
                    name: m[1],
                    detail: '',
                    kind: pat.kind,
                    range: new monaco.Range(i, 1, i, model.getLineMaxColumn(i)),
                    selectionRange: new monaco.Range(i, 1, i, model.getLineMaxColumn(i)),
                    children: []
                  };
                  if (stack.length > 0) {
                    stack[stack.length - 1].symbol.children.push(symNode);
                  } else {
                    roots.push(symNode);
                  }
                  if (!/^\s*(?:extern|pure\s+virtual)\b/.test(line)) {
                    stack.push({ symbol: symNode, startLine: i, endRe: pat.endRe });
                  }
                  matched = true;
                  break;
                }
              }
              if (matched) continue;

              const tdMatch = line.match(/^\s*typedef\s+.*\b([a-zA-Z_][a-zA-Z0-9_]*)\s*;/);
              if (tdMatch && tdMatch[1]) {
                const tdSym = {
                  name: tdMatch[1],
                  detail: 'typedef',
                  kind: monaco.languages.SymbolKind.TypeParameter,
                  range: new monaco.Range(i, 1, i, model.getLineMaxColumn(i)),
                  selectionRange: new monaco.Range(i, 1, i, model.getLineMaxColumn(i)),
                  children: []
                };
                if (stack.length > 0) stack[stack.length - 1].symbol.children.push(tdSym);
                else roots.push(tdSym);
              }
            }
            while (stack.length > 0) {
              const top = stack.pop();
              top.symbol.range = new monaco.Range(top.startLine, 1, lineCount, model.getLineMaxColumn(lineCount));
            }
            return roots;
          }
        });

        monaco.languages.registerFoldingRangeProvider('uvm-systemverilog', {
          provideFoldingRanges: function (model) {
            const lineCount = model.getLineCount();
            const ranges = [];
            const blockStack = [];
            const ifdefStack = [];
            let commentStart = -1;

            const openers = [
              { open: /^\s*(?:virtual\s+)?class\b/, close: /^\s*endclass\b/ },
              { open: /^\s*(?:(?:virtual|local|protected|static|pure)\s+)*function\b/, close: /^\s*endfunction\b/ },
              { open: /^\s*(?:(?:virtual|local|protected|static|pure)\s+)*task\b/, close: /^\s*endtask\b/ },
              { open: /^\s*module\b/, close: /^\s*endmodule\b/ },
              { open: /^\s*interface\b/, close: /^\s*endinterface\b/ },
              { open: /^\s*package\b/, close: /^\s*endpackage\b/ },
              { open: /^\s*program\b/, close: /^\s*endprogram\b/ },
              { open: /^\s*covergroup\b/, close: /^\s*endgroup\b/ },
              { open: /^\s*case[xz]?\b/, close: /^\s*endcase\b/ },
              { open: /\bbegin\b(?:\s*:\s*\w+)?\s*(?:\/\/.*)?$/, close: /^\s*end\b/ },
              { open: /^\s*fork\b/, close: /^\s*join(?:_any|_none)?\b/ }
            ];

            for (let i = 1; i <= lineCount; i++) {
              const rawLine = model.getLineContent(i);
              if (commentStart === -1) {
                const cIdx = rawLine.indexOf('/*');
                if (cIdx !== -1 && rawLine.indexOf('*/', cIdx + 2) === -1) {
                  commentStart = i;
                }
              } else if (rawLine.indexOf('*/') !== -1) {
                if (i > commentStart) {
                  ranges.push({ start: commentStart, end: i, kind: monaco.languages.FoldingRangeKind.Comment });
                }
                commentStart = -1;
                continue;
              }
              if (commentStart !== -1) continue;

              const line = rawLine.replace(/\/\*[\s\S]*?\*\//g, '').replace(/"(?:[^"\\]|\\.)*"/g, '""').replace(/\/\/.*$/, '');
              if (/^\s*`ifn?def\b/.test(line)) {
                ifdefStack.push(i);
                continue;
              }
              if (/^\s*`endif\b/.test(line) && ifdefStack.length > 0) {
                const start = ifdefStack.pop();
                if (i > start) ranges.push({ start: start, end: i, kind: monaco.languages.FoldingRangeKind.Region });
                continue;
              }
              if (/^\s*(?:extern|pure\s+virtual)\b/.test(line)) continue;
              if (/\btypedef\b/.test(line)) continue;
              if (/^\s*(?:import|export)\s+"DPI/i.test(line)) continue;

              let closed = false;
              for (let s = blockStack.length - 1; s >= 0; s--) {
                if (blockStack[s].close.test(line)) {
                  const popped = blockStack.splice(s, 1)[0];
                  if (i > popped.start) ranges.push({ start: popped.start, end: i });
                  closed = true;
                  break;
                }
              }
              if (closed && !/\bbegin\b(?:\s*:\s*\w+)?\s*$/.test(line)) continue;

              for (let k = 0; k < openers.length; k++) {
                if (openers[k].open.test(line)) {
                  blockStack.push({ start: i, close: openers[k].close });
                  break;
                }
              }
            }
            return ranges;
          }
        });
      }

      function attachMonacoEditorActions(editor) {
        if (!editor || editor.__uvmActionsAttached) return;
        editor.__uvmActionsAttached = true;

        editor.addAction({
          id: 'uvm-view-docs',
          label: 'UVM: View Documentation',
          keybindings: [monaco.KeyMod.Alt | monaco.KeyCode.KeyD],
          contextMenuGroupId: 'navigation',
          contextMenuOrder: 1.1,
          run: function (ed) {
            const pos = ed.getPosition();
            const ctx = extractMonacoSymbolContext(ed.getModel(), pos);
            if (ctx) {
              openUvmDocFromMonaco(ctx.clean, ctx.ownerClass, ctx.baseClass, ctx.symKind, pos, '');
            }
          }
        });

        editor.addAction({
          id: 'uvm-goto-def',
          label: 'UVM: Go to Definition',
          keybindings: [monaco.KeyCode.F12],
          contextMenuGroupId: 'navigation',
          contextMenuOrder: 1.2,
          run: function (ed) {
            const pos = ed.getPosition();
            const ctx = extractMonacoSymbolContext(ed.getModel(), pos);
            if (ctx) {
              openUvmDefFromMonaco(ctx.clean, ctx.ownerClass, ctx.baseClass, ctx.symKind, ed.getModel());
            }
          }
        });

        editor.addAction({
          id: 'uvm-toggle-sticky-scroll',
          label: 'UVM: Toggle Sticky Scroll',
          contextMenuGroupId: '1_modification',
          contextMenuOrder: 9.1,
          run: function (ed) {
            const cur = ed.getOption(monaco.editor.EditorOption.stickyScroll);
            const nextEnabled = !(cur && cur.enabled);
            ed.updateOptions({ stickyScroll: { enabled: nextEnabled } });
            try { localStorage.setItem(MONACO_STICKY_KEY, nextEnabled ? '1' : '0'); } catch (e) { }
          }
        });

        editor.onMouseDown(function (e) {
          if (!e.target || !e.target.position) return;
          const ev = e.event;
          if (!(ev.ctrlKey || ev.metaKey || ev.altKey)) return;
          const model = editor.getModel();
          const ctx = extractMonacoSymbolContext(model, e.target.position);
          if (!ctx) return;
          if (ev.altKey && !ev.ctrlKey && !ev.metaKey) {
            openUvmDocFromMonaco(ctx.clean, ctx.ownerClass, ctx.baseClass, ctx.symKind, e.target.position, '');
          } else if (ev.ctrlKey || ev.metaKey) {
            openUvmDefFromMonaco(ctx.clean, ctx.ownerClass, ctx.baseClass, ctx.symKind, model);
          }
        });
      }

      function getMonacoTheme() {
        const curTheme = document.documentElement.getAttribute('data-theme') || 'light';
        return (curTheme === 'dark' || curTheme === 'night') ? 'uvm-dark' : 'uvm-light';
      }

      const VSCODE_ICON_SVG = '<svg class="monaco-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .326 8.74L3.899 12 .326 15.26a1 1 0 0 0 .001 1.479L1.65 17.94a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352zM18 17.5l-6-5.5 6-5.5v11z"/></svg>';
      const CLOSE_ICON_SVG = '<svg class="monaco-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

      function getInitialTargetLine() {
        const hash = window.location.hash;
        if (hash && (hash.startsWith('#L') || hash.startsWith('#line-'))) {
          const n = parseInt(hash.replace(/^#(?:L|line-)/, ''), 10);
          if (!isNaN(n) && n >= 1) return n;
        }
        const activeRow = document.querySelector('.file-code-pane tr.active-line, .sv-code-table tr.active-line');
        if (activeRow) {
          const raw = activeRow.id ? activeRow.id.replace(/^L/, '') : activeRow.getAttribute('data-line');
          const n = parseInt(raw || '', 10);
          if (!isNaN(n) && n >= 1) return n;
        }
        return null;
      }

      let monacoTutAddedDecorations = [];
      function applyTutorialAddedLines() {
        if (!monacoEditorInstance || !window.monaco || !window.__tutAddedLinesByFile) return;
        const fname = getActiveFileName();
        const added = window.__tutAddedLinesByFile[fname] || [];
        const decs = added.map(function (ln) {
          return {
            range: new monaco.Range(ln, 1, ln, 1),
            options: { isWholeLine: true, className: 'tut-line-added' }
          };
        });
        monacoTutAddedDecorations = monacoEditorInstance.deltaDecorations(monacoTutAddedDecorations, decs);
      }

      function activateMonaco() {
        const activationId = ++monacoActivationSeq;

        if (studioCodeContainer) {
          studioCodeContainer.scrollTop = 0;
          studioCodeContainer.scrollLeft = 0;
          studioCodeContainer.classList.add('monaco-active');
          if (studioCodeContainer.classList.contains('studio-code-container') && !studioCodeContainer.style.height) {
            const prevHeight = studioCodeContainer.offsetHeight || 0;
            studioCodeContainer.style.height = Math.max(prevHeight, 520) + 'px';
          }
        }

        loadMonacoScript(function () {
          if (activationId !== monacoActivationSeq) return;
          registerUvmSystemVerilogLanguage();
          defineUvmMonacoThemes();
          setupMonacoLanguageProviders();

          const codeText = getActiveCodeText();
          const lang = detectMonacoLanguage(getActiveFileName());
          const themeName = getMonacoTheme();
          let stickyEnabled = true;
          try { stickyEnabled = localStorage.getItem(MONACO_STICKY_KEY) !== '0'; } catch (e) { }

          if (fallbackPre) fallbackPre.style.display = 'none';
          monacoPane.style.display = 'block';
          monacoPane.classList.add('active');

          if (!monacoEditorInstance) {
            monacoEditorInstance = monaco.editor.create(monacoPane, {
              value: codeText,
              language: lang,
              theme: themeName,
              readOnly: true,
              lineNumbers: 'on',
              renderWhitespace: 'none',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              fontFamily: 'Consolas, "Cascadia Mono", "Roboto Mono", SFMono-Regular, Menlo, Monaco, monospace',
              fontSize: 13,
              fontLigatures: false,
              minimap: { enabled: true },
              stickyScroll: { enabled: stickyEnabled },
              smoothScrolling: true,
              bracketPairColorization: { enabled: false },
              guides: { bracketPairs: false, indentation: false },
              occurrencesHighlight: 'singleFile',
              folding: true
            });
            attachMonacoEditorActions(monacoEditorInstance);
          } else {
            const model = monacoEditorInstance.getModel();
            if (model) monaco.editor.setModelLanguage(model, lang);
            monacoEditorInstance.setValue(codeText);
            monaco.editor.setTheme(themeName);
          }

          isMonacoActive = true;
          applyTutorialAddedLines();

          const targetLine = pendingMonacoTargetLine || getInitialTargetLine();
          pendingMonacoTargetLine = null;
          monacoEditorInstance.layout();
          const initialLayoutInfo = monacoEditorInstance.getLayoutInfo ? monacoEditorInstance.getLayoutInfo() : null;
          const hadHeight = initialLayoutInfo && initialLayoutInfo.height > 0;
          if (targetLine && hadHeight) {
            revealAndHighlightLineInMonaco(targetLine);
          } else if (targetLine) {
            requestAnimationFrame(function () {
              if (activationId !== monacoActivationSeq || !monacoEditorInstance) return;
              monacoEditorInstance.layout();
              revealAndHighlightLineInMonaco(targetLine);
            });
          }
          setTimeout(function () {
            if (activationId === monacoActivationSeq && monacoEditorInstance) {
              monacoEditorInstance.layout();
            }
          }, 80);
        }, function () {
          if (activationId !== monacoActivationSeq) return;
          if (fallbackPre) {
            fallbackPre.textContent = getActiveCodeText();
            fallbackPre.style.display = 'block';
          } else {
            deactivateMonaco();
          }
        });
      }

      function deactivateMonaco() {
        monacoActivationSeq++;
        isMonacoActive = false;
        monacoPane.style.display = 'none';
        monacoPane.classList.remove('active');
        if (fallbackPre) fallbackPre.style.display = 'none';
        if (studioCodeContainer) {
          studioCodeContainer.classList.remove('monaco-active');
          if (studioCodeContainer.classList.contains('studio-code-container')) {
            studioCodeContainer.style.height = '';
          }
        }
        btnToggleMonaco.classList.remove('active');
        btnToggleMonaco.innerHTML = VSCODE_ICON_SVG + '<span>Monaco IDE</span>';
        try { localStorage.setItem(MONACO_STATE_KEY, '0'); } catch (e) { }
      }

      btnToggleMonaco.addEventListener('click', function () {
        if (isMonacoActive) {
          deactivateMonaco();
        } else {
          btnToggleMonaco.classList.add('active');
          btnToggleMonaco.innerHTML = CLOSE_ICON_SVG + '<span>Classic View</span>';
          try { localStorage.setItem(MONACO_STATE_KEY, '1'); } catch (e) { }
          activateMonaco();
        }
      });

      registerMessageHandler(function (data) {
        if (data.theme && monacoEditorInstance && window.monaco) {
          const theme = (data.theme === 'dark' || data.theme === 'night') ? 'uvm-dark' : 'uvm-light';
          monaco.editor.setTheme(theme);
        }
      });

      // Always start in the default Classic View on page load; Monaco opens on demand via #btn-toggle-monaco
      monacoPane.style.display = 'none';
      if (studioCodeContainer) studioCodeContainer.classList.remove('monaco-active');
      try { localStorage.setItem(MONACO_STATE_KEY, '0'); } catch (e) { }

      // Expose helpers for tab switches and tutorial line decorations
      window.__detectUvmMonacoLanguage = detectMonacoLanguage;
      window.__getActiveUvmFileName = getActiveFileName;
      window.__applyMonacoTutorialAddedLines = applyTutorialAddedLines;
    })();

    // Synchronize tab switches with Monaco
    onFileTabSwitched = function (idx) {
      if (isMonacoActive && monacoEditorInstance) {
        const model = monacoEditorInstance.getModel();
        if (model && window.monaco && window.__detectUvmMonacoLanguage && window.__getActiveUvmFileName) {
          monaco.editor.setModelLanguage(model, window.__detectUvmMonacoLanguage(window.__getActiveUvmFileName()));
        }
        monacoEditorInstance.setValue(getActiveCodeText());
        monacoEditorInstance.setScrollTop(0);
        monacoEditorInstance.setPosition({ lineNumber: 1, column: 1 });
        monacoActiveLineDecorations = monacoEditorInstance.deltaDecorations(monacoActiveLineDecorations, []);
        if (typeof window.__applyMonacoTutorialAddedLines === 'function') {
          window.__applyMonacoTutorialAddedLines();
        }
      } else {
        const fallbackPre = document.getElementById('monaco-fallback-pre');
        if (fallbackPre && fallbackPre.style.display === 'block') {
          fallbackPre.textContent = getActiveCodeText();
        }
      }
    };

    // 6. Editor Keyboard Shortcuts (Alt+Z Word Wrap, Ctrl+G Go to Line)
    (function initCodeEditorShortcuts() {
      const btnToggleWrap = document.getElementById('btn-toggle-wrap');

      function toggleWrap() {
        if (!studioCodeContainer) return;
        const isWrapped = studioCodeContainer.classList.toggle('code-wrap-active');
        if (btnToggleWrap) btnToggleWrap.classList.toggle('active', isWrapped);
        if (isMonacoActive && monacoEditorInstance) {
          monacoEditorInstance.updateOptions({ wordWrap: isWrapped ? 'on' : 'off' });
        }
      }

      if (btnToggleWrap) {
        btnToggleWrap.addEventListener('click', toggleWrap);
      }

      window.addEventListener('keydown', function (e) {
        if (e.altKey && (e.key === 'z' || e.key === 'Z')) {
          e.preventDefault();
          toggleWrap();
        }
        if ((e.ctrlKey || e.metaKey) && (e.key === 'g' || e.key === 'G')) {
          e.preventDefault();
          if (isMonacoActive && monacoEditorInstance) {
            monacoEditorInstance.focus();
            monacoEditorInstance.trigger('keyboard', 'editor.action.gotoLine', null);
            return;
          }
          const input = prompt('Go to line number:');
          if (input) {
            const line = parseInt(input.trim().replace(/^L/, ''), 10);
            if (!isNaN(line)) {
              scrollToLine(line);
            }
          }
        }
      });
    })();

    // Hash and cross-frame scrollToSection / line handling
    function handleInitialHash() {
      const hash = window.location.hash;
      if (hash && (hash.startsWith('#L') || hash.startsWith('#line-'))) {
        scrollToLine(hash);
      }
    }
    window.addEventListener('hashchange', handleInitialHash);
    setTimeout(handleInitialHash, 100);

    registerMessageHandler(function (data) {
      if (data.type === 'scrollToSection') {
        const anchor = data.anchor || data.id;
        if (anchor && (anchor.startsWith('L') || anchor.startsWith('#L') || anchor.startsWith('line-'))) {
          scrollToLine(anchor);
          sendScrollAck(data.navToken, anchor, data.id || anchor);
        }
      }
    });

    // Expose control methods
    return {
      switchFileTab: switchFileTab,
      switchFile: function (filename) {
        if (!filename) return false;
        const cleanTarget = filename.replace(/\\/g, '/');
        const idx = filesList.findIndex(function (f) {
          const fn = f.name.replace(/\\/g, '/');
          return fn === cleanTarget || fn.endsWith('/' + cleanTarget) || cleanTarget.endsWith('/' + fn);
        });
        if (idx !== -1) {
          switchFileTab(idx);
          return true;
        }
        return false;
      },
      getCurrentFileIdx: function () { return currentFileIdx; },
      scrollToLine: scrollToLine
    };
  }

  // =========================================================================
  // UVM Symbol Resolution, Disambiguation Popover & Cross-Frame Routing
  // =========================================================================

  const HOVERABLE_TOKEN_CLASSES = ['sv-ident', 'sv-type', 'sv-uvm-type', 'sv-method', 'sv-macro', 'sv-constant'];

  function isHoverableToken(el) {
    if (!el || !el.classList) return false;
    for (let i = 0; i < HOVERABLE_TOKEN_CLASSES.length; i++) {
      if (el.classList.contains(HOVERABLE_TOKEN_CLASSES[i])) return true;
    }
    return false;
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function getCurrentBackContext() {
    try {
      const p = window.location.pathname.replace(/\\/g, '/');
      const tutMatch = p.match(/(tutorial_view\/[^/]+\.html)$/);
      if (tutMatch) {
        return { kind: 'tutorial', url: tutMatch[1], title: document.title.split('|')[0].trim() };
      }
      const exMatch = p.match(/(examples_view\/[^/]+\/[^/]+\.html)$/);
      if (exMatch) {
        return { kind: 'example', url: exMatch[1], title: document.title.split('|')[0].trim() };
      }
    } catch (e) { }
    return null;
  }

  function dispatchOpenDoc(docUrl, symbol, ownerClass) {
    const fromCtx = getCurrentBackContext();
    if (window.parent && window.parent !== window) {
      if (!fromCtx) {
        try {
          if (window.parent.openDocView) {
            window.parent.openDocView(docUrl || undefined, symbol, ownerClass || undefined);
            return;
          }
        } catch (err) { }
      }
      window.parent.postMessage({
        type: 'openDocView',
        symbol: symbol,
        ownerClass: ownerClass || undefined,
        url: docUrl || undefined,
        fromTutorial: fromCtx || undefined
      }, '*');
      return;
    }
    if (docUrl) {
      window.location.href = '../' + docUrl.replace(/^(\.\.\/)+/, '');
    }
  }

  function dispatchOpenSource(srcUrl) {
    if (!srcUrl) return;
    if (window.parent && window.parent !== window) {
      try {
        if (window.parent.openSourceView) {
          window.parent.openSourceView(srcUrl);
          return;
        }
      } catch (err) { }
      window.parent.postMessage({ type: 'openSourceView', url: srcUrl }, '*');
      return;
    }
    window.location.href = '../' + srcUrl.replace(/^(\.\.\/)+/, '');
  }

  function getUvmAncestorChain(clsName) {
    const chain = [];
    const seen = new Set();
    let curr = clsName;
    let nodes = null;
    try {
      nodes = window.parent && window.parent.UVM_DATA && window.parent.UVM_DATA.classHierarchy
        ? window.parent.UVM_DATA.classHierarchy.nodes
        : null;
    } catch (err) {
      nodes = null;
    }
    while (curr && !seen.has(curr)) {
      seen.add(curr);
      chain.push(curr);
      if (nodes && nodes[curr]) {
        curr = nodes[curr].parent;
      } else {
        const syms = getUvmSymbols();
        curr = (syms && syms.classParents && syms.classParents[curr]) ? syms.classParents[curr].parent : null;
      }
    }
    return chain;
  }

  const SV_NATIVE_METHODS_JS = new Set([
    'size', 'exists', 'delete', 'first', 'last', 'next', 'prev',
    'find', 'find_index', 'find_first', 'find_last', 'min', 'max', 'sum',
    'sort', 'rsort', 'shuffle', 'reverse', 'unique',
    'pop_front', 'pop_back', 'push_front', 'push_back', 'insert',
    'num', 'len', 'substr', 'atoi', 'atohex', 'atooct', 'atobin', 'itoa', 'hextoa', 'octtoa', 'bintoa',
    'toupper', 'tolower', 'getc', 'putc', 'compare', 'icompare'
  ]);

  function isKnownUvmOwnerClass(clsName, syms) {
    if (!clsName) return false;
    if (clsName === 'Global' || clsName === 'Globals') return true;
    return Boolean((syms.classes && syms.classes[clsName]) || (syms.classParents && syms.classParents[clsName]));
  }

  function resolveUvmClassField(clsName, fieldName, syms) {
    if (!clsName || !fieldName || !syms || !syms.classFields) return null;
    const chain = getUvmAncestorChain(clsName);
    for (let i = 0; i < chain.length; i++) {
      const cmap = syms.classFields[chain[i]];
      if (cmap && cmap[fieldName]) {
        return Object.assign({ class: chain[i] }, cmap[fieldName]);
      }
    }
    return null;
  }

  const PRIORITY_DISAMBIG_CLASSES = new Set([
    'Global', 'Globals', 'uvm_object', 'uvm_component', 'uvm_objection',
    'uvm_phase', 'uvm_config_db', 'uvm_reg', 'uvm_reg_field', 'uvm_mem',
    'uvm_reg_block', 'uvm_analysis_port', 'uvm_tlm_fifo', 'uvm_sequence_base',
    'uvm_sequencer_base', 'uvm_root', 'uvm_factory', 'uvm_report_object'
  ]);

  function formatSingleSymbol(name, type, entry) {
    return {
      isAmbiguous: false,
      name: name,
      type: (entry && entry.type) || type || 'symbol',
      kind: (entry && (entry.kind || entry.type)) || type || 'symbol',
      ownerClass: (entry && entry.class) || '',
      ret: (entry && entry.ret) || '',
      file: (entry && entry.file) || '',
      line: (entry && entry.line) || 1,
      doc: (entry && entry.doc) || '',
      doc_url: (entry && entry.doc_url) || '',
      entry: entry
    };
  }

  function resolveMethodEntry(cleanToken, candidates, ownerClass, baseClass) {
    if (!Array.isArray(candidates) || candidates.length === 0) return null;
    const publicCands = candidates.filter(c => c.class && !c.class.startsWith('m_uvm_'));
    const pool = publicCands.length > 0 ? publicCands : candidates;

    function wrapCandidate(c) {
      return {
        isAmbiguous: false,
        name: cleanToken,
        type: c.kind || 'method',
        kind: c.kind || 'method',
        ownerClass: c.class || '',
        ret: c.ret || '',
        file: c.file || '',
        line: c.line || 1,
        doc: c.doc || '',
        doc_url: c.doc_url || '',
        entry: c
      };
    }

    if (ownerClass) {
      if (ownerClass === 'Global' || ownerClass === 'Globals') {
        const gMatch = pool.find(c => c.class === 'Global' || c.class === 'Globals')
          || candidates.find(c => c.class === 'Global' || c.class === 'Globals');
        if (gMatch) return wrapCandidate(gMatch);
      } else {
        const chain = getUvmAncestorChain(ownerClass);
        for (let i = 0; i < chain.length; i++) {
          const match = pool.find(c => c.class === chain[i]) || candidates.find(c => c.class === chain[i]);
          if (match) return wrapCandidate(match);
        }
      }
    }

    if (baseClass) {
      const chain = getUvmAncestorChain(baseClass);
      for (let i = 0; i < chain.length; i++) {
        const match = pool.find(c => c.class === chain[i]) || candidates.find(c => c.class === chain[i]);
        if (match) return wrapCandidate(match);
      }
    }

    if (pool.length === 1) {
      return wrapCandidate(pool[0]);
    }

    // Deduplicate by distinct doc target when every candidate points to the exact same anchored doc item
    const distinctDocUrls = new Set(pool.map(c => c.doc_url || (c.file + ':' + c.line)));
    if (distinctDocUrls.size === 1) {
      const onlyDocUrl = pool[0].doc_url || '';
      if (onlyDocUrl.includes('#doc-nav-')) {
        const best = pool.find(c => c.class === 'uvm_component' || c.class === 'uvm_object') || pool[0];
        return wrapCandidate(best);
      }
    }

    const sorted = pool.slice().sort((a, b) => {
      const ap = PRIORITY_DISAMBIG_CLASSES.has(a.class) ? 0 : 1;
      const bp = PRIORITY_DISAMBIG_CLASSES.has(b.class) ? 0 : 1;
      if (ap !== bp) return ap - bp;
      return String(a.class).localeCompare(String(b.class));
    });

    const primary = wrapCandidate(sorted[0]);
    return {
      isAmbiguous: true,
      name: cleanToken,
      type: primary.type,
      kind: primary.kind,
      candidates: sorted,
      primary: primary
    };
  }

  function lookupUvmSymbol(token, ownerClass, baseClass, symKind) {
    const cleanToken = String(token || '').trim().replace(/^`/, '');
    const syms = getUvmSymbols();
    if (!cleanToken || !syms) return null;

    const ownerIsKnownUvm = isKnownUvmOwnerClass(ownerClass, syms);
    const baseIsKnownUvm = isKnownUvmOwnerClass(baseClass, syms);
    // Reject explicitly non-UVM receivers (e.g. vif.reset(), my_queue.size())
    if (ownerClass && !ownerIsKnownUvm && !baseIsKnownUvm) {
      return null;
    }

    function canResolveMethod() {
      if (cleanToken === 'new' && !ownerIsKnownUvm && !baseIsKnownUvm) {
        return false;
      }
      if (SV_NATIVE_METHODS_JS.has(cleanToken) && !ownerIsKnownUvm && !baseIsKnownUvm) {
        return false;
      }
      return true;
    }

    if (symKind === 'method' && syms.methods && syms.methods[cleanToken]) {
      return canResolveMethod() ? resolveMethodEntry(cleanToken, syms.methods[cleanToken], ownerClass, baseClass) : null;
    }
    if (symKind === 'macro' && syms.macros && syms.macros[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'macro', syms.macros[cleanToken]);
    }
    if (symKind === 'constant' && syms.constants && syms.constants[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'constant', syms.constants[cleanToken]);
    }
    if (symKind === 'type' && syms.types && syms.types[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'type', syms.types[cleanToken]);
    }
    if (symKind === 'var' && syms.vars && syms.vars[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'variable', syms.vars[cleanToken]);
    }

    if (syms.classes && syms.classes[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'class', syms.classes[cleanToken]);
    }
    if (syms.macros && syms.macros[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'macro', syms.macros[cleanToken]);
    }
    if (syms.types && syms.types[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'type', syms.types[cleanToken]);
    }
    if (syms.constants && syms.constants[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'constant', syms.constants[cleanToken]);
    }
    if (ownerIsKnownUvm || baseIsKnownUvm) {
      const targetCls = ownerIsKnownUvm ? ownerClass : baseClass;
      const cf = resolveUvmClassField(targetCls, cleanToken, syms);
      if (cf) {
        return formatSingleSymbol(cleanToken, cf.kind || 'variable', cf);
      }
    }

    if (syms.vars && syms.vars[cleanToken]) {
      const vEntry = syms.vars[cleanToken];
      const isGlobalUvmVar = /^(?:uvm_|ovm_|\+UVM_|\+uvm_)/.test(cleanToken);
      if (isGlobalUvmVar) {
        return formatSingleSymbol(cleanToken, 'variable', vEntry);
      }
      if (ownerIsKnownUvm || baseIsKnownUvm) {
        const targetCls = ownerIsKnownUvm ? ownerClass : baseClass;
        const chain = getUvmAncestorChain(targetCls);
        if (!vEntry.class || chain.includes(vEntry.class)) {
          return formatSingleSymbol(cleanToken, 'variable', vEntry);
        }
      }
    }
    if (syms.methods && syms.methods[cleanToken]) {
      return canResolveMethod() ? resolveMethodEntry(cleanToken, syms.methods[cleanToken], ownerClass, baseClass) : null;
    }
    return null;
  }

  let activeDisambigPopover = null;

  function closeSymbolDisambigPopover() {
    if (activeDisambigPopover) {
      activeDisambigPopover.classList.remove('visible');
    }
  }

  function showSymbolDisambigPopover(anchorEl, resolved) {
    if (!anchorEl || !resolved || !resolved.candidates || !resolved.candidates.length) return;
    let popover = document.getElementById('sym-disambig-popover');
    if (!popover) {
      popover = document.createElement('div');
      popover.id = 'sym-disambig-popover';
      popover.className = 'sym-disambig-popover';
      popover.setAttribute('role', 'dialog');
      popover.setAttribute('aria-label', 'Choose UVM symbol class');
      document.body.appendChild(popover);

      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') closeSymbolDisambigPopover();
      });
      document.addEventListener('mousedown', function (ev) {
        if (popover.classList.contains('visible') && !popover.contains(ev.target) && !ev.target.closest('.clickable-uvm-sym, .wildcard-src-trigger')) {
          closeSymbolDisambigPopover();
        }
      });
      window.addEventListener('scroll', function (ev) {
        if (popover.classList.contains('visible') && ev.target && popover.contains(ev.target)) return;
        closeSymbolDisambigPopover();
      }, { passive: true, capture: true });
    }
    activeDisambigPopover = popover;

    const kindLabel = resolved.kind || resolved.type || 'method';
    const itemsHtml = resolved.candidates.map((cand, idx) => {
      const clsName = cand.class || 'Global';
      const qualified = (clsName === 'Global' || clsName === 'Globals')
        ? resolved.name
        : `${clsName}::${resolved.name}`;
      const retHtml = cand.ret ? `<span class="sdp-ret">${escapeHtml(cand.ret)}</span>` : '';
      const fileHtml = cand.file ? `<span class="sdp-loc">${escapeHtml(cand.file)}:${cand.line || 1}</span>` : '';
      return `
        <div class="sdp-item" data-cand-idx="${idx}">
          <button type="button" class="sdp-doc-btn" title="Open documentation for ${escapeHtml(qualified)}">
            <span class="sdp-name">${escapeHtml(qualified)}</span>
            ${retHtml}
            ${fileHtml}
          </button>
          ${cand.file ? `<button type="button" class="sdp-src-btn" title="Open source at ${escapeHtml(cand.file)}:${cand.line || 1}">Src</button>` : ''}
        </div>
      `;
    }).join('');

    popover.innerHTML = `
      <div class="sdp-header">
        <div class="sdp-title-wrap">
          <span class="sdp-badge">${escapeHtml(kindLabel)}</span>
          <span class="sdp-title">${escapeHtml(resolved.name)}</span>
          <span class="sdp-count">${resolved.candidates.length} classes</span>
        </div>
        <button type="button" class="sdp-close" aria-label="Close">&times;</button>
      </div>
      <div class="sdp-list">${itemsHtml}</div>
    `;

    popover.querySelector('.sdp-close').addEventListener('click', closeSymbolDisambigPopover);
    popover.querySelectorAll('.sdp-item').forEach((rowEl) => {
      const idx = parseInt(rowEl.getAttribute('data-cand-idx'), 10);
      const cand = resolved.candidates[idx];
      if (!cand) return;
      const docBtn = rowEl.querySelector('.sdp-doc-btn');
      if (docBtn) {
        docBtn.addEventListener('click', function () {
          closeSymbolDisambigPopover();
          if (resolved.preferSource && cand.file) {
            dispatchOpenSource('src_view/' + cand.file + '.html#L' + (cand.line || 1));
          } else {
            dispatchOpenDoc(cand.doc_url || undefined, resolved.name, cand.class || '');
          }
        });
      }
      const srcBtn = rowEl.querySelector('.sdp-src-btn');
      if (srcBtn && cand.file) {
        srcBtn.addEventListener('click', function (ev) {
          ev.stopPropagation();
          closeSymbolDisambigPopover();
          dispatchOpenSource('src_view/' + cand.file + '.html#L' + (cand.line || 1));
        });
      }
    });

    popover.classList.add('visible');
    const aRect = anchorEl.getBoundingClientRect();
    const pRect = popover.getBoundingClientRect();
    const vw = window.innerWidth || document.documentElement.clientWidth;
    const vh = window.innerHeight || document.documentElement.clientHeight;

    let top = aRect.bottom + 6;
    if (top + pRect.height > vh - 12 && aRect.top - pRect.height - 6 >= 12) {
      top = aRect.top - pRect.height - 6;
    }
    top = Math.max(10, Math.min(top, vh - pRect.height - 10));

    let left = aRect.left;
    if (left + pRect.width > vw - 12) {
      left = Math.max(10, vw - pRect.width - 12);
    }
    popover.style.top = top + 'px';
    popover.style.left = Math.max(10, left) + 'px';
  }

  function initLinks() {
    // Intercept clicks on links pointing to source code, example studios, or UVM symbols
    document.addEventListener('click', function (e) {
      // 1. Clickable UVM Symbols (spans in Code Studio or <a> badges in headers)
      const symEl = e.target.closest('.clickable-uvm-sym');
      if (symEl) {
        if (e.ctrlKey || e.metaKey) return;
        e.preventDefault();
        const sym = symEl.getAttribute('data-sym') || symEl.textContent.trim();
        const customUrl = symEl.getAttribute('data-doc') || symEl.getAttribute('data-url');
        const owner = symEl.getAttribute('data-sym-owner') || '';
        const base = symEl.getAttribute('data-sym-base') || '';
        const symKind = symEl.getAttribute('data-sym-kind') || '';
        if (customUrl) {
          dispatchOpenDoc(customUrl, sym, owner);
          return;
        }
        const resolved = lookupUvmSymbol(sym, owner, base, symKind);
        if (resolved && resolved.isAmbiguous) {
          showSymbolDisambigPopover(symEl, resolved);
        } else if (resolved) {
          dispatchOpenDoc(resolved.doc_url || undefined, sym, resolved.ownerClass || owner);
        } else if (sym) {
          dispatchOpenDoc(undefined, sym, owner);
        }
        return;
      }

      const link = e.target.closest('a');
      if (!link || link.closest('#doc-toc-nav')) return;

      const href = link.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript:')) return;

      // 1b. In-page hash links pointing to inherited items or collapsed zones
      if (href.startsWith('#') && href.length > 1) {
        const rawTarget = decodeURIComponent(href.replace(/^#/, ''));
        const inhMatch = findMatchingInheritedSection(rawTarget);
        let directTarget = null;
        try {
          directTarget = document.getElementById(rawTarget) || document.querySelector('[name="' + CSS.escape(rawTarget) + '"]');
        } catch (e) { }
        if (inhMatch || (directTarget && (directTarget.closest('.derived-classes-card.collapsed') || directTarget.closest('.hierarchy-subclasses-card.collapsed') || directTarget.closest('details:not([open])')))) {
          e.preventDefault();
          try {
            history.pushState(null, '', '#' + rawTarget);
          } catch (err) { }
          window.postMessage({ type: 'scrollToSection', anchor: rawTarget, id: rawTarget }, '*');
          return;
        }
      }

      // 2. Example Studio Callouts & Links
      if (link.classList.contains('example-callout-link') || href.includes('examples_view/')) {
        e.preventDefault();
        const exTarget = link.getAttribute('data-example-url') || link.getAttribute('href');
        const targetHref = new URL(exTarget, window.location.href).href;
        const backCtx = getCurrentBackContext();
        const fromTut = backCtx && backCtx.kind === 'tutorial' ? backCtx : null;
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ type: 'openExampleView', url: targetHref, fromTutorial: fromTut || undefined }, '*');
          return;
        }
        try {
          if (window.parent && window.parent.openExampleView) {
            window.parent.openExampleView(targetHref);
          }
        } catch (err) { }
        return;
      }

      // 2b. Tutorial Links
      const tutHrefAttr = link.getAttribute('data-tutorial-href');
      if (tutHrefAttr || link.classList.contains('tutorial-link') || href.includes('tutorial_view/')) {
        e.preventDefault();
        const relTut = tutHrefAttr || (href.match(/(tutorial_view\/.*)$/) ? href.match(/(tutorial_view\/.*)$/)[1] : '');
        if (relTut && window.parent && window.parent !== window) {
          window.parent.postMessage({ type: 'openTutorialView', url: relTut }, '*');
        } else {
          window.location.href = new URL(href, window.location.href).href;
        }
        return;
      }

      // 3. Source Code Links
      if (link.classList.contains('src-code-link') || href.includes('src_view/')) {
        if (link.classList.contains('wildcard-src-trigger') && !currentWildcardVariant) {
          e.preventDefault();
          e.stopPropagation();
          showWildcardDisambigPopover(link);
          return;
        }
        e.preventDefault();
        saveScrollAnchor();
        const targetHref = new URL(link.getAttribute('href'), window.location.href).href;
        if (window.parent && window.parent !== window) {
          dispatchOpenSource(targetHref);
        } else {
          window.location.href = targetHref;
        }
        return;
      }

      // 3b. Cross-doc links inside inherited blocks or explicit data-doc-href links
      const docHrefAttr = link.getAttribute('data-doc-href');
      if (docHrefAttr || (!link.classList.contains('doc-breadcrumb-link') && href.includes('docs_view/'))) {
        e.preventDefault();
        const relDoc = docHrefAttr || (href.match(/(docs_view\/.*)$/) ? href.match(/(docs_view\/.*)$/)[1] : '');
        if (relDoc && window.parent && window.parent !== window) {
          dispatchOpenDoc(relDoc);
        } else {
          window.location.href = new URL(href, window.location.href).href;
        }
        return;
      }

      // 4. Breadcrumb Navigation
      if (link.classList.contains('doc-breadcrumb-link')) {
        e.preventDefault();
        const rawHref = link.getAttribute('href') || '';
        if (rawHref.includes('#/tutorial')) {
          if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: 'switchSidebarTab', tab: 'tutorial' }, '*');
            return;
          }
        } else if (rawHref.includes('#/examples')) {
          if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: 'switchSidebarTab', tab: 'examples' }, '*');
            return;
          }
        }
        const docHref = link.getAttribute('data-doc-href') || 'docs_view/overviews/intro-txt.html';
        const cleanHashDoc = docHref.replace(/^docs_view\//, '');
        const fromCtx = getCurrentBackContext();
        if (window.parent && window.parent !== window) {
          if (fromCtx) {
            window.parent.postMessage({ type: 'openDocView', url: docHref, fromTutorial: fromCtx }, '*');
            return;
          }
          try {
            window.parent.location.hash = '#/doc/' + cleanHashDoc;
            return;
          } catch (err) { }
          window.parent.postMessage({ type: 'openDocView', url: docHref }, '*');
          return;
        }
        window.top.location.href = link.getAttribute('href');
      }
    });

    // Auto-restore into main app if opened directly outside iframe
    try {
      if (window.self === window.top) {
        const isExample = window.location.pathname.includes('examples_view/');
        const isTutorial = window.location.pathname.includes('tutorial_view/');
        const isSrc = window.location.pathname.includes('src_view/');
        const match = window.location.pathname.match(/(?:docs_view|examples_view|tutorial_view|src_view)\/(.*)$/);
        if (match) {
          const relPath = match[1];
          const depth = relPath.split('/').length;
          const rootRel = '../'.repeat(depth + 1);
          const routePrefix = isExample ? '#/example/' : (isTutorial ? '#/tutorial/' : (isSrc ? '#/src/' : '#/doc/'));
          window.location.replace(rootRel + 'index.html' + routePrefix + relPath + window.location.hash);
        }
      }
    } catch (e) { }

    // Notify parent when document/example/tutorial/source is loaded
    try {
      if (window.parent && window.parent !== window) {
        const isExample = window.location.pathname.includes('examples_view/');
        const isTutorial = window.location.pathname.includes('tutorial_view/');
        const isSrc = window.location.pathname.includes('src_view/');
        if (isExample) {
          const match = window.location.pathname.match(/(examples_view\/.*)$/);
          const exRel = match ? (match[1] + (window.location.hash || '')) : '';
          window.parent.postMessage({ type: 'exampleNavigated', url: exRel, title: document.title }, '*');
        } else if (isTutorial) {
          const match = window.location.pathname.match(/(tutorial_view\/.*)$/);
          const tutRel = match ? (match[1] + (window.location.hash || '')) : '';
          window.parent.postMessage({ type: 'tutorialNavigated', url: tutRel, title: document.title }, '*');
        } else if (isSrc) {
          const match = window.location.pathname.match(/(src_view\/.*)$/);
          const srcRel = match ? (match[1] + (window.location.hash || '')) : '';
          window.parent.postMessage({ type: 'srcNavigated', url: srcRel, title: document.title }, '*');
        } else {
          const match = window.location.pathname.match(/(docs_view\/.*)$/);
          const docRel = match ? (match[1] + (window.location.hash || '')) : '';
          window.parent.postMessage({ type: 'docNavigated', url: docRel, title: document.title }, '*');
        }
      }
    } catch (e) { }
  }

  // =========================================================================
  // Media Lightbox & Code Blocks
  // =========================================================================

  function serializeSvgToDataUrl(svgEl) {
    if (!svgEl) return '';
    const clone = svgEl.cloneNode(true);
    if (!clone.getAttribute('xmlns')) {
      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    }
    const rect = svgEl.getBoundingClientRect();
    const curW = clone.getAttribute('width');
    const curH = clone.getAttribute('height');
    const wNum = (!curW || curW.includes('%')) ? Math.round(rect.width) : parseFloat(curW);
    const hNum = (!curH || curH.includes('%')) ? Math.round(rect.height) : parseFloat(curH);
    if ((!curW || curW.includes('%')) && rect.width > 0) {
      clone.setAttribute('width', String(wNum));
    }
    if ((!curH || curH.includes('%')) && rect.height > 0) {
      clone.setAttribute('height', String(hNum));
    }
    if (!clone.getAttribute('viewBox') && wNum > 0 && hNum > 0) {
      clone.setAttribute('viewBox', `0 0 ${wNum} ${hNum}`);
    }
    clone.style.maxWidth = 'none';
    const xml = new XMLSerializer().serializeToString(clone);
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(xml);
  }

  function initDiagramZoom() {
    document.addEventListener('click', function (e) {
      const zoomBtn = e.target.closest('.doc-img-zoom-btn, .tut-svg-zoom-btn');
      const img = e.target.closest('.doc-diagram-img');
      const svgEl = e.target.closest('.tut-mermaid-wrap svg, .doc-diagram-card svg');
      if (zoomBtn || img || svgEl) {
        e.preventDefault();
        e.stopPropagation();
        const card = (zoomBtn || img || svgEl).closest('.doc-diagram-card, .tut-mermaid-wrap');
        const targetImg = card ? card.querySelector('.doc-diagram-img') : img;
        const targetSvg = card ? card.querySelector('svg:not(.zoom-icon)') : svgEl;
        let fullSrc = '';
        let title = 'UVM Diagram';

        if (targetImg && targetImg.src) {
          fullSrc = targetImg.src;
          const titleEl = card ? card.querySelector('.doc-diagram-caption, .doc-diagram-label span') : null;
          title = titleEl ? titleEl.textContent.trim() : (targetImg.alt || 'UVM Diagram');
        } else if (targetSvg) {
          fullSrc = serializeSvgToDataUrl(targetSvg);
          const topic = targetSvg.closest('.CTopic');
          const headingEl = topic ? topic.querySelector('.CTitle') : null;
          title = (targetSvg.getAttribute('aria-label') || (headingEl ? headingEl.textContent.trim() : '') || 'Diagram');
        }

        if (fullSrc) {
          if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: 'openImageModal', src: fullSrc, title: title }, '*');
          } else {
            window.open(fullSrc, '_blank');
          }
        }
      }
    });

    window.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && window.parent && window.parent !== window) {
        window.parent.postMessage({ type: 'closeImageModal' }, '*');
      }
    });
  }

  function initCodeBlocks() {
    const checkSvg = '<svg class="copy-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>';
    document.addEventListener('click', function (e) {
      const btn = e.target.closest('.code-copy-btn');
      if (!btn) return;
      const container = btn.closest('.code-block-container');
      if (!container) return;
      const codeEl = container.querySelector('code');
      if (!codeEl) return;
      const text = codeEl.innerText || codeEl.textContent;
      copyText(text).then(function () {
        const copyTextSpan = btn.querySelector('.copy-text');
        if (copyTextSpan) {
          const orig = copyTextSpan.textContent;
          btn.classList.add('copied');
          copyTextSpan.textContent = 'Copied!';
          setTimeout(function () {
            btn.classList.remove('copied');
            copyTextSpan.textContent = orig;
          }, 2000);
        } else {
          if (!btn.dataset.origHtml) btn.dataset.origHtml = btn.innerHTML;
          const origTitle = btn.getAttribute('title') || 'Copy code';
          btn.classList.add('copied');
          btn.innerHTML = checkSvg;
          btn.setAttribute('title', 'Copied!');
          setTimeout(function () {
            btn.classList.remove('copied');
            if (btn.dataset.origHtml) btn.innerHTML = btn.dataset.origHtml;
            btn.setAttribute('title', origTitle);
          }, 2000);
        }
      });
    });
  }

  // =========================================================================
  // Wildcard Variant Selector & Disambiguation (TLM1 uvm_*_port/export/imp)
  // =========================================================================

  let currentWildcardVariant = '';
  let wildcardManifest = null;

  function showWildcardDisambigPopover(anchorEl) {
    if (!wildcardManifest || !wildcardManifest.variants) return;
    const grp = anchorEl.getAttribute('data-wildcard-group') || '';
    const member = anchorEl.getAttribute('data-wildcard-member') || '';
    const list = grp
      ? wildcardManifest.variants.filter(v => v.group === grp)
      : wildcardManifest.variants;
    const candidates = (list.length ? list : wildcardManifest.variants).map(v => ({
      class: v.name,
      file: v.file,
      line: v.line,
      ret: v.params ? `#(${v.params})` : '',
      doc_url: `docs_view/${wildcardManifest.page}#${v.docTopic}`
    }));
    showSymbolDisambigPopover(anchorEl, {
      name: member ? `${wildcardManifest.pattern}::${member}` : wildcardManifest.pattern,
      kind: member ? 'method' : 'class',
      preferSource: true,
      candidates: candidates
    });
  }

  function replaceAllWildcardPatterns(text, variant, pattern) {
    if (!text || !variant) return text;
    const m = variant.name.match(/^uvm_(.+)_(port|export|imp)$/);
    if (!m) return text.split(pattern).join(variant.name);
    const stem = m[1];
    return text
      .split('uvm_*_port').join(`uvm_${stem}_port`)
      .split('uvm_*_export').join(`uvm_${stem}_export`)
      .split('uvm_*_imp').join(`uvm_${stem}_imp`);
  }

  function collectWildcardTextNodes(rootEl) {
    const nodes = [];
    if (!rootEl) return nodes;
    const walker = document.createTreeWalker(rootEl, NodeFilter.SHOW_TEXT, null);
    let node;
    while ((node = walker.nextNode())) {
      if (node.parentElement && node.parentElement.closest('#wildcard-selector-bar, #wildcard-variant-select, script, style')) continue;
      if (node.__wildcardOrig !== undefined || (node.nodeValue && /uvm_\*_(?:port|export|imp)/.test(node.nodeValue))) {
        if (node.__wildcardOrig === undefined) {
          node.__wildcardOrig = node.nodeValue;
        }
        nodes.push(node);
      }
    }
    return nodes;
  }

  function applyWildcardVariant(variantName, savePref) {
    if (!wildcardManifest) return;
    const pattern = wildcardManifest.pattern;
    const variant = wildcardManifest.variants.find(v => v.name === variantName) || null;
    currentWildcardVariant = variant ? variant.name : '';

    const selectEl = document.getElementById('wildcard-variant-select');
    if (selectEl && selectEl.value !== currentWildcardVariant) {
      selectEl.value = currentWildcardVariant;
    }
    const pageSelectEl = document.getElementById('wildcard-page-variant-select');
    if (pageSelectEl && pageSelectEl.value !== currentWildcardVariant) {
      pageSelectEl.value = currentWildcardVariant;
    }

    const contentEl = document.getElementById('Content');
    const hiddenTopicIds = new Set();
    if (contentEl) {
      const classEls = Array.from(contentEl.querySelectorAll(':scope > .CClass'));
      classEls.forEach(cEl => {
        const shouldHide = Boolean(variant && variant.docTopic && cEl.id !== variant.docTopic);
        let cur = cEl;
        while (cur && (cur === cEl || !cur.classList.contains('CClass'))) {
          if (shouldHide) {
            cur.classList.add('wildcard-group-hidden');
            if (cur.id) hiddenTopicIds.add(cur.id);
            cur.querySelectorAll('[id]').forEach(desc => {
              if (desc.id) hiddenTopicIds.add(desc.id);
            });
          } else {
            cur.classList.remove('wildcard-group-hidden');
          }
          cur = cur.nextElementSibling;
        }
      });
    }

    const roots = [contentEl, document.getElementById('doc-toc-sidebar'), document.querySelector('.doc-breadcrumbs')];
    if (document.title && (window.__wildcardOrigDocTitle !== undefined || /uvm_\*_(?:port|export|imp)/.test(document.title))) {
      if (window.__wildcardOrigDocTitle === undefined) window.__wildcardOrigDocTitle = document.title;
      document.title = variant
        ? replaceAllWildcardPatterns(window.__wildcardOrigDocTitle, variant, pattern)
        : window.__wildcardOrigDocTitle;
    }
    roots.forEach(r => {
      collectWildcardTextNodes(r).forEach(node => {
        node.nodeValue = variant
          ? replaceAllWildcardPatterns(node.__wildcardOrig, variant, pattern)
          : node.__wildcardOrig;
      });
    });

    if (contentEl) {
      contentEl.querySelectorAll('.CBody > p').forEach(p => {
        if (p.classList.contains('wildcard-resolved-iface')) return;
        const txt = (p.textContent || '').toLowerCase();
        const nextEl = p.nextElementSibling;
        if (txt.includes('asterisk') && nextEl && nextEl.classList.contains('code-block-container')) {
          let resolvedEl = nextEl.nextElementSibling;
          if (!resolvedEl || !resolvedEl.classList.contains('wildcard-resolved-iface')) {
            resolvedEl = document.createElement('p');
            resolvedEl.className = 'wildcard-resolved-iface wildcard-group-hidden';
            nextEl.parentNode.insertBefore(resolvedEl, nextEl.nextSibling);
          }
          if (variant) {
            const m = variant.name.match(/^uvm_(.+)_(port|export|imp)$/);
            const stem = m ? m[1] : variant.name;
            p.classList.add('wildcard-group-hidden');
            nextEl.classList.add('wildcard-group-hidden');
            resolvedEl.innerHTML = `Interface type: <code>${escapeHtml(stem)}</code> (resolved for <code>${escapeHtml(variant.name)}</code>).`;
            resolvedEl.classList.remove('wildcard-group-hidden');
          } else {
            p.classList.remove('wildcard-group-hidden');
            nextEl.classList.remove('wildcard-group-hidden');
            resolvedEl.classList.add('wildcard-group-hidden');
          }
        }
      });
      contentEl.querySelectorAll('a[href*="uvm_*_"]:not(.wildcard-src-trigger)').forEach(a => {
        if (a.dataset.wildcardOrigHref === undefined) {
          a.dataset.wildcardOrigHref = a.getAttribute('href') || '';
        }
        if (variant) {
          const m = variant.name.match(/^uvm_(.+)_(port|export|imp)$/);
          const stem = m ? m[1] : '';
          a.setAttribute('href', stem
            ? a.dataset.wildcardOrigHref.replace(/uvm_\*_(port|export|imp)(?:#\([^)]*\))?/, `uvm_${stem}_$1`)
            : a.dataset.wildcardOrigHref);
        } else {
          a.setAttribute('href', a.dataset.wildcardOrigHref);
        }
      });
    }

    if (contentEl) {
      contentEl.querySelectorAll('.ContentsSummary tr.SSMethod').forEach(tr => {
        const link = tr.querySelector('a[data-target-id], a[href^="#"]');
        const tid = link ? (link.getAttribute('data-target-id') || '').replace(/^#/, '') : '';
        const targetEl = tid ? contentEl.querySelector(`[data-anchor="${CSS.escape(tid)}"]`) : null;
        if (variant && targetEl && targetEl.classList.contains('wildcard-group-hidden')) {
          tr.classList.add('wildcard-group-hidden');
        } else {
          tr.classList.remove('wildcard-group-hidden');
        }
      });
    }

    const tocSidebar = document.getElementById('doc-toc-sidebar');
    if (tocSidebar) {
      tocSidebar.querySelectorAll('.doc-toc-group-block, .doc-toc-item').forEach(el => {
        const link = el.querySelector(':scope > .doc-toc-link, :scope > .doc-toc-group-header > .doc-toc-link');
        const tid = link ? link.getAttribute('data-target-id') : '';
        if (tid && hiddenTopicIds.has(tid)) {
          el.classList.add('wildcard-group-hidden');
        } else {
          el.classList.remove('wildcard-group-hidden');
        }
      });
      tocSidebar.querySelectorAll('a.doc-toc-link[title]').forEach(a => {
        if (a.dataset.wildcardOrigTitle === undefined) {
          const t = a.getAttribute('title') || '';
          if (t.indexOf(pattern) !== -1) {
            a.dataset.wildcardOrigTitle = t;
          }
        }
        if (a.dataset.wildcardOrigTitle !== undefined) {
          a.setAttribute('title', variant
            ? replaceAllWildcardPatterns(a.dataset.wildcardOrigTitle, variant, pattern)
            : a.dataset.wildcardOrigTitle);
        }
      });
      const mobileCurr = document.getElementById('doc-toc-mobile-current');
      if (mobileCurr && mobileCurr.dataset.wildcardOrig) {
        mobileCurr.textContent = variant
          ? replaceAllWildcardPatterns(mobileCurr.dataset.wildcardOrig, variant, pattern)
          : mobileCurr.dataset.wildcardOrig;
      }
    }

    document.querySelectorAll('a.wildcard-src-trigger').forEach(link => {
      if (!link.dataset.origHref) {
        link.dataset.origHref = link.getAttribute('href') || '';
        link.dataset.origSrcLine = link.getAttribute('data-src-line') || '1';
      }
      if (variant) {
        const prefix = link.dataset.origHref.split('src_view/')[0] || '';
        link.setAttribute('href', `${prefix}src_view/${variant.file}.html#L${variant.line}`);
        link.setAttribute('data-src-line', String(variant.line));
        link.setAttribute('title', `Open ${variant.name} source at line ${variant.line}`);
      } else {
        link.setAttribute('href', link.dataset.origHref);
        link.setAttribute('data-src-line', link.dataset.origSrcLine);
        link.removeAttribute('title');
      }
    });

    const hintEl = document.getElementById('wildcard-hint');
    if (hintEl) {
      hintEl.textContent = variant
        ? `Showing ${variant.name} (${variant.file}:${variant.line}) — links open this class directly`
        : 'All variants shown — click any source link to choose implementation';
    }

    if (savePref) {
      try {
        const nextUrl = currentWildcardVariant
          ? '#' + encodeURIComponent(currentWildcardVariant)
          : window.location.pathname + window.location.search;
        if (window.history && window.history.replaceState) {
          window.history.replaceState(null, '', nextUrl);
        }
      } catch (e) { }
      if (window.parent && window.parent !== window) {
        try {
          window.parent.postMessage({
            type: 'wildcardVariantChanged',
            docRel: wildcardManifest.page,
            variant: currentWildcardVariant
          }, '*');
        } catch (e) { }
      }
    }
  }

  function resolveWildcardCopyAnchor(anchor, isPageLink) {
    if (!wildcardManifest || !currentWildcardVariant) {
      return isPageLink ? '' : anchor;
    }
    if (isPageLink) return currentWildcardVariant;
    if (anchor && anchor.indexOf(wildcardManifest.pattern) !== -1) {
      const escaped = wildcardManifest.pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return anchor.replace(new RegExp(escaped + '(?:#\\([^)]*\\))?'), currentWildcardVariant);
    }
    return anchor;
  }

  function resolveWildcardTarget(rawTarget) {
    if (!wildcardManifest || !wildcardManifest.variants || !rawTarget) return null;
    if (wildcardManifest.pattern && rawTarget.indexOf(wildcardManifest.pattern) === 0) {
      let resolvedId = 'doc-nav-main';
      try {
        const exactEl = document.querySelector(`[data-anchor="${CSS.escape(rawTarget)}"]`);
        if (exactEl && exactEl.id) {
          resolvedId = exactEl.id;
        } else {
          const wantReqRsp = rawTarget.indexOf('REQ') !== -1 && rawTarget.indexOf('RSP') !== -1;
          const matchVar = wildcardManifest.variants.find(item => wantReqRsp ? item.group === 'REQ_RSP' : item.group === 'T') || wildcardManifest.variants[0];
          if (matchVar && matchVar.docTopic) resolvedId = matchVar.docTopic;
        }
      } catch (e) { }
      return { variant: null, suffix: '', resolvedId: resolvedId };
    }
    const dotIdx = rawTarget.indexOf('.');
    const base = dotIdx !== -1 ? rawTarget.slice(0, dotIdx) : rawTarget;
    const suffix = dotIdx !== -1 ? rawTarget.slice(dotIdx + 1) : '';
    const v = wildcardManifest.variants.find(item => item.name === base);
    if (!v) return null;
    let resolvedId = v.docTopic || 'doc-nav-main';
    if (suffix && v.docTopic) {
      const topicEl = document.getElementById(v.docTopic);
      const classAnchor = topicEl ? topicEl.getAttribute('data-anchor') : '';
      if (classAnchor) {
        try {
          const memberEl = document.querySelector(`[data-anchor="${CSS.escape(classAnchor + '.' + suffix)}"]`);
          if (memberEl && memberEl.id) resolvedId = memberEl.id;
        } catch (e) { }
      }
    }
    return { variant: v, suffix: suffix, resolvedId: resolvedId };
  }

  function syncWildcardFromHash() {
    if (!wildcardManifest) return;
    const rawHash = decodeURIComponent((window.location.hash || '').replace(/^#/, ''));
    if (!rawHash) return;
    const wResolved = resolveWildcardTarget(rawHash);
    if (wResolved) {
      applyWildcardVariant(wResolved.variant ? wResolved.variant.name : '', false);
      if (wResolved.resolvedId) {
        window.postMessage({ type: 'scrollToSection', anchor: wResolved.resolvedId, id: wResolved.resolvedId }, '*');
      }
    }
  }

  function initWildcardVariantController() {
    const manifestEl = document.getElementById('uvm-wildcard-variants');
    const selectEl = document.getElementById('wildcard-variant-select');
    const pageSelectEl = document.getElementById('wildcard-page-variant-select');
    if (!manifestEl || (!selectEl && !pageSelectEl)) return;
    try {
      wildcardManifest = JSON.parse(manifestEl.textContent);
    } catch (e) {
      return;
    }

    if (selectEl) {
      selectEl.addEventListener('change', function () {
        applyWildcardVariant(selectEl.value, true);
      });
    }
    if (pageSelectEl) {
      pageSelectEl.addEventListener('change', function () {
        applyWildcardVariant(pageSelectEl.value, true);
      });
    }

    const rawHash = decodeURIComponent((window.location.hash || '').replace(/^#/, ''));
    const hashResolved = rawHash ? resolveWildcardTarget(rawHash) : null;
    if (hashResolved) {
      applyWildcardVariant(hashResolved.variant ? hashResolved.variant.name : '', false);
    } else {
      applyWildcardVariant('', false);
    }

    window.addEventListener('hashchange', syncWildcardFromHash);
  }

  // =========================================================================
  // Universal Initializer (Executes for any page type on DOMContentLoaded)
  // =========================================================================

  let currentStudioController = null;

  function initAll() {
    initTheme();
    initLinks();
    initCodeBlocks();
    initDiagramZoom();
    initBreadcrumbs();
    initScrollAnchor();

    if (document.getElementById('doc-toc-sidebar')) {
      initTOC();
    }
    initWildcardVariantController();
    if (document.querySelector('.CTitle, .STitle, .IHeading')) {
      initHeadingAnchors();
    }

    const studio = initCodeStudio();
    currentStudioController = studio;

    // Source Notes File Badge click -> switch file in Code Studio
    const notesBadge = document.querySelector('.notes-file-badge');
    if (notesBadge && studio) {
      notesBadge.addEventListener('click', function () {
        const targetFile = notesBadge.getAttribute('data-file');
        if (targetFile) {
          studio.switchFile(targetFile);
          const studioEl = document.getElementById('doc-nav-studio') ||
            document.getElementById('doc-nav-code') ||
            document.querySelector('.studio-section') ||
            document.querySelector('.code-studio-section');
          if (studioEl) {
            studioEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      });
    }

    // Immediate check for hash navigation to retracted zones or anchors on load
    try {
      const curHash = (window.location.hash || '').replace(/^#/, '');
      if (curHash) {
        const decHash = decodeURIComponent(curHash);
        const inhMatch = findMatchingInheritedSection(decHash);
        if (inhMatch && typeof inhMatch._ensureExpandedAndRendered === 'function') {
          inhMatch._ensureExpandedAndRendered(function () {
            window.postMessage({ type: 'scrollToSection', anchor: decHash, id: decHash }, '*');
          });
        } else {
          let directTarget = null;
          try {
            directTarget = document.getElementById(decHash) || document.querySelector('[name="' + CSS.escape(decHash) + '"]');
          } catch (e) { }
          if (directTarget) {
            expandAllRetractedAncestors(directTarget);
          }
        }
      }
    } catch (e) { }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  return {
    clipboard: { copyText: copyText, bindCopyFeedback: bindCopyFeedback },
    escapeHtml: escapeHtml,
    getUvmSymbols: getUvmSymbols,
    ensureUvmSymbolsLoaded: ensureUvmSymbolsLoaded,
    initTheme: initTheme,
    initTOC: initTOC,
    initHeadingAnchors: initHeadingAnchors,
    initCodeStudio: initCodeStudio,
    getStudioController: function () { return currentStudioController; },
    initLinks: initLinks,
    initScrollAnchor: initScrollAnchor,
    saveScrollAnchor: saveScrollAnchor,
    restoreScrollAnchor: restoreScrollAnchor,
    expandAllRetractedAncestors: expandAllRetractedAncestors,
    findMatchingInheritedSection: findMatchingInheritedSection,
    retryPendingSectionScroll: retryPendingSectionScroll,
    initAll: initAll
  };
})();

