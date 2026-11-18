/**
 * UVM 1.2 Interactive Home Page Logic
 * Handles parent SPA messaging, theme sync, and Personal Workspace (Bookmarks & Recent History).
 */

(function () {
  const BOOKMARKS_KEY = 'uvm_pinned_bookmarks';
  const RECENT_KEY = 'uvm_recent_history';
  const TUTORIAL_PROGRESS_KEY = 'uvm_tutorial_progress';

  function getTutorialMeta() {
    if (typeof TUTORIAL_META !== 'undefined' && TUTORIAL_META) {
      return TUTORIAL_META;
    }
    return { totalChapters: 0, defaultUrl: '', chapters: [], featured: [] };
  }

  function applyTheme(theme) {
    if (theme !== 'light' && theme !== 'dark') return;
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function readStorageArray(key) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function writeStorageArray(key, arr) {
    try {
      localStorage.setItem(key, JSON.stringify(arr));
    } catch (e) { }
  }

  function postToParent(payload) {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage(payload, '*');
    }
  }

  function navigateToItem(item) {
    if (!item || !item.url) return;
    if (item.type === 'example') {
      postToParent({ type: 'openExampleView', url: item.url });
    } else if (item.type === 'tutorial') {
      postToParent({ type: 'openTutorialView', url: item.url });
    } else if (item.type === 'source') {
      postToParent({ type: 'openSourceView', url: item.url });
    } else {
      postToParent({ type: 'openDocView', url: item.url });
    }
  }

  function getTypeLabel(type) {
    if (type === 'example') return 'Example';
    if (type === 'tutorial') return 'Tutorial';
    if (type === 'source') return 'Source';
    return 'Doc';
  }

  function renderBookmarks() {
    const listEl = document.getElementById('home-bookmarks-list');
    const countEl = document.getElementById('home-bookmarks-count');
    if (!listEl) return;

    const bookmarks = readStorageArray(BOOKMARKS_KEY);
    if (countEl) countEl.textContent = String(bookmarks.length);

    if (bookmarks.length === 0) {
      listEl.innerHTML =
        '<div class="home-empty-state">No pinned pages yet. Click the <strong>&#9733;</strong> button in the top-right pane header on any page to pin it here.</div>';
      return;
    }

    listEl.innerHTML = bookmarks
      .map((item, idx) => {
        const type = item.type || 'doc';
        const title = escapeHtml(item.title || item.url);
        const subtitle = escapeHtml((item.url || '').split('#')[0]);
        return `
          <div class="home-ws-item" data-ws-kind="bookmark" data-ws-index="${idx}">
            <button type="button" class="home-ws-link" title="${subtitle}">
              <span class="home-ws-type home-ws-type-${escapeHtml(type)}">${getTypeLabel(type)}</span>
              <span class="home-ws-title">${title}</span>
            </button>
            <button type="button" class="home-ws-remove" data-remove-bookmark="${idx}" title="Unpin bookmark" aria-label="Unpin ${title}">&times;</button>
          </div>
        `;
      })
      .join('');

    listEl.querySelectorAll('.home-ws-link').forEach((btn, idx) => {
      btn.addEventListener('click', () => navigateToItem(bookmarks[idx]));
    });

    listEl.querySelectorAll('[data-remove-bookmark]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.getAttribute('data-remove-bookmark'), 10);
        const current = readStorageArray(BOOKMARKS_KEY);
        if (!isNaN(idx) && idx >= 0 && idx < current.length) {
          current.splice(idx, 1);
          writeStorageArray(BOOKMARKS_KEY, current);
          renderBookmarks();
        }
      });
    });
  }

  function renderRecent() {
    const listEl = document.getElementById('home-recent-list');
    const clearBtn = document.getElementById('home-clear-recent');
    if (!listEl) return;

    const recent = readStorageArray(RECENT_KEY);
    if (clearBtn) {
      clearBtn.style.display = recent.length > 0 ? 'inline-flex' : 'none';
    }

    if (recent.length === 0) {
      listEl.innerHTML =
        '<div class="home-empty-state">Pages you open across Docs, Sources, and Examples will appear here automatically.</div>';
      return;
    }

    listEl.innerHTML = recent
      .map((item, idx) => {
        const type = item.type || 'doc';
        const title = escapeHtml(item.title || item.url);
        const subtitle = escapeHtml((item.url || '').split('#')[0]);
        return `
          <div class="home-ws-item" data-ws-kind="recent" data-ws-index="${idx}">
            <button type="button" class="home-ws-link" title="${subtitle}">
              <span class="home-ws-type home-ws-type-${escapeHtml(type)}">${getTypeLabel(type)}</span>
              <span class="home-ws-title">${title}</span>
            </button>
          </div>
        `;
      })
      .join('');

    listEl.querySelectorAll('.home-ws-link').forEach((btn, idx) => {
      btn.addEventListener('click', () => navigateToItem(recent[idx]));
    });
  }

  function renderTutorialFeaturedCards() {
    const gridEl = document.getElementById('home-tutorial-cards');
    if (!gridEl) return;
    const meta = getTutorialMeta();
    const cards = Array.isArray(meta.featured) ? meta.featured : [];
    gridEl.innerHTML = cards.map((card) => `
      <button type="button" class="home-card" data-tutorial="${escapeHtml(card.href)}">
        <div class="home-card-top">
          <span class="home-card-title">${escapeHtml(card.title)}</span>
          <span class="home-badge ${escapeHtml(card.badge_class || 'home-badge-beginner')}">${escapeHtml(card.badge || '')}</span>
        </div>
        <p class="home-card-desc">${escapeHtml(card.desc || '')}</p>
      </button>
    `).join('');
    gridEl.querySelectorAll('[data-tutorial]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const url = btn.getAttribute('data-tutorial');
        if (url) postToParent({ type: 'openTutorialView', url });
      });
    });
  }

  function renderTutorialProgress() {
    const textEl = document.getElementById('home-tutorial-progress-text');
    const fillEl = document.getElementById('home-tutorial-progress-fill');
    const ctaEl = document.getElementById('home-tutorial-cta');
    if (!textEl && !fillEl) return;

    const meta = getTutorialMeta();
    const chapters = Array.isArray(meta.chapters) ? meta.chapters : [];
    const total = meta.totalChapters || chapters.length || 0;

    let completed = {};
    try {
      const parsed = JSON.parse(localStorage.getItem(TUTORIAL_PROGRESS_KEY) || '{}');
      completed = (parsed && parsed.completed) || {};
    } catch (e) { }

    const activeSlugs = new Set(chapters.map((c) => c.slug));
    const doneCount = Object.keys(completed).filter((k) => completed[k] && (activeSlugs.size === 0 || activeSlugs.has(k))).length;
    const pct = total > 0 ? Math.min(100, Math.round((doneCount / total) * 100)) : 0;
    if (textEl) textEl.textContent = `${doneCount} / ${total} chapters`;
    if (fillEl) fillEl.style.width = `${pct}%`;

      if (ctaEl && chapters.length > 0) {
        const nextCh = chapters.find((c) => !completed[c.slug]) || chapters[chapters.length - 1];
        ctaEl.setAttribute('data-tutorial', nextCh.href);
        const labelSpan = ctaEl.querySelector('span');
        if (labelSpan) {
          labelSpan.innerHTML = doneCount > 0 ? 'Resume Course &rarr;' : 'Start Course &rarr;';
        }
      }
    }

    function renderWorkspace() {
      renderBookmarks();
      renderRecent();
      renderTutorialProgress();
    }

    document.addEventListener('DOMContentLoaded', () => {
      const searchBtn = document.getElementById('home-search-btn');
      if (searchBtn) {
        searchBtn.addEventListener('click', () => {
          postToParent({ type: 'openSearchModal' });
        });
      }

      document.querySelectorAll('[data-tab]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const tab = btn.getAttribute('data-tab');
          if (tab) postToParent({ type: 'switchSidebarTab', tab });
        });
      });

      document.querySelectorAll('[data-doc]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const url = btn.getAttribute('data-doc');
          if (url) postToParent({ type: 'openDocView', url });
        });
      });

      document.querySelectorAll('[data-example]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const url = btn.getAttribute('data-example');
          if (url) postToParent({ type: 'openExampleView', url });
        });
      });

      document.querySelectorAll('[data-tutorial]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const url = btn.getAttribute('data-tutorial');
          if (url) postToParent({ type: 'openTutorialView', url });
        });
      });

      const clearRecentBtn = document.getElementById('home-clear-recent');
      if (clearRecentBtn) {
        clearRecentBtn.addEventListener('click', () => {
          writeStorageArray(RECENT_KEY, []);
          renderRecent();
        });
      }

      renderTutorialFeaturedCards();
      renderWorkspace();
    });

    window.addEventListener('message', (e) => {
      if (!e.data || typeof e.data !== 'object') return;
      if (e.data.theme) {
        applyTheme(e.data.theme);
      } else if (e.data.type === 'workspaceDataUpdated' || e.data.type === 'tutorialProgressUpdated') {
        renderWorkspace();
      }
    });

    window.addEventListener('storage', (e) => {
      if (e.key === BOOKMARKS_KEY || e.key === RECENT_KEY || e.key === TUTORIAL_PROGRESS_KEY) {
        renderWorkspace();
      } else if (e.key === 'theme' && e.newValue) {
        applyTheme(e.newValue);
      }
    });
  }) ();
