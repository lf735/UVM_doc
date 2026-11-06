/**
 * UVM 1.2 Source View Page Controller (Compatibility Wrapper)
 * All core source viewing features (line highlighting, symbol jump,
 * copy code, deep link copying, theme sync, standalone redirect)
 * are unified in js/page_common.js.
 */
(function () {
  if (window.UVM_PAGE_COMMON && window.UVM_PAGE_COMMON.initAll) {
    window.UVM_PAGE_COMMON.initAll();
  }
})();

