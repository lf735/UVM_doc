/**
 * UVM 1.2 Documentation Page Controller
 * Shared client logic for all pages in docs_view/
 * Provides: Table of Contents (TOC) generator, ScrollSpy, deep-link routing,
 * theme sync, image modal triggers, and clipboard copy.
 */

(function initDocPage() {
  // In-page Table of Contents (On this page) generator & Scrollspy
  (function initDocTOC() {
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

    // 2. Check summary
    const summaryEl = contentEl.querySelector('.Summary');
    if (summaryEl) {
      const safeId = 'doc-nav-summary';
      summaryEl.id = safeId;
      summaryEl.setAttribute('data-anchor', 'Summary');
      topItems.push({
        id: safeId,
        anchor: 'Summary',
        title: 'Summary',
        type: 'summary',
        el: summaryEl
      });
    }

    // 3. Scan all topics in #Content
    const topicWrappers = contentEl.querySelectorAll('#Content > div');

    // Check if page contains H2 topics
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
      if (groups.length === 0) {
        toggleAllBtn.style.display = 'none';
      } else {
        toggleAllBtn.style.display = 'inline-flex';
      }
    }

    // Render TOC HTML
    let html = '';
    const initialItems = topItems.concat(standaloneItems);
    if (initialItems.length > 0) {
      html += '<ul class="doc-toc-list">';
      initialItems.forEach(function (item) {
        const cleanTitle = item.title.replace(/"/g, '&quot;');
        html += '<li class="doc-toc-item">';
        html += '<a href="#' + item.id + '" data-target-id="' + item.id + '" class="doc-toc-link" title="' + cleanTitle + '">';
        html += cleanTitle;
        html += '</a></li>';
      });
      html += '</ul>';
    }

    groups.forEach(function (group) {
      const cleanGroupTitle = group.title.replace(/"/g, '&quot;');
      const hasSubItems = group.items.length > 0;
      html += '<div class="doc-toc-group-block' + (hasSubItems ? '' : ' no-children') + '" id="block-' + group.id + '">';
      html += '<div class="doc-toc-group-header">';
      if (hasSubItems) {
        html += '<button class="doc-toc-chevron-btn" type="button" aria-label="Toggle group ' + cleanGroupTitle + '" title="Toggle group">';
        html += '<svg class="doc-toc-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
        html += '</button>';
      } else {
        html += '<span class="doc-toc-dot-indicator"></span>';
      }
      html += '<a href="#' + group.id + '" data-target-id="' + group.id + '" class="doc-toc-link doc-toc-group-title" title="' + cleanGroupTitle + '">';
      html += cleanGroupTitle;
      html += '</a>';
      if (hasSubItems) {
        html += '<span class="doc-toc-badge">' + group.items.length + '</span>';
      }
      html += '</div>';

      if (hasSubItems) {
        html += '<ul class="doc-toc-subitems">';
        group.items.forEach(function (sub) {
          const cleanSubTitle = sub.title.replace(/"/g, '&quot;');
          const extraCls = sub.isGroupHeader ? ' doc-toc-subgroup-header' : '';
          html += '<li class="doc-toc-item doc-toc-subitem' + extraCls + '">';
          html += '<a href="#' + sub.id + '" data-target-id="' + sub.id + '" class="doc-toc-link' + (sub.isGroupHeader ? ' doc-toc-subgroup-link' : '') + '" title="' + cleanSubTitle + '">';
          html += cleanSubTitle;
          html += '</a></li>';
        });
        html += '</ul>';
      }
      html += '</div>';
    });

    tocNav.innerHTML = html;

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

    // Content link click handling
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

    // Cross-frame listener
    window.addEventListener('message', function (e) {
      if (!e.data || typeof e.data !== 'object') return;
      if (e.data.type === 'scrollToSection') {
        const anchor = e.data.anchor;
        const targetId = e.data.id;
        let target = null;
        if (anchor) {
          if (anchor === 'MainTopic' || anchor === 'Overview') {
            target = document.getElementById('doc-nav-main') || document.getElementById('MainTopic');
          } else if (anchor === 'Summary') {
            target = document.getElementById('doc-nav-summary') || document.querySelector('.Summary');
          } else {
            try {
              target = document.querySelector('[data-anchor="' + CSS.escape(anchor) + '"]') ||
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
            if (target && target.tagName === 'A' && target.closest) {
              target = target.closest('#Content > div') || target.closest('.CTopic') || target;
            }
          }
        }
        if (!target && targetId) {
          target = document.getElementById(targetId) || document.querySelector('[data-doc-topic="' + targetId + '"]');
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

    if (window.location.hash) {
      handleHashNav(window.location.hash);
    }

    window.addEventListener('hashchange', function () {
      handleHashNav(window.location.hash);
    });

    setTimeout(updateScrollSpy, 120);
  })();

  // Code snippet copy button handler
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.code-copy-btn');
    if (!btn) return;
    const container = btn.closest('.code-block-container');
    if (!container) return;
    const codeEl = container.querySelector('code');
    if (!codeEl) return;
    const text = codeEl.innerText || codeEl.textContent;
    navigator.clipboard.writeText(text).then(() => {
      const copyText = btn.querySelector('.copy-text');
      const orig = copyText ? copyText.textContent : 'Copy';
      btn.classList.add('copied');
      if (copyText) copyText.textContent = 'Copied!';
      setTimeout(() => {
        btn.classList.remove('copied');
        if (copyText) copyText.textContent = orig;
      }, 2000);
    }).catch(err => {
      console.error('Copy failed: ', err);
    });
  });

  // Theme sync
  window.addEventListener('message', function (e) {
    if (e.data && e.data.theme) {
      document.documentElement.setAttribute('data-theme', e.data.theme);
    }
  });
  try {
    const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
    if (parentTheme) {
      document.documentElement.setAttribute('data-theme', parentTheme);
    }
  } catch (e) { }

  // Auto-restore into main app if opened directly outside iframe
  try {
    if (window.self === window.top) {
      const match = window.location.pathname.match(/(?:docs_view|src_view)\/(.*)$/);
      if (match) {
        const relPath = match[1];
        const depth = relPath.split('/').length;
        const rootRel = '../'.repeat(depth + 1);
        window.location.replace(rootRel + 'index.html#/doc/' + relPath + window.location.hash);
      }
    }
  } catch (e) { }

  // Inform parent that doc is loaded
  try {
    if (window.parent && window.parent !== window) {
      const match = window.location.pathname.match(/(docs_view\/.*)$/);
      const docRel = match ? match[1] : '';
      window.parent.postMessage({
        type: 'docNavigated',
        url: docRel
      }, '*');
    }
  } catch (e) { }

  // Breadcrumb home navigation (prevent recursive iframe embedding)
  document.addEventListener('click', function (e) {
    const homeLink = e.target.closest('.doc-breadcrumb-home');
    if (homeLink) {
      e.preventDefault();
      if (window.parent && window.parent !== window) {
        try {
          window.parent.location.hash = '#/doc/overviews/intro-txt.html';
          return;
        } catch (err) { }
        window.parent.postMessage({
          type: 'openDocView',
          url: 'docs_view/overviews/intro-txt.html'
        }, '*');
        return;
      }
      window.top.location.href = homeLink.getAttribute('href');
    }
  });

  // Intercept clicks on source code links
  document.addEventListener('click', function (e) {
    const link = e.target.closest('a');
    if (!link) return;
    const href = link.getAttribute('href');
    if (!href || href === '#' || href.startsWith('javascript:')) return;

    if (link.classList.contains('src-code-link') || href.includes('src_view/')) {
      e.preventDefault();
      const targetHref = new URL(link.getAttribute('href'), window.location.href).href;
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({
          type: 'openSourceView',
          url: targetHref
        }, '*');
      }
      try {
        if (window.parent && window.parent.openSourceView) {
          window.parent.openSourceView(targetHref);
        }
      } catch (err) { }
    }
  });

  // Diagram enlarge & zoom lightbox triggers
  document.addEventListener('click', function (e) {
    const zoomBtn = e.target.closest('.doc-img-zoom-btn');
    const img = e.target.closest('.doc-diagram-img');
    if (zoomBtn || img) {
      e.preventDefault();
      e.stopPropagation();
      const card = (zoomBtn || img).closest('.doc-diagram-card');
      const targetImg = card ? card.querySelector('.doc-diagram-img') : img;
      if (targetImg) {
        const titleEl = card ? card.querySelector('.doc-diagram-label span') : null;
        const title = titleEl ? titleEl.textContent.trim() : (targetImg.alt || 'UVM Diagram');
        const fullSrc = targetImg.src;
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({
            type: 'openImageModal',
            src: fullSrc,
            title: title
          }, '*');
        } else {
          window.open(fullSrc, '_blank');
        }
      }
    }
  });

  // Forward Escape key to parent to close modals if iframe has focus
  window.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && window.parent && window.parent !== window) {
      window.parent.postMessage({ type: 'closeImageModal' }, '*');
    }
  });
})();

