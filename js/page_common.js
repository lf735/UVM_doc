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
  // Table of Contents (TOC) & ScrollSpy
  // =========================================================================

  function initTOC() {
    const contentEl = document.getElementById('Content');
    const tocSidebar = document.getElementById('doc-toc-sidebar');
    const tocNav = document.getElementById('doc-toc-nav');
    const toggleAllBtn = document.getElementById('doc-toc-toggle-all');
    if (!contentEl || !tocSidebar || !tocNav) return;

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
        mainTitleEl.id = safeId;
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
        topSummaryEl.setAttribute('data-anchor', safeAnchor);
        tocEntries.push({
          kind: 'item',
          data: {
            id: topSummaryEl.id,
            anchor: safeAnchor,
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
    const topicWrappers = contentEl.querySelectorAll('#Content > div');

    topicWrappers.forEach(function (wrap) {
      if (wrap.id === 'doc-nav-main' || wrap.querySelector('#MainTopic')) return;

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
          classSummary.setAttribute('data-anchor', classSummary.getAttribute('data-anchor') || 'Summary');
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
        tocHtml += '<li class="doc-toc-item' + typeCls + isMono + '">';
        tocHtml += '<a href="#' + item.id + '" data-target-id="' + item.id + '"' + itemAnchorAttr + ' class="doc-toc-link" title="' + cleanTitle + '">';
        tocHtml += cleanTitle;
        tocHtml += '</a></li>';
        return;
      }

      const group = entry.data;
      const cleanGroupTitle = group.title.replace(/"/g, '&quot;');
      const hasSubItems = group.items.length > 0;
      const defaultCollapsedCls = (hasSubItems && group.isInheritedGroup) ? ' collapsed' : '';
      const groupAnchorAttr = group.anchor ? ' data-anchor="' + escapeHtml(group.anchor) + '"' : '';
      tocHtml += '<li class="doc-toc-item doc-toc-group-item doc-toc-group-block' + (hasSubItems ? '' : ' no-children') + defaultCollapsedCls + '" id="block-' + group.id + '">';
      tocHtml += '<div class="doc-toc-group-header">';
      if (hasSubItems) {
        tocHtml += '<button class="doc-toc-chevron-btn" type="button" aria-label="Toggle group ' + cleanGroupTitle + '" title="Toggle group">';
        tocHtml += '<svg class="doc-toc-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
        tocHtml += '</button>';
      } else {
        tocHtml += '<span class="doc-toc-dot-indicator"></span>';
      }
      tocHtml += '<a href="#' + group.id + '" data-target-id="' + group.id + '"' + groupAnchorAttr + ' class="doc-toc-link doc-toc-group-title" title="' + cleanGroupTitle + '">';
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
          tocHtml += '<li class="doc-toc-item doc-toc-subitem' + extraCls + '">';
          tocHtml += '<a href="#' + sub.id + '" data-target-id="' + sub.id + '"' + inhAttr + anchorAttr + ' class="doc-toc-link' + (sub.isGroupHeader ? ' doc-toc-subgroup-link' : '') + '" title="' + cleanSubTitle + '">';
          tocHtml += cleanSubTitle;
          tocHtml += '</a></li>';
        });
        tocHtml += '</ul>';
      }
      tocHtml += '</li>';
    });

    tocHtml += '</ul>';
    tocNav.innerHTML = tocHtml;

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

    function onManualScrollDone() {
      isManualScrolling = false;
      pendingTargetEl = null;
      updateScrollSpy();
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
      return Math.max(0, currentScroll + rect.top - 24);
    }

    function performScroll(targetY) {
      const scrollEl = document.scrollingElement || document.documentElement || document.body;
      try {
        window.scrollTo({ top: targetY, behavior: 'smooth' });
      } catch (e) {
        window.scrollTo(0, targetY);
      }
      if (scrollEl && Math.abs(scrollEl.scrollTop - targetY) > 5) {
        try {
          scrollEl.scrollTo({ top: targetY, behavior: 'smooth' });
        } catch (e) {
          scrollEl.scrollTop = targetY;
        }
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
      const rect = targetEl.getBoundingClientRect();
      if (Math.abs(rect.top - 24) > 6) {
        const adjustedY = getTargetScrollY(targetEl);
        performScroll(adjustedY);
        pendingTargetEl = null;
        setTimeout(onManualScrollDone, 100);
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
      tocSidebar.addEventListener('wheel', function () { lastTocUserInteract = Date.now(); }, { passive: true });
      tocSidebar.addEventListener('touchmove', function () { lastTocUserInteract = Date.now(); }, { passive: true });
    }

    function scrollTocToItem(linkEl, opts) {
      if (!linkEl || !tocSidebar) return;
      if (linkEl.offsetParent === null) return;
      const options = opts || {};
      if (!options.force && (Date.now() - lastTocUserInteract < 1500 || tocSidebar.matches(':hover'))) {
        return;
      }
      const sidebarRect = tocSidebar.getBoundingClientRect();
      const linkRect = linkEl.getBoundingClientRect();
      if (linkRect.height === 0 || sidebarRect.height === 0) return;

      const pad = 16;
      const isAbove = linkRect.top < sidebarRect.top + pad;
      const isBelow = linkRect.bottom > sidebarRect.bottom - pad;
      if (!isAbove && !isBelow) return;

      const currentScroll = tocSidebar.scrollTop;
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
          tocSidebar.scrollTo({ top: targetOffset, behavior: 'smooth' });
        } catch (e) {
          tocSidebar.scrollTop = targetOffset;
        }
      } else {
        tocSidebar.scrollTop = targetOffset;
      }
    }

    function resolveScrollContainer(el) {
      if (!el || !el.closest) return el;
      if (el.classList && el.classList.contains('inherited-methods-section')) return el;
      const inhEntry = el.closest('.inherited-topic-entry');
      if (inhEntry) return inhEntry;
      const inhSec = el.closest('.inherited-methods-section');
      if (inhSec) return inhSec;
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

      let activeItem = null;
      for (let i = 0; i < allNavItems.length; i++) {
        const item = allNavItems[i];
        const el = item.el || document.getElementById(item.id);
        if (!el || el.offsetParent === null) continue;
        const rect = el.getBoundingClientRect();
        if (rect.top <= 100) {
          activeItem = item;
        }
      }

      if (!activeItem && allNavItems.length > 0) {
        activeItem = allNavItems[0];
      }

      if (activeItem && activeItem.link) {
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
          const anchor = data.anchor;
          const targetId = data.id || anchor;
          const navToken = data.navToken;

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
    setTimeout(updateScrollSpy, 120);
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

    for (let i = 0; i < headings.length; i++) {
      const el = headings[i];
      const rect = el.getBoundingClientRect();
      if (rect.top >= -40 && rect.top <= viewportHeight * 0.6) {
        const dist = Math.abs(rect.top - 24);
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
      const anchor = getHeadingAnchor(heading);
      if (!anchor) return;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'heading-anchor-btn';
      btn.setAttribute('aria-label', 'Copy link to this section');
      btn.setAttribute('title', 'Copy link to this section');
      btn.setAttribute('data-anchor', anchor);
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

      const anchor = btn.getAttribute('data-anchor');
      if (!anchor) return;

      const hash = '#' + anchor;
      try {
        history.pushState(null, '', hash);
      } catch (err) {
        window.location.hash = hash;
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
            try { window.parent.location.hash = `#/example/${exClean}${hash}`; } catch (err) { }
            window.parent.postMessage({ type: 'exampleNavigated', url: exRel + hash }, '*');
          } else {
            fullUrl = `${parentBase}#/doc/${docRel}${hash}`;
            try { window.parent.location.hash = `#/doc/${docRel}${hash}`; } catch (err) { }
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

    if (!studioTabBar && !codePanes.length && !document.querySelector('.sv-code-table')) return;

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
      if (idx < 0 || idx >= codePanes.length) return;
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

      if (studioTabs[idx]) {
        try {
          studioTabs[idx].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
        } catch (e) {
          studioTabs[idx].scrollIntoView(false);
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
    function scrollToLine(lineHashOrNum) {
      if (!lineHashOrNum) return;
      const lineStr = String(lineHashOrNum).replace(/^#?L?/, '');
      const selector = `#L${lineStr}`;
      const targetRow = document.querySelector(`.file-code-pane tr${selector}`) ||
        document.querySelector(`.sv-code-table tr${selector}`) ||
        document.getElementById(`L${lineStr}`);
      if (targetRow) {
        document.querySelectorAll('.file-code-pane tr.active-line, .sv-code-table tr.active-line').forEach(function (tr) {
          tr.classList.remove('active-line');
        });
        void targetRow.offsetWidth;
        targetRow.classList.add('active-line');

        const container = studioCodeContainer || document.getElementById('src-code-container') || document.querySelector('.code-container');
        if (container && container.scrollHeight > container.clientHeight && getComputedStyle(container).overflowY !== 'visible') {
          const cRect = container.getBoundingClientRect();
          const rRect = targetRow.getBoundingClientRect();
          const offsetTop = rRect.top - cRect.top + container.scrollTop;
          const targetScroll = Math.max(0, offsetTop - (container.clientHeight / 2));
          container.scrollTo({ top: targetScroll, left: 0, behavior: 'smooth' });
        } else {
          targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
      const findCase = document.getElementById('find-case');
      const findWord = document.getElementById('find-word');
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
            for (let i = 0; i < rows.length; i++) {
              const text = rows[i].querySelector('.code') ? rows[i].querySelector('.code').textContent : '';
              const declRegex = new RegExp('(?:class|function|task|typedef)\\s+(?:\\w+\\s+)?' + cleanToken + '\\b|`define\\s+' + cleanToken + '\\b');
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

    // 5. Monaco Editor Dynamic Loader
    let monacoEditorInstance = null;
    let isMonacoActive = false;
    (function initMonacoLoader() {
      const btnToggleMonaco = document.getElementById('btn-toggle-monaco');
      const monacoPane = document.getElementById('monaco-editor-pane');
      if (!btnToggleMonaco || !monacoPane) return;

      function loadMonacoScript(onSuccess, onError) {
        if (window.monaco) {
          onSuccess();
          return;
        }
        if (window.require && window.require.config) {
          window.require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
          window.require(['vs/editor/editor.main'], function () { onSuccess(); });
          return;
        }
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js';
        script.onload = function () {
          window.require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
          window.require(['vs/editor/editor.main'], function () { onSuccess(); });
        };
        script.onerror = onError || function () { };
        document.head.appendChild(script);
      }

      function setupMonacoLanguageProviders() {
        if (window.__monacoProvidersRegistered || !window.monaco || !getUvmSymbols()) return;
        window.__monacoProvidersRegistered = true;

        monaco.languages.registerHoverProvider('systemverilog', {
          provideHover: function (model, position) {
            const word = model.getWordAtPosition(position);
            if (!word) return null;
            const clean = word.word.replace(/^`/, '');
            const resolved = lookupUvmSymbol(clean);
            const sym = resolved ? (resolved.isAmbiguous ? resolved.primary : resolved) : null;
            if (!sym) return null;
            const contents = [
              { value: `**[${(sym.type || 'symbol').toUpperCase()}]** \`${sym.ownerClass ? sym.ownerClass + '::' : ''}${clean}\`` },
              { value: `*Source:* \`${sym.file}:${sym.line || 1}\`` }
            ];
            if (sym.doc) contents.push({ value: sym.doc });
            return {
              range: new monaco.Range(position.lineNumber, word.startColumn, position.lineNumber, word.endColumn),
              contents: contents
            };
          }
        });

        monaco.languages.registerDefinitionProvider('systemverilog', {
          provideDefinition: function (model, position) {
            const word = model.getWordAtPosition(position);
            if (!word) return null;
            const clean = word.word.replace(/^`/, '');
            const resolved = lookupUvmSymbol(clean);
            const sym = resolved ? (resolved.isAmbiguous ? resolved.primary : resolved) : null;
            if (!sym) return null;
            if (sym.file && !window.location.pathname.includes(sym.file)) {
              dispatchOpenSource(`src_view/${sym.file}.html#L${sym.line || 1}`);
            }
            return {
              uri: model.uri,
              range: new monaco.Range(sym.line || 1, 1, sym.line || 1, 1)
            };
          }
        });
      }

      function getMonacoTheme() {
        const curTheme = document.documentElement.getAttribute('data-theme') || 'light';
        return (curTheme === 'dark' || curTheme === 'night') ? 'vs-dark' : 'vs';
      }

      const VSCODE_ICON_SVG = '<svg class="monaco-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .326 8.74L3.899 12 .326 15.26a1 1 0 0 0 .001 1.479L1.65 17.94a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352zM18 17.5l-6-5.5 6-5.5v11z"/></svg>';
      const CLOSE_ICON_SVG = '<svg class="monaco-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

      function activateMonaco() {
        btnToggleMonaco.innerHTML = VSCODE_ICON_SVG + ' <span>Loading Monaco...</span>';

        const prevHeight = studioCodeContainer ? studioCodeContainer.offsetHeight : 0;
        const targetHeight = Math.max(prevHeight, 520);

        if (studioCodeContainer) {
          studioCodeContainer.classList.add('monaco-active');
          if (studioCodeContainer.classList.contains('studio-code-container')) {
            studioCodeContainer.style.height = targetHeight + 'px';
          }
        }

        loadMonacoScript(function () {
          setupMonacoLanguageProviders();
          const codeText = getActiveCodeText();
          const themeName = getMonacoTheme();

          codePanes.forEach(function (p) { p.style.display = 'none'; });
          const svTable = document.querySelector('.sv-code-table');
          if (svTable) svTable.style.display = 'none';

          monacoPane.style.display = 'block';
          monacoPane.classList.add('active');

          if (!monacoEditorInstance) {
            monacoEditorInstance = monaco.editor.create(monacoPane, {
              value: codeText,
              language: 'systemverilog',
              theme: themeName,
              readOnly: true,
              lineNumbers: 'on',
              renderWhitespace: 'none',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              fontFamily: 'Consolas, "Cascadia Mono", monospace',
              fontSize: 13,
              minimap: { enabled: true }
            });
          } else {
            monacoEditorInstance.setValue(codeText);
            monaco.editor.setTheme(themeName);
          }

          requestAnimationFrame(function () {
            if (monacoEditorInstance) {
              monacoEditorInstance.layout();
            }
          });
          setTimeout(function () {
            if (monacoEditorInstance) {
              monacoEditorInstance.layout();
            }
          }, 80);

          const hash = window.location.hash;
          if (hash && hash.startsWith('#L')) {
            const lineNum = parseInt(hash.replace('#L', ''), 10);
            if (!isNaN(lineNum)) {
              monacoEditorInstance.revealLineInCenter(lineNum);
              monacoEditorInstance.setPosition({ lineNumber: lineNum, column: 1 });
            }
          }

          isMonacoActive = true;
          btnToggleMonaco.innerHTML = CLOSE_ICON_SVG + ' <span>Standard View</span>';
          btnToggleMonaco.classList.add('active');
        }, function () {
          btnToggleMonaco.innerHTML = VSCODE_ICON_SVG + ' <span>Monaco Error</span>';
          if (studioCodeContainer) {
            studioCodeContainer.classList.remove('monaco-active');
            if (studioCodeContainer.classList.contains('studio-code-container')) {
              studioCodeContainer.style.height = '';
            }
          }
          setTimeout(function () {
            btnToggleMonaco.innerHTML = VSCODE_ICON_SVG + ' <span>Monaco IDE</span>';
          }, 3000);
        });
      }

      function deactivateMonaco() {
        monacoPane.style.display = 'none';
        monacoPane.classList.remove('active');

        if (studioCodeContainer) {
          studioCodeContainer.classList.remove('monaco-active');
          if (studioCodeContainer.classList.contains('studio-code-container')) {
            studioCodeContainer.style.height = '';
          }
        }

        codePanes.forEach(function (p, idx) {
          p.style.display = (idx === currentFileIdx) ? '' : 'none';
        });
        const svTable = document.querySelector('.sv-code-table');
        if (svTable) svTable.style.display = '';
        isMonacoActive = false;
        btnToggleMonaco.innerHTML = VSCODE_ICON_SVG + ' <span>Monaco IDE</span>';
        btnToggleMonaco.classList.remove('active');
      }

      btnToggleMonaco.addEventListener('click', function () {
        if (isMonacoActive) {
          deactivateMonaco();
        } else {
          activateMonaco();
        }
      });

      registerMessageHandler(function (data) {
        if (data.theme && monacoEditorInstance && window.monaco) {
          const theme = (data.theme === 'dark' || data.theme === 'night') ? 'vs-dark' : 'vs';
          monaco.editor.setTheme(theme);
        }
      });
    })();

    // Synchronize tab switches with tools
    onFileTabSwitched = function (idx) {
      if (typeof clearFindMatches === 'function') clearFindMatches();
      if (typeof clearTokenOccurrences === 'function') clearTokenOccurrences();
      if (isMonacoActive && monacoEditorInstance) {
        monacoEditorInstance.setValue(getActiveCodeText());
      }
    };

    // 6. Editor Keyboard Shortcuts (Alt+Z Word Wrap, Ctrl+G Go to Line)
    (function initCodeEditorShortcuts() {
      const btnToggleWrap = document.getElementById('btn-toggle-wrap');

      function toggleWrap() {
        if (!studioCodeContainer) return;
        const isWrapped = studioCodeContainer.classList.toggle('code-wrap-active');
        if (btnToggleWrap) btnToggleWrap.classList.toggle('active', isWrapped);
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

  function dispatchOpenDoc(docUrl, symbol, ownerClass) {
    if (window.parent && window.parent !== window) {
      try {
        if (window.parent.openDocView) {
          window.parent.openDocView(docUrl || undefined, symbol, ownerClass || undefined);
          return;
        }
      } catch (err) { }
      window.parent.postMessage({
        type: 'openDocView',
        symbol: symbol,
        ownerClass: ownerClass || undefined,
        url: docUrl || undefined
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
      curr = (nodes && nodes[curr]) ? nodes[curr].parent : null;
    }
    return chain;
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

    if (symKind === 'method' && syms.methods && syms.methods[cleanToken]) {
      return resolveMethodEntry(cleanToken, syms.methods[cleanToken], ownerClass, baseClass);
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
    if (syms.vars && syms.vars[cleanToken]) {
      return formatSingleSymbol(cleanToken, 'variable', syms.vars[cleanToken]);
    }
    if (syms.methods && syms.methods[cleanToken]) {
      return resolveMethodEntry(cleanToken, syms.methods[cleanToken], ownerClass, baseClass);
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
        if (popover.classList.contains('visible') && !popover.contains(ev.target) && !ev.target.closest('.clickable-uvm-sym')) {
          closeSymbolDisambigPopover();
        }
      });
      window.addEventListener('scroll', closeSymbolDisambigPopover, { passive: true, capture: true });
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
          dispatchOpenDoc(cand.doc_url || undefined, resolved.name, cand.class || '');
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
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ type: 'openExampleView', url: targetHref }, '*');
        }
        try {
          if (window.parent && window.parent.openExampleView) {
            window.parent.openExampleView(targetHref);
          }
        } catch (err) { }
        return;
      }

      // 3. Source Code Links
      if (link.classList.contains('src-code-link') || href.includes('src_view/')) {
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
        const docHref = link.getAttribute('data-doc-href') || 'docs_view/overviews/intro-txt.html';
        const cleanHashDoc = docHref.replace(/^docs_view\//, '');
        if (window.parent && window.parent !== window) {
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
        const isSrc = window.location.pathname.includes('src_view/');
        const match = window.location.pathname.match(/(?:docs_view|examples_view|src_view)\/(.*)$/);
        if (match) {
          const relPath = match[1];
          const depth = relPath.split('/').length;
          const rootRel = '../'.repeat(depth + 1);
          const routePrefix = isExample ? '#/example/' : (isSrc ? '#/src/' : '#/doc/');
          window.location.replace(rootRel + 'index.html' + routePrefix + relPath + window.location.hash);
        }
      }
    } catch (e) { }

    // Notify parent when document/example/source is loaded
    try {
      if (window.parent && window.parent !== window) {
        const isExample = window.location.pathname.includes('examples_view/');
        const isSrc = window.location.pathname.includes('src_view/');
        if (isExample) {
          const match = window.location.pathname.match(/(examples_view\/.*)$/);
          const exRel = match ? (match[1] + (window.location.hash || '')) : '';
          window.parent.postMessage({ type: 'exampleNavigated', url: exRel, title: document.title }, '*');
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

  function initDiagramZoom() {
    document.addEventListener('click', function (e) {
      const zoomBtn = e.target.closest('.doc-img-zoom-btn');
      const img = e.target.closest('.doc-diagram-img');
      if (zoomBtn || img) {
        e.preventDefault();
        e.stopPropagation();
        const card = (zoomBtn || img).closest('.doc-diagram-card');
        const targetImg = card ? card.querySelector('.doc-diagram-img') : img;
        if (targetImg) {
          const titleEl = card ? card.querySelector('.doc-diagram-caption, .doc-diagram-label span') : null;
          const title = titleEl ? titleEl.textContent.trim() : (targetImg.alt || 'UVM Diagram');
          const fullSrc = targetImg.src;
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
        const orig = copyTextSpan ? copyTextSpan.textContent : 'Copy';
        btn.classList.add('copied');
        if (copyTextSpan) copyTextSpan.textContent = 'Copied!';
        setTimeout(function () {
          btn.classList.remove('copied');
          if (copyTextSpan) copyTextSpan.textContent = orig;
        }, 2000);
      });
    });
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
    initScrollAnchor();

    if (document.getElementById('doc-toc-sidebar')) {
      initTOC();
    }
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

