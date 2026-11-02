/**
 * UVM 1.2 Source View Page Controller
 * Shared client logic for all pages in src_view/
 * Provides: line highlighting, jump-to-symbol, copy raw code,
 * theme sync, and navigation back to documentation.
 */

// Immediate Theme Initialization (executes synchronously before DOM builds to eliminate FOUC / flash)
(function initImmediateTheme() {
  try {
    const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
    const localTheme = localStorage.getItem('theme');
    const theme = parentTheme || localTheme;
    if (theme) {
      document.documentElement.setAttribute('data-theme', theme);
    }
  } catch (e) { }
})();

(function initSrcPage() {
  // Copy raw source code
  const copyBtn = document.getElementById('copy-src-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      const rawTextEl = document.getElementById('raw-source-text');
      const text = rawTextEl ? rawTextEl.value : '';
      navigator.clipboard.writeText(text).then(() => {
        const span = copyBtn.querySelector('span');
        const orig = span ? span.textContent : 'Copy Code';
        if (span) span.textContent = 'Copied!';
        copyBtn.classList.add('btn-success');
        setTimeout(() => {
          if (span) span.textContent = orig;
          copyBtn.classList.remove('btn-success');
        }, 2000);
      });
    });
  }

  // Highlight active target line
  function highlightTargetLine() {
    const hash = window.location.hash;
    document.querySelectorAll('.sv-code-table tr.active-line').forEach(el => el.classList.remove('active-line'));
    if (hash && hash.startsWith('#L')) {
      const target = document.querySelector(hash);
      if (target) {
        target.classList.add('active-line');
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }

  window.addEventListener('hashchange', highlightTargetLine);
  window.addEventListener('DOMContentLoaded', highlightTargetLine);
  setTimeout(highlightTargetLine, 100);

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
      const match = window.location.pathname.match(/src_view\/(.*)$/);
      if (match) {
        const relPath = match[1];
        const depth = relPath.split('/').length;
        const rootRel = '../'.repeat(depth + 1);
        window.location.replace(rootRel + 'index.html#/src/' + relPath + window.location.hash);
      }
    }
  } catch (e) { }

  // Intercept clicks on doc button or doc links
  document.addEventListener('click', function (e) {
    const link = e.target.closest('a');
    if (!link) return;
    const href = link.getAttribute('href');
    if (!href || href === '#' || href.startsWith('javascript:')) return;

    if (link.classList.contains('src-to-doc-btn') || href.includes('docs_view/')) {
      e.preventDefault();
      const targetHref = new URL(link.getAttribute('href'), window.location.href).href;
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({
          type: 'openDocView',
          url: targetHref
        }, '*');
      }
      try {
        if (window.parent && window.parent.openDocView) {
          window.parent.openDocView(targetHref);
        }
      } catch (err) { }
    }
  });
})();

