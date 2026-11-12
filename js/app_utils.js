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

  // =========================================================================
  // Matcher & Multi-word / Regex Search Utilities
  // =========================================================================

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

      let score = 0;
      let catMatched = false;
      if (re.test(name)) {
        score = 1000;
      } else if (re.test(fullColon) || re.test(fullDot)) {
        score = 900;
        catMatched = true;
      } else if (re.test(fullSpace)) {
        score = 800;
        catMatched = true;
      } else if (re.test(cat)) {
        score = 600;
        catMatched = true;
      } else if (re.test(desc)) {
        score = 300;
      } else {
        return { match: false, score: 0 };
      }
      if (item.isInherited) {
        score = catMatched ? Math.max(50, score - 50) : Math.max(50, score - 600);
      }
      return { match: true, score };
    }

    const words = matcher.words;
    if (words.length === 0) return { match: true, score: 0 };

    const targetName = matcher.isCaseSensitive ? name : name.toLowerCase();
    const targetCat = matcher.isCaseSensitive ? cat : cat.toLowerCase();
    const targetDesc = matcher.isCaseSensitive ? desc : desc.toLowerCase();
    const cleanQuery = matcher.clean;

    const combined = `${targetName} ${targetCat} ${targetDesc}`;
    const allFound = words.every(w => combined.includes(w));
    if (!allFound) return { match: false, score: 0 };

    const catMatched = targetCat ? words.some(w => targetCat.includes(w)) : false;

    let score = 0;
    if (targetName === cleanQuery) {
      score = 1000;
    } else if (targetName.startsWith(cleanQuery)) {
      score = 900;
    } else if (words.every(w => targetName.includes(w))) {
      score = 800;
    } else if (words.every(w => targetName.includes(w) || targetCat.includes(w))) {
      score = 700;
    } else if (words.every(w => targetCat.includes(w))) {
      score = 500;
    } else {
      score = 300;
    }

    if (item.isInherited) {
      score = catMatched ? Math.max(50, score - 50) : Math.max(50, score - 600);
    }

    return { match: true, score };
  }

  function highlightMatch(text, matcher) {
    if (!text) return '';
    if (!matcher) return escapeHtml(text);

    let pattern = null;
    if (matcher.type === 'regex') {
      if (!matcher.valid || !matcher.regex) return escapeHtml(text);
      try {
        const gFlags = (matcher.regex.flags || '') + (matcher.regex.flags.includes('g') ? '' : 'g');
        pattern = new RegExp(matcher.regex.source, gFlags);
      } catch (e) {
        return escapeHtml(text);
      }
    } else {
      const words = matcher.words;
      if (!words || words.length === 0) return escapeHtml(text);
      const escaped = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).filter(Boolean);
      if (escaped.length === 0) return escapeHtml(text);
      pattern = new RegExp(`(${escaped.join('|')})`, matcher.isCaseSensitive ? 'g' : 'gi');
    }

    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = pattern.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(escapeHtml(text.substring(lastIndex, match.index)));
      }
      parts.push(`<strong style="color:var(--primary); text-decoration:underline">${escapeHtml(match[0])}</strong>`);
      lastIndex = pattern.lastIndex;

      if (match[0].length === 0) {
        pattern.lastIndex++;
      }
    }

    if (lastIndex < text.length) {
      parts.push(escapeHtml(text.substring(lastIndex)));
    }

    return parts.join('');
  }

  function isItemTypeAllowed(itemType, filterSet) {
    if (!filterSet || filterSet.has('all') || filterSet.size === 0) return true;
    if (!itemType) return false;
    if (itemType === 'method') {
      return filterSet.has('function') || filterSet.has('task') || filterSet.has('method');
    }
    if (itemType === 'constant' || itemType === 'parameter') {
      return filterSet.has('constant');
    }
    if (itemType === 'variable') {
      return filterSet.has('variable');
    }
    if (itemType === 'type' || itemType === 'enum' || itemType === 'enumeration') {
      return filterSet.has('type');
    }
    if (itemType === 'port') {
      return filterSet.has('port');
    }
    if (itemType === 'studio' || itemType === 'stepper' || itemType === 'example') {
      return filterSet.has('example');
    }
    if (itemType === 'overview') {
      return filterSet.has('class') || filterSet.has('file');
    }
    return filterSet.has(itemType);
  }

  function isRagResultAllowed(r, filterSet) {
    if (!filterSet || filterSet.has('all') || filterSet.size === 0) return true;

    const url = (r.targetUrl || (r.chunk && r.chunk.url) || '').toLowerCase();
    const isExample = url.includes('examples_view/') || r.type === 'example' || r.type === 'studio' || r.type === 'stepper' || r.targetType === 'example';

    if (filterSet.has('example')) {
      if (isExample) {
        if (filterSet.has('beginner') || filterSet.has('intermediate') || filterSet.has('advanced')) {
          const desc = (r.snippet || (r.chunk && r.chunk.text) || '').toLowerCase();
          const diff = ((r.chunk && r.chunk.difficulty) || '').toLowerCase();
          const cat = (r.category || '').toLowerCase();
          let matchDiff = false;
          ['beginner', 'intermediate', 'advanced'].forEach(d => {
            if (filterSet.has(d)) {
              if (diff === d || cat.includes(d) || desc.includes(d + ' level') || desc.includes('level: ' + d)) {
                matchDiff = true;
              }
            }
          });
          return matchDiff;
        }
        return true;
      }
    }
    if (filterSet.size === 1 && filterSet.has('example') && !isExample) {
      return false;
    }
    if (isExample && !filterSet.has('example')) {
      return false;
    }

    if (filterSet.has('class')) {
      if (r.type === 'class' || r.targetType === 'class' || r.type === 'overview') return true;
    }

    if (filterSet.has('function') || filterSet.has('task')) {
      if (r.type === 'method' || r.type === 'function' || r.type === 'task' ||
        r.targetType === 'method' || r.targetType === 'function' || r.targetType === 'task') {
        return true;
      }
      if (r.targetSections && r.targetSections.some(s => s.type === 'method' || s.type === 'function' || s.type === 'task')) {
        return true;
      }
      if (r.children && r.children.some(c => c.chunk && (c.chunk.type === 'method' || c.chunk.type === 'function' || c.chunk.type === 'task'))) {
        return true;
      }
    }

    if (filterSet.has('macro')) {
      if (r.type === 'macro' || r.targetType === 'macro') return true;
      if (r.targetSections && r.targetSections.some(s => s.type === 'macro')) return true;
      if (r.children && r.children.some(c => c.chunk && c.chunk.type === 'macro')) return true;
    }

    if (filterSet.has('file')) {
      if (r.type === 'file' || r.targetType === 'file') return true;
      const docPath = url.split('#')[0];
      if (typeof global.UVM_DATA !== 'undefined' && global.UVM_DATA.docToSrc && global.UVM_DATA.docToSrc[docPath]) {
        return true;
      }
      if (r.type === 'overview') return true;
    }

    return false;
  }

  global.UvmAppUtils = {
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
    isRagResultAllowed
  };
})(window);

