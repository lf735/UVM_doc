/**
 * UVM 1.2 Interactive Documentation - Shared App Utilities
 * Pure, stateless helpers exposed via window.UvmAppUtils (offline file:// safe).
 */
(function (global) {
  'use strict';

  function normalizeViewUrl(url, defaultUrl, primaryPrefix, fallbackPrefix) {
    if (!url) return defaultUrl;
    const hashIdx = url.indexOf('#');
    const pathPart = hashIdx !== -1 ? url.substring(0, hashIdx) : url;
    const hashPart = hashIdx !== -1 ? url.substring(hashIdx) : '';
    let clean = pathPart.replace(/^[./]+/, '');
    if (fallbackPrefix && clean.includes(fallbackPrefix)) {
      clean = clean.substring(clean.indexOf(fallbackPrefix));
    } else if (clean.includes(primaryPrefix)) {
      clean = clean.substring(clean.indexOf(primaryPrefix));
    } else {
      clean = primaryPrefix + clean;
    }
    return clean + hashPart;
  }

  function normalizeDocUrl(url) {
    return normalizeViewUrl(url, 'docs_view/overviews/intro-txt.html', 'docs_view/', 'examples_view/');
  }

  function normalizeExampleUrl(url) {
    return normalizeViewUrl(url, 'examples_view/basics/hello_world.html', 'examples_view/');
  }

  function normalizeSrcUrl(url) {
    return normalizeViewUrl(url, 'src_view/comps/uvm_driver.svh.html#L44', 'src_view/');
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

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

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

  global.UvmAppUtils = {
    normalizeDocUrl,
    normalizeExampleUrl,
    normalizeSrcUrl,
    normalizePathForCompare,
    urlsMatch,
    escapeHtml,
    debounce
  };
})(window);

