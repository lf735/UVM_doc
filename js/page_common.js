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
    const delay = duration || 2000;
    const orig = originalText || (buttonEl ? buttonEl.textContent : 'Copy');
    if (buttonEl) {
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
    window.addEventListener('message', function (e) {
      if (e.data && e.data.theme) {
        document.documentElement.setAttribute('data-theme', e.data.theme);
        document.documentElement.style.colorScheme = e.data.theme;
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
  // Table of Contents (TOC) & ScrollSpy
  // =========================================================================

  function initTOC() {
    const contentEl = document.getElementById('Content');
    const tocSidebar = document.getElementById('doc-toc-sidebar');
    const tocNav = document.getElementById('doc-toc-nav');
    const toggleAllBtn = document.getElementById('doc-toc-toggle-all');
    if (!contentEl || !tocSidebar || !tocNav) return;

    const topItems = [];
    const groups = [];
    const standaloneItems = [];
    let currentGroup = null;
    let topicSeq = 0;

    // 1. Check main topic
    const mainTopic = contentEl.querySelector('#MainTopic .CTitle, #MainTopic h1, #MainTopic h2');
    if (mainTopic) {
      const safeId = 'doc-nav-main';
      mainTopic.id = safeId;
      const mainA = mainTopic.querySelector('a[name]');
      const mainAnchor = mainA ? mainA.getAttribute('name') : 'MainTopic';
      mainTopic.setAttribute('data-anchor', mainAnchor);
      topItems.push({
        id: safeId,
        anchor: mainAnchor,
        title: (mainTopic.innerText || mainTopic.textContent || 'Overview').trim(),
        type: 'main',
        el: mainTopic
      });
    }

    // 2. Check top-level summary or contents
    const topSummaryEl = contentEl.querySelector('#MainTopic .Summary, #doc-nav-main .Summary, .Summary');
    if (topSummaryEl) {
      const sTitleEl = topSummaryEl.querySelector('.STitle');
      const sTitleText = (sTitleEl ? (sTitleEl.innerText || sTitleEl.textContent || '') : '').trim();
      const isContents = sTitleText.toLowerCase() === 'contents';
      const safeId = isContents ? 'doc-nav-contents' : 'doc-nav-summary';
      const safeAnchor = isContents ? 'Contents' : 'Summary';
      const label = isContents ? 'Contents' : 'Summary';

      topSummaryEl.id = topSummaryEl.id || safeId;
      topSummaryEl.setAttribute('data-anchor', safeAnchor);
      topItems.push({
        id: topSummaryEl.id,
        anchor: safeAnchor,
        title: label,
        type: isContents ? 'contents' : 'summary',
        el: topSummaryEl
      });
    }

    // 3. Scan all topics in #Content
    const topicWrappers = contentEl.querySelectorAll('#Content > div');

    let hasH2 = false;
    for (let i = 0; i < topicWrappers.length; i++) {
      const topic = topicWrappers[i].querySelector('.CTopic');
      if (!topic || topic.id === 'MainTopic') continue;
      const titleEl = topic.querySelector('.CTitle');
      if (titleEl && titleEl.tagName.toUpperCase() === 'H2') {
        hasH2 = true;
        break;
      }
    }

    topicWrappers.forEach(function (wrap) {
      const topic = wrap.querySelector('.CTopic');
      if (!topic || topic.id === 'MainTopic') return;
      const titleEl = topic.querySelector('.CTitle');
      if (!titleEl) return;
      const rawTitle = (titleEl.innerText || titleEl.textContent || '').trim();
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

      const cls = wrap.className || '';
      const tag = titleEl.tagName.toUpperCase();
      const isH2 = tag === 'H2';
      const isCGroup = cls.indexOf('CGroup') !== -1;

      if (hasH2) {
        if (isH2) {
          currentGroup = {
            id: safeId,
            anchor: aName || safeId,
            title: rawTitle,
            el: wrap,
            items: []
          };
          groups.push(currentGroup);
        } else {
          const itemObj = {
            id: safeId,
            anchor: aName || safeId,
            title: rawTitle,
            el: wrap,
            isGroupHeader: isCGroup,
            type: 'subitem'
          };
          if (currentGroup) {
            currentGroup.items.push(itemObj);
          } else {
            standaloneItems.push(itemObj);
          }
        }
      } else {
        if (isCGroup) {
          currentGroup = {
            id: safeId,
            anchor: aName || safeId,
            title: rawTitle,
            el: wrap,
            items: []
          };
          groups.push(currentGroup);
        } else {
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
            standaloneItems.push(itemObj);
          }
        }
      }
    });

    const totalItemsCount = topItems.length + standaloneItems.length + groups.length + groups.reduce(function (acc, g) { return acc + g.items.length; }, 0);
    if (totalItemsCount <= 1) {
      tocSidebar.style.display = 'none';
      return;
    }

    if (toggleAllBtn) {
      toggleAllBtn.style.display = (groups.length === 0) ? 'none' : 'inline-flex';
    }

    // Render TOC HTML
    let tocHtml = '';
    const initialItems = topItems.concat(standaloneItems);
    if (initialItems.length > 0) {
      tocHtml += '<ul class="doc-toc-list">';
      initialItems.forEach(function (item) {
        const cleanTitle = item.title.replace(/"/g, '&quot;');
        tocHtml += '<li class="doc-toc-item">';
        tocHtml += '<a href="#' + item.id + '" data-target-id="' + item.id + '" class="doc-toc-link" title="' + cleanTitle + '">';
        tocHtml += cleanTitle;
        tocHtml += '</a></li>';
      });
      tocHtml += '</ul>';
    }

    groups.forEach(function (group) {
      const cleanGroupTitle = group.title.replace(/"/g, '&quot;');
      const hasSubItems = group.items.length > 0;
      tocHtml += '<div class="doc-toc-group-block' + (hasSubItems ? '' : ' no-children') + '" id="block-' + group.id + '">';
      tocHtml += '<div class="doc-toc-group-header">';
      if (hasSubItems) {
        tocHtml += '<button class="doc-toc-chevron-btn" type="button" aria-label="Toggle group ' + cleanGroupTitle + '" title="Toggle group">';
        tocHtml += '<svg class="doc-toc-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
        tocHtml += '</button>';
      } else {
        tocHtml += '<span class="doc-toc-dot-indicator"></span>';
      }
      tocHtml += '<a href="#' + group.id + '" data-target-id="' + group.id + '" class="doc-toc-link doc-toc-group-title" title="' + cleanGroupTitle + '">';
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
          tocHtml += '<li class="doc-toc-item doc-toc-subitem' + extraCls + '">';
          tocHtml += '<a href="#' + sub.id + '" data-target-id="' + sub.id + '" class="doc-toc-link' + (sub.isGroupHeader ? ' doc-toc-subgroup-link' : '') + '" title="' + cleanSubTitle + '">';
          tocHtml += cleanSubTitle;
          tocHtml += '</a></li>';
        });
        tocHtml += '</ul>';
      }
      tocHtml += '</div>';
    });

    tocNav.innerHTML = tocHtml;

    const allNavItems = [];
    initialItems.forEach(function (item) {
      const link = tocNav.querySelector('.doc-toc-link[data-target-id="' + item.id + '"]');
      allNavItems.push({ id: item.id, anchor: item.anchor || item.id, title: item.title, el: item.el, link: link });
    });
    groups.forEach(function (group) {
      const groupLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + group.id + '"]');
      allNavItems.push({ id: group.id, anchor: group.anchor || group.id, title: group.title, el: group.el, link: groupLink });
      group.items.forEach(function (sub) {
        const subLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + sub.id + '"]');
        allNavItems.push({ id: sub.id, anchor: sub.anchor || sub.id, title: sub.title, el: sub.el, link: subLink });
      });
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
      const targetY = getTargetScrollY(targetEl);
      const currentScroll = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
      const distance = Math.abs(currentScroll - targetY);

      pendingTargetEl = targetEl;
      startManualScroll(Math.min(2400, Math.max(600, distance * 0.15 + 400)));
      performScroll(targetY);

      targetEl.classList.add('doc-target-highlight');
      setTimeout(function () {
        targetEl.classList.remove('doc-target-highlight');
      }, 1600);
    }

    function scrollTocToItem(linkEl) {
      if (!linkEl || !tocSidebar) return;
      const sidebarRect = tocSidebar.getBoundingClientRect();
      const linkRect = linkEl.getBoundingClientRect();
      if (linkRect.top < sidebarRect.top || linkRect.bottom > sidebarRect.bottom) {
        const currentScroll = tocSidebar.scrollTop;
        const targetOffset = linkRect.top - sidebarRect.top + currentScroll - (sidebarRect.height / 2);
        try {
          tocSidebar.scrollTo({ top: Math.max(0, targetOffset), behavior: 'smooth' });
        } catch (e) {
          tocSidebar.scrollTop = Math.max(0, targetOffset);
        }
      }
    }

    // Click on TOC link
    const tocLinks = tocNav.querySelectorAll('.doc-toc-link');
    tocLinks.forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = link.getAttribute('data-target-id');
        const target = document.getElementById(targetId) || document.querySelector('[data-doc-topic="' + targetId + '"]');

        tocLinks.forEach(function (l) { l.classList.remove('active'); });
        link.classList.add('active');

        const parentGroupBlock = link.closest('.doc-toc-group-block');
        if (parentGroupBlock && parentGroupBlock.classList.contains('collapsed')) {
          parentGroupBlock.classList.remove('collapsed');
          updateToggleAllBtn();
        }

        if (target) {
          scrollToElement(target);
        }
      });
    });

    // Content in-page link click handling
    contentEl.addEventListener('click', function (e) {
      const link = e.target.closest('a[href*="#"]');
      if (!link) return;
      const href = link.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript:')) return;
      if (link.classList.contains('src-code-link') || href.includes('src_view/')) return;

      if (href.startsWith('#')) {
        const targetId = link.getAttribute('data-target-id') || href.substring(1);
        let target = document.getElementById(targetId) || document.querySelector('[data-doc-topic="' + targetId + '"]');
        if (!target) {
          try {
            target = document.querySelector('[data-anchor="' + CSS.escape(targetId) + '"]') ||
              document.querySelector('a[name="' + CSS.escape(targetId) + '"]');
          } catch (err) { }
        }
        if (target && target.tagName === 'A' && target.closest) {
          target = target.closest('#Content > div') || target.closest('.CTopic') || target;
        }
        if (target) {
          e.preventDefault();
          scrollToElement(target);

          const realId = target.id || target.getAttribute('data-doc-topic') || targetId;
          try {
            history.replaceState(null, null, '#' + realId);
          } catch (err) { }

          if (tocNav && realId) {
            const mLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + realId + '"]');
            if (mLink) {
              tocLinks.forEach(function (l) { l.classList.remove('active'); });
              mLink.classList.add('active');
              const pB = mLink.closest('.doc-toc-group-block');
              if (pB && pB.classList.contains('collapsed')) {
                pB.classList.remove('collapsed');
                updateToggleAllBtn();
              }
              scrollTocToItem(mLink);
            }
          }
        }
      }
    });

    // Group chevron toggles
    const chevronBtns = tocNav.querySelectorAll('.doc-toc-chevron-btn');
    chevronBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        const block = btn.closest('.doc-toc-group-block');
        if (block) {
          block.classList.toggle('collapsed');
          updateToggleAllBtn();
        }
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
      toggleAllBtn.addEventListener('click', function () {
        const allBlocks = tocNav.querySelectorAll('.doc-toc-group-block');
        const anyExpanded = Array.from(allBlocks).some(function (b) { return !b.classList.contains('collapsed'); });
        if (anyExpanded) {
          allBlocks.forEach(function (b) { b.classList.add('collapsed'); });
        } else {
          allBlocks.forEach(function (b) { b.classList.remove('collapsed'); });
        }
        updateToggleAllBtn();
      });
    }

    // ScrollSpy
    let scrollTimer = null;
    function updateScrollSpy() {
      if (isManualScrolling) return;

      let activeItem = null;
      for (let i = 0; i < allNavItems.length; i++) {
        const item = allNavItems[i];
        if (!item.el) continue;
        const rect = item.el.getBoundingClientRect();
        if (rect.top <= 100) {
          activeItem = item;
        } else {
          break;
        }
      }

      if (!activeItem && allNavItems.length > 0) {
        activeItem = allNavItems[0];
      }

      if (activeItem && activeItem.link) {
        tocLinks.forEach(function (link) {
          link.classList.toggle('active', link === activeItem.link);
        });

        const parentBlock = activeItem.link.closest('.doc-toc-group-block');
        if (parentBlock && parentBlock.classList.contains('collapsed')) {
          parentBlock.classList.remove('collapsed');
          updateToggleAllBtn();
        }

        scrollTocToItem(activeItem.link);

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

    window.addEventListener('scrollend', function () {
      if (isManualScrolling) {
        clearTimeout(manualScrollTimer);
        checkAndCorrectScroll();
      }
    });

    window.addEventListener('scroll', function () {
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
    }, { passive: true });

    // Cross-frame scrollToSection listener
    window.addEventListener('message', function (e) {
      if (!e.data || typeof e.data !== 'object') return;
      if (e.data.type === 'scrollToSection') {
        const anchor = e.data.anchor;
        const targetId = e.data.id || anchor;
        let target = null;
        if (targetId) {
          target = document.getElementById(targetId) || document.querySelector('[data-doc-topic="' + targetId + '"]');
        }
        if (!target && anchor) {
          if (anchor === 'MainTopic' || anchor === 'Overview' || anchor === 'doc-nav-main') {
            target = document.getElementById('doc-nav-main') || document.getElementById('MainTopic');
          } else if (anchor === 'Contents' || anchor === 'doc-nav-contents') {
            target = document.getElementById('doc-nav-contents') || document.querySelector('.ContentsSummary');
          } else if (anchor === 'Summary' || anchor === 'doc-nav-summary') {
            target = document.getElementById('doc-nav-summary') || document.querySelector('.ClassSummary, .Summary');
          } else {
            try {
              target = document.getElementById(anchor) ||
                document.querySelector('[data-anchor="' + CSS.escape(anchor) + '"]') ||
                document.querySelector('a[name="' + CSS.escape(anchor) + '"]');
            } catch (err) { }
            if (!target) {
              const allA = document.querySelectorAll('[data-anchor], a[name]');
              for (let i = 0; i < allA.length; i++) {
                if (allA[i].getAttribute('data-anchor') === anchor || allA[i].getAttribute('name') === anchor) {
                  target = allA[i];
                  break;
                }
              }
            }
          }
        }
        if (target && target.tagName === 'A' && target.closest) {
          target = target.closest('#Content > div') || target.closest('.CTopic') || target;
        }
        if (target) {
          scrollToElement(target);
          const targetNavId = target.id || target.getAttribute('data-doc-topic');
          if (tocNav && targetNavId) {
            const mLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + targetNavId + '"]');
            if (mLink) {
              tocLinks.forEach(function (l) { l.classList.remove('active'); });
              mLink.classList.add('active');
              const pB = mLink.closest('.doc-toc-group-block');
              if (pB && pB.classList.contains('collapsed')) {
                pB.classList.remove('collapsed');
                updateToggleAllBtn();
              }
              scrollTocToItem(mLink);
            }
          }
        }
      }
    });

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
  // Heading Anchors & Canonical Link Sharing
  // =========================================================================

  function initHeadingAnchors() {
    const LINK_ICON_SVG = '<svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>';
    const CHECK_ICON_SVG = '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>';

    function getHeadingAnchor(headingEl) {
      if (!headingEl) return '';
      if (headingEl.id && headingEl.id !== 'IFirstHeading') return headingEl.id;

      const aTag = headingEl.querySelector('a[name], a[id]');
      if (aTag) {
        const name = aTag.getAttribute('name') || aTag.getAttribute('id');
        if (name && !name.startsWith('link')) return name;
      }

      const wrap = headingEl.closest('[data-anchor], [data-doc-topic], .CClass, .CMethod, .CGroup, .Summary');
      if (wrap) {
        const topicId = wrap.id || wrap.getAttribute('data-doc-topic');
        if (topicId) return topicId;
        const anchor = wrap.getAttribute('data-anchor');
        if (anchor) return anchor;
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

      heading.appendChild(btn);
    }

    function scanHeadings() {
      document.querySelectorAll('.CTitle, .STitle, .IHeading').forEach(setupHeading);
    }

    scanHeadings();
    setTimeout(scanHeadings, 150);

    document.addEventListener('click', function (e) {
      const btn = e.target.closest('.heading-anchor-btn');
      if (!btn) return;

      e.preventDefault();
      e.stopPropagation();

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
  // Multi-File Code Studio Controller
  // =========================================================================

  function initCodeStudio() {
    const studioTabBar = document.getElementById('studio-tab-bar');
    const studioTabs = document.querySelectorAll('.studio-tab');
    const codePanes = document.querySelectorAll('.file-code-pane');
    const studioFileSelect = document.getElementById('studio-file-select');
    const studioCodeContainer = document.getElementById('studio-code-container');
    const studioTabScrollLeft = document.getElementById('studio-tab-scroll-left');
    const studioTabScrollRight = document.getElementById('studio-tab-scroll-right');
    const btnCopyCode = document.getElementById('btn-copy-code');
    const btnDownloadRaw = document.getElementById('btn-download-raw');
    const btnCopyExampleLink = document.getElementById('btn-copy-example-link');
    const btnSplitSource = document.getElementById('btn-split-source');

    if (!studioTabBar && !codePanes.length) return;

    let currentFileIdx = 0;
    const zipPayloadEl = document.getElementById('zip-payload');
    let filesList = [];
    try {
      if (zipPayloadEl && zipPayloadEl.getAttribute('data-zip')) {
        filesList = JSON.parse(zipPayloadEl.getAttribute('data-zip'));
      }
    } catch (e) { }

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

    // Line number click -> copy line deep-link & highlight
    document.querySelectorAll('.file-code-pane .ln a').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        const lineNum = a.textContent.trim();
        const targetRow = a.closest('tr');
        if (targetRow) {
          document.querySelectorAll('.file-code-pane tr.active-line').forEach(function (tr) {
            tr.classList.remove('active-line');
          });
          targetRow.classList.add('active-line');
        }

        let fullUrl = window.location.href.split('#')[0] + `#L${lineNum}`;
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
          fullUrl = `${parentBase}#/example/${exClean}?file=${currentFileIdx}#L${lineNum}`;
        }

        copyText(fullUrl).then(function () {
          const origText = a.textContent;
          a.textContent = '✓';
          setTimeout(function () { a.textContent = origText; }, 1200);
        });
      });
    });

    if (btnCopyCode) {
      btnCopyCode.addEventListener('click', function () {
        const curFile = filesList[currentFileIdx];
        if (!curFile) return;
        copyText(curFile.content).then(function () {
          bindCopyFeedback(btnCopyCode, 'Copy Code', 'Copied!');
        });
      });
    }

    if (btnDownloadRaw) {
      btnDownloadRaw.addEventListener('click', function () {
        const curFile = filesList[currentFileIdx];
        if (!curFile) return;
        const blob = new Blob([curFile.content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = curFile.name.split('/').pop();
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
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

    // Expose switchFileTab for stepper synchronization
    return { switchFileTab: switchFileTab, getCurrentFileIdx: function () { return currentFileIdx; } };
  }

  // =========================================================================
  // Native Client-Side Zero-Dependency ZIP Generator
  // =========================================================================

  function crc32(uint8) {
    let crc = ~0;
    for (let i = 0; i < uint8.length; i++) {
      crc ^= uint8[i];
      for (let j = 0; j < 8; j++) {
        crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
      }
    }
    return ~crc >>> 0;
  }

  function createNativeZipBlob(files) {
    const encoder = new TextEncoder();
    const fileEntries = [];
    let offset = 0;
    const parts = [];

    for (const f of files) {
      const nameBytes = encoder.encode(f.name);
      const dataBytes = encoder.encode(f.content);
      const crc = crc32(dataBytes);

      // Local File Header (30 bytes + name length)
      const header = new Uint8Array(30);
      const view = new DataView(header.buffer);
      header.set([0x50, 0x4B, 0x03, 0x04], 0); // PK\x03\x04
      view.setUint16(4, 20, true);              // version 2.0
      view.setUint16(6, 0x0800, true);          // UTF-8 flag
      view.setUint16(8, 0, true);               // compression: 0 (Store)
      view.setUint16(10, 0, true);              // time
      view.setUint16(12, 0, true);              // date
      view.setUint32(14, crc, true);            // CRC-32
      view.setUint32(18, dataBytes.length, true); // compressed size
      view.setUint32(22, dataBytes.length, true); // uncompressed size
      view.setUint16(26, nameBytes.length, true); // filename length
      view.setUint16(28, 0, true);              // extra field length

      fileEntries.push({ offset, nameBytes, dataBytes, crc, length: dataBytes.length });
      parts.push(header, nameBytes, dataBytes);
      offset += header.length + nameBytes.length + dataBytes.length;
    }

    const cdOffset = offset;
    let cdSize = 0;

    // Central Directory Headers (46 bytes + name length)
    for (const entry of fileEntries) {
      const cd = new Uint8Array(46);
      const view = new DataView(cd.buffer);
      cd.set([0x50, 0x4B, 0x01, 0x02], 0);    // PK\x01\x02
      view.setUint16(4, 20, true);            // version made by
      view.setUint16(6, 20, true);            // version needed
      view.setUint16(8, 0x0800, true);        // UTF-8 flag
      view.setUint16(10, 0, true);            // compression: 0
      view.setUint16(12, 0, true);            // time
      view.setUint16(14, 0, true);            // date
      view.setUint32(16, entry.crc, true);    // CRC-32
      view.setUint32(20, entry.length, true); // comp size
      view.setUint32(24, entry.length, true); // uncomp size
      view.setUint16(28, entry.nameBytes.length, true); // filename len
      view.setUint16(30, 0, true);            // extra len
      view.setUint16(32, 0, true);            // comment len
      view.setUint16(34, 0, true);            // disk start
      view.setUint16(36, 0, true);            // int attr
      view.setUint32(38, 0, true);            // ext attr
      view.setUint32(42, entry.offset, true); // local header offset

      parts.push(cd, entry.nameBytes);
      cdSize += cd.length + entry.nameBytes.length;
    }

    // End of Central Directory (22 bytes)
    const eocd = new Uint8Array(22);
    const eocdView = new DataView(eocd.buffer);
    eocd.set([0x50, 0x4B, 0x05, 0x06], 0);    // PK\x05\x06
    eocdView.setUint16(4, 0, true);           // disk number
    eocdView.setUint16(6, 0, true);           // start disk
    eocdView.setUint16(8, files.length, true);  // entries on disk
    eocdView.setUint16(10, files.length, true); // total entries
    eocdView.setUint32(12, cdSize, true);     // size of central directory
    eocdView.setUint32(16, cdOffset, true);   // offset of central directory
    eocdView.setUint16(20, 0, true);          // comment length

    parts.push(eocd);
    return new Blob(parts, { type: 'application/zip' });
  }

  function initZipDownload() {
    const btnDownloadZip = document.getElementById('btn-download-zip');
    const zipPayloadEl = document.getElementById('zip-payload');
    if (!btnDownloadZip || !zipPayloadEl) return;

    btnDownloadZip.addEventListener('click', function () {
      let filesList = [];
      try {
        filesList = JSON.parse(zipPayloadEl.getAttribute('data-zip') || '[]');
      } catch (e) {
        console.warn('Could not parse zip payload', e);
      }
      if (!filesList || filesList.length === 0) return;

      const zipBlob = createNativeZipBlob(filesList);
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      const pageTitle = (document.title.split('|')[0] || 'uvm_archive').trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');
      a.href = url;
      a.download = `${pageTitle}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  // =========================================================================
  // Simulation Console & Log Filters
  // =========================================================================

  function initSimulationConsole() {
    const simTabs = document.querySelectorAll('.sim-tab');
    const simCmdText = document.getElementById('sim-cmd-text');
    const btnCopyCmd = document.getElementById('btn-copy-cmd');
    const termFilters = document.querySelectorAll('.term-filter');
    const terminalBody = document.getElementById('terminal-body');

    if (!terminalBody && !simTabs.length) return;

    const rawLogContent = terminalBody ? terminalBody.textContent : '';

    const SIM_COMMANDS = {
      questa: 'make -f Makefile.questa run',
      vcs: 'make -f Makefile.vcs run',
      xcelium: 'make -f Makefile.ius run'
    };

    simTabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        simTabs.forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');
        const sim = tab.getAttribute('data-sim');
        if (simCmdText && SIM_COMMANDS[sim]) {
          simCmdText.textContent = SIM_COMMANDS[sim];
        }
      });
    });

    if (btnCopyCmd && simCmdText) {
      btnCopyCmd.addEventListener('click', function () {
        copyText(simCmdText.textContent).then(function () {
          bindCopyFeedback(btnCopyCmd, 'Copy', 'Copied!');
        });
      });
    }

    termFilters.forEach(function (btn) {
      btn.addEventListener('click', function () {
        termFilters.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        const level = btn.getAttribute('data-level');
        if (!terminalBody) return;

        if (level === 'all') {
          terminalBody.textContent = rawLogContent;
        } else if (level === 'info') {
          const filtered = rawLogContent.split('\n').filter(function (l) {
            return l.includes('UVM_INFO') || l.includes('---') || l.includes('Report counts') || l.includes('PASSED');
          });
          terminalBody.textContent = filtered.join('\n');
        } else if (level === 'warning') {
          const filtered = rawLogContent.split('\n').filter(function (l) {
            return l.includes('UVM_WARNING') || l.includes('---');
          });
          terminalBody.textContent = filtered.join('\n');
        } else if (level === 'error') {
          const filtered = rawLogContent.split('\n').filter(function (l) {
            return l.includes('UVM_ERROR') || l.includes('UVM_FATAL') || l.includes('---');
          });
          terminalBody.textContent = filtered.join('\n');
        }
      });
    });
  }

  // =========================================================================
  // Interactive Visual Flow Stepper
  // =========================================================================

  function initFlowStepper(studioController) {
    const stepperSection = document.getElementById('visual-flow-stepper');
    const stepNodes = document.querySelectorAll('.step-node');
    const stepPrevBtn = document.getElementById('stepper-prev');
    const stepNextBtn = document.getElementById('stepper-next');
    const stepPlayBtn = document.getElementById('stepper-play');
    const stepActiveTitle = document.getElementById('step-active-title');
    const stepActiveComp = document.getElementById('step-active-comp');
    const stepActiveDesc = document.getElementById('step-active-desc');
    const stepActiveLog = document.getElementById('step-active-log');
    const stepperPayloadEl = document.getElementById('stepper-payload');
    const terminalBody = document.getElementById('terminal-body');
    const studioCodeContainer = document.getElementById('studio-code-container');

    if (!stepperSection || !stepNodes.length) return;

    let stepperSteps = [];
    try {
      if (stepperPayloadEl && stepperPayloadEl.getAttribute('data-stepper')) {
        stepperSteps = JSON.parse(stepperPayloadEl.getAttribute('data-stepper'));
      }
    } catch (e) {
      console.warn('Could not parse stepper payload', e);
    }
    if (!stepperSteps || stepperSteps.length === 0) return;

    const zipPayloadEl = document.getElementById('zip-payload');
    let filesList = [];
    try {
      if (zipPayloadEl && zipPayloadEl.getAttribute('data-zip')) {
        filesList = JSON.parse(zipPayloadEl.getAttribute('data-zip'));
      }
    } catch (e) { }

    let currentStepIdx = 0;
    let playInterval = null;

    function renderStep(idx) {
      if (idx < 0) idx = 0;
      if (idx >= stepperSteps.length) idx = stepperSteps.length - 1;
      currentStepIdx = idx;

      const step = stepperSteps[idx];

      stepNodes.forEach(function (node, i) {
        node.classList.toggle('active', i === idx);
        node.classList.toggle('completed', i < idx);
      });

      if (stepActiveTitle) stepActiveTitle.textContent = step.title;
      if (stepActiveComp) stepActiveComp.textContent = `Target: ${step.component}`;
      if (stepActiveDesc) stepActiveDesc.textContent = step.desc;
      if (stepActiveLog) stepActiveLog.textContent = step.log_snippet;

      if (stepPrevBtn) stepPrevBtn.disabled = idx === 0;
      if (stepNextBtn) stepNextBtn.disabled = idx === stepperSteps.length - 1;

      // Topology card highlight
      document.querySelectorAll('.topo-card').forEach(function (card) {
        const text = card.textContent.toLowerCase();
        const compTarget = step.component.toLowerCase();
        const match = compTarget.split(/[,&]/).some(function (c) { return text.includes(c.trim()); });
        card.classList.toggle('highlighted', match);
      });

      // Synchronize with Code Studio
      if (step.highlight_file && studioController && studioController.switchFileTab) {
        const fileIndex = filesList.findIndex(function (f) { return f.name.includes(step.highlight_file); });
        if (fileIndex !== -1 && fileIndex !== studioController.getCurrentFileIdx()) {
          studioController.switchFileTab(fileIndex);
        }
      }

      if (step.highlight_line) {
        const activeIdx = studioController ? studioController.getCurrentFileIdx() : 0;
        const activePane = document.getElementById(`file-pane-${activeIdx}`);
        const targetRow = activePane ? activePane.querySelector(`tr[data-line="${step.highlight_line}"], tr#L${step.highlight_line}`) : null;
        if (targetRow) {
          document.querySelectorAll('.file-code-pane tr.stepper-highlight').forEach(function (tr) {
            tr.classList.remove('stepper-highlight');
          });
          targetRow.classList.add('stepper-highlight');
          if (studioCodeContainer) {
            const rowTop = targetRow.offsetTop;
            studioCodeContainer.scrollTo({
              top: Math.max(0, rowTop - (studioCodeContainer.clientHeight / 2)),
              behavior: 'smooth'
            });
          }
        }
      }

      // Synchronize with simulation log trace
      if (terminalBody && step.log_snippet) {
        const logText = terminalBody.textContent || '';
        const needle = step.log_snippet.split('[')[0].trim();
        if (needle) {
          const pos = logText.indexOf(needle);
          if (pos !== -1) {
            const lineNo = logText.substring(0, pos).split('\n').length;
            terminalBody.scrollTo({ top: Math.max(0, (lineNo - 2) * 19), behavior: 'smooth' });
          }
        }
      }
    }

    function stopAutoPlay() {
      if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
        if (stepPlayBtn) stepPlayBtn.textContent = 'Play ▶';
      }
    }

    if (stepPrevBtn) {
      stepPrevBtn.addEventListener('click', function () {
        stopAutoPlay();
        renderStep(currentStepIdx - 1);
      });
    }

    if (stepNextBtn) {
      stepNextBtn.addEventListener('click', function () {
        stopAutoPlay();
        renderStep(currentStepIdx + 1);
      });
    }

    stepNodes.forEach(function (node, idx) {
      node.addEventListener('click', function () {
        stopAutoPlay();
        renderStep(idx);
      });
    });

    if (stepPlayBtn) {
      stepPlayBtn.addEventListener('click', function () {
        if (playInterval) {
          stopAutoPlay();
        } else {
          stepPlayBtn.textContent = 'Pause ❚❚';
          playInterval = setInterval(function () {
            if (currentStepIdx >= stepperSteps.length - 1) {
              renderStep(0);
            } else {
              renderStep(currentStepIdx + 1);
            }
          }, 2500);
        }
      });
    }

    renderStep(0);
  }

  // =========================================================================
  // Derived Classes & Component Hierarchy Cards
  // =========================================================================

  function initDerivedClasses() {
    document.addEventListener('click', function (e) {
      const header = e.target.closest('.derived-classes-header');
      if (header) {
        const card = header.closest('.derived-classes-card');
        if (card) card.classList.toggle('collapsed');
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        const header = e.target.closest('.derived-classes-header');
        if (header) {
          e.preventDefault();
          const card = header.closest('.derived-classes-card');
          if (card) card.classList.toggle('collapsed');
        }
      }
    });

    // Handle click on derived-class-pill for exact in-page or cross-page jump
    document.addEventListener('click', function (e) {
      const pill = e.target.closest('.derived-class-pill');
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
  }

  // =========================================================================
  // Centralized Link Interception & Cross-Frame Routing
  // =========================================================================

  function initLinks() {
    // Intercept clicks on links pointing to source code, example studios, or UVM symbols
    document.addEventListener('click', function (e) {
      // 1. Clickable UVM Symbols (spans in Code Studio or <a> badges in headers)
      const symEl = e.target.closest('.clickable-uvm-sym');
      if (symEl) {
        e.preventDefault();
        const sym = symEl.getAttribute('data-sym') || symEl.textContent.trim();
        const customUrl = symEl.getAttribute('data-doc') || symEl.getAttribute('data-url');
        if (sym && window.parent && window.parent !== window) {
          window.parent.postMessage({
            type: 'openDocView',
            symbol: sym,
            url: customUrl || undefined
          }, '*');
        }
        try {
          if (window.parent && window.parent.openDocView) {
            window.parent.openDocView(customUrl || undefined, sym);
          }
        } catch (err) { }
        return;
      }

      const link = e.target.closest('a');
      if (!link) return;

      const href = link.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript:')) return;

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
        const targetHref = new URL(link.getAttribute('href'), window.location.href).href;
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ type: 'openSourceView', url: targetHref }, '*');
        }
        try {
          if (window.parent && window.parent.openSourceView) {
            window.parent.openSourceView(targetHref);
          }
        } catch (err) { }
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
        const match = window.location.pathname.match(/(?:docs_view|examples_view|src_view)\/(.*)$/);
        if (match) {
          const relPath = match[1];
          const depth = relPath.split('/').length;
          const rootRel = '../'.repeat(depth + 1);
          const routePrefix = isExample ? '#/example/' : '#/doc/';
          window.location.replace(rootRel + 'index.html' + routePrefix + relPath + window.location.hash);
        }
      }
    } catch (e) { }

    // Notify parent when document/example is loaded
    try {
      if (window.parent && window.parent !== window) {
        const isExample = window.location.pathname.includes('examples_view/');
        if (isExample) {
          const match = window.location.pathname.match(/(examples_view\/.*)$/);
          const exRel = match ? (match[1] + (window.location.hash || '')) : '';
          window.parent.postMessage({ type: 'exampleNavigated', url: exRel, title: document.title }, '*');
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

  function initAll() {
    initTheme();
    initLinks();
    initCodeBlocks();
    initDiagramZoom();

    if (document.getElementById('doc-toc-sidebar')) {
      initTOC();
    }
    if (document.querySelector('.CTitle, .STitle, .IHeading')) {
      initHeadingAnchors();
    }

    const studio = initCodeStudio();
    initZipDownload();
    initSimulationConsole();

    if (document.getElementById('visual-flow-stepper')) {
      initFlowStepper(studio);
    }
    if (document.querySelector('.derived-classes-card, .derived-class-pill')) {
      initDerivedClasses();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  return {
    clipboard: { copyText: copyText, bindCopyFeedback: bindCopyFeedback },
    initTheme: initTheme,
    initTOC: initTOC,
    initHeadingAnchors: initHeadingAnchors,
    initCodeStudio: initCodeStudio,
    initZipDownload: initZipDownload,
    initSimulationConsole: initSimulationConsole,
    initFlowStepper: initFlowStepper,
    initDerivedClasses: initDerivedClasses,
    initLinks: initLinks,
    initAll: initAll
  };
})();

