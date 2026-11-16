#!/usr/bin/env python3
"""
Verification script for App Shell Scroll Isolation, Mobile Header Pinning,
and Mobile Pane Toggle Icon Synchronization.
Asserts css/style.css layout/mobile rules and js/app.js guards.
"""

import sys
import re
from pathlib import Path


def extract_media_block(css_text: str, media_header: str) -> str:
    idx = css_text.find(media_header)
    assert idx != -1, f"Missing media query: {media_header}"
    brace_start = css_text.find("{", idx)
    assert brace_start != -1, f"Malformed media query: {media_header}"
    depth = 0
    for pos in range(brace_start, len(css_text)):
        ch = css_text[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return css_text[brace_start + 1 : pos]
    raise AssertionError(f"Unclosed media query: {media_header}")


def test_css_shell_scroll_isolation():
    css_path = Path("css/style.css")
    assert css_path.exists(), "css/style.css not found"
    content = css_path.read_text(encoding="utf-8")

    # 1. Outer app shell & source viewer must use overflow: clip to prevent anchor/scrollIntoView scroll propagation
    required_blocks = [
        ("html:has(> body#app-container)", ["overflow: clip;", "overscroll-behavior: none;"]),
        ("body#app-container", ["height: 100dvh;", "display: flex;", "flex-direction: column;", "overflow: clip;", "overscroll-behavior: none;"]),
        (".app-header", ["flex: 0 0 auto;"]),
        (".app-layout", ["flex: 1 1 auto;", "min-height: 0;", "overflow: clip;"]),
        (".app-viewport", ["overflow: clip;"]),
        (".pane", ["overflow: clip;"]),
        ("html.src-page", ["overflow: clip;"]),
        ("body.src-viewer-body", ["height: 100dvh;", "max-height: 100dvh;", "overflow: clip !important;"]),
    ]
    for selector, props in required_blocks:
        pattern = re.escape(selector) + r"\s*\{([^}]*)\}"
        m = re.search(pattern, content)
        assert m, f"Missing CSS rule for {selector}"
        body = m.group(1)
        for prop in props:
            assert prop in body, f"Missing '{prop}' in CSS rule for {selector}"

    # 2. Mobile (@media (max-width: 860px)) header pinning & view-switcher hiding
    mobile_css = extract_media_block(content, "@media (max-width: 860px)")
    assert "body#app-container" in mobile_css, "Missing mobile body#app-container rule"
    assert "position: fixed;" in mobile_css, "Mobile shell/header must use position: fixed"
    assert "padding-top: var(--header-height);" in mobile_css, "Mobile body#app-container must reserve header height"
    assert re.search(r"\.app-header\s*\{[^}]*position:\s*fixed;[^}]*top:\s*0;", mobile_css), (
        "Mobile .app-header must be fixed at top: 0"
    )
    assert re.search(r"\.view-switcher\s*\{[^}]*display:\s*none;", mobile_css), (
        "Mobile .view-switcher must be hidden (display: none)"
    )
    assert "html:not(.src-page):not(:has(> body#app-container))" in mobile_css, (
        "Mobile overflow-x: hidden rule must exclude app shell and src-page"
    )

    # 3. .CBody lists must restore left padding after global reset (* { padding: 0; margin: 0; })
    assert re.search(r"\.CBody\s+ul,\s*\.CBody\s+ol\s*\{[^}]*padding-left:", content), (
        ".CBody ul, .CBody ol must define padding-left so bullets do not render in the margin"
    )

    # 4. Responsive compact TOC (@media (max-width: 1000px)) & TOC scroll isolation
    assert re.search(r"\.doc-toc-sidebar\s*\{[^}]*overscroll-behavior:\s*contain;", content), (
        "Desktop .doc-toc-sidebar must set overscroll-behavior: contain"
    )
    assert re.search(r"\.doc-toc-mobile-trigger\s*\{[^}]*display:\s*none;", content), (
        "Desktop .doc-toc-mobile-trigger must be hidden by default"
    )
    toc_mobile_css = extract_media_block(content, "@media (max-width: 1000px)")
    for required_tok in (
        "overflow-x: clip;",
        ".doc-toc-sidebar",
        "position: sticky;",
        ".doc-toc-mobile-trigger",
        ".doc-toc-sidebar.is-pinned .doc-toc-mobile-trigger",
        ".doc-toc-sidebar.toc-mobile-open .doc-toc-inner",
        "overscroll-behavior: contain;",
        "scroll-margin-top: 56px;",
    ):
        assert required_tok in toc_mobile_css, f"Missing '{required_tok}' in @media (max-width: 1000px)"

    # 5. Sticky .doc-breadcrumbs & non-scrolling .doc-body wrapper
    assert re.search(r"\.doc-body\s*\{[^}]*overflow-x:\s*clip;[^}]*overflow-y:\s*visible;", content), (
        ".doc-body must use overflow-x: clip; overflow-y: visible; so sticky breadcrumbs and TOC work reliably"
    )
    assert re.search(r"\.doc-breadcrumbs\s*\{[^}]*position:\s*sticky;[^}]*top:\s*0;", content), (
        ".doc-breadcrumbs must use position: sticky; top: 0;"
    )
    assert re.search(r"\.doc-breadcrumbs\.is-pinned\s*\{", content), (
        ".doc-breadcrumbs.is-pinned must define pinned elevation/border styling"
    )
    assert "--doc-breadcrumbs-height" in content, (
        "css/style.css must offset sticky TOC and scroll-margin-top by --doc-breadcrumbs-height"
    )

    print("PASS: css/style.css shell scroll isolation, mobile header, sticky breadcrumbs, and compact TOC rules verified.")


def test_js_guards():
    js_path = Path("js/app.js")
    assert js_path.exists(), "js/app.js not found"
    content = js_path.read_text(encoding="utf-8")

    required_patterns = [
        r"function\s+resetShellScroll\s*\(",
        r"window\.addEventListener\(\s*['\"]scroll['\"]\s*,\s*resetShellScroll",
        r"document\.addEventListener\(\s*['\"]scroll['\"]",
        r"function\s+updatePaneExpandButtons\s*\(\s*mode\s*\)",
        r"updatePaneExpandButtons\(currentMode\)",
        r"resetShellScroll\(\)",
    ]
    for pat in required_patterns:
        assert re.search(pat, content), f"Missing required pattern in js/app.js: {pat}"

    # Verify updatePaneExpandButtons is called both on resize and after parseHash()
    idx_parse = content.find("parseHash();")
    idx_init_btns = content.find("updatePaneExpandButtons(currentMode);", idx_parse)
    idx_init_reset = content.find("resetShellScroll();", idx_parse)
    assert idx_parse != -1 and idx_init_btns != -1 and idx_init_reset != -1, (
        "Initialization must call parseHash(), updatePaneExpandButtons(currentMode), and resetShellScroll()"
    )

    print("PASS: js/app.js shell scroll guard and mobile button sync verified.")


def test_mobile_toc_controller():
    pc_path = Path("js/page_common.js")
    assert pc_path.exists(), "js/page_common.js not found"
    content = pc_path.read_text(encoding="utf-8")

    required_patterns = [
        r"doc-toc-mobile-trigger",
        r"doc-toc-mobile-current",
        r"function\s+getBreadcrumbsHeight\s*\(",
        r"function\s+initBreadcrumbs\s*\(",
        r"--doc-breadcrumbs-height",
        r"function\s+isCompactTocMode\s*\(",
        r"function\s+getScrollOffset\s*\(",
        r"function\s+setMobileTocOpen\s*\(",
        r"function\s+updatePinnedState\s*\(",
        r"function\s+updateMobileCurrentLabel\s*\(",
        r"_uvmTocWheelHandler",
        r"_uvmTocTouchMoveHandler",
    ]
    for pat in required_patterns:
        assert re.search(pat, content), f"Missing required pattern in js/page_common.js: {pat}"

    print("PASS: js/page_common.js compact responsive TOC controller verified.")


def main() -> int:
    test_css_shell_scroll_isolation()
    test_js_guards()
    test_mobile_toc_controller()
    print("ALL SHELL LAYOUT & MOBILE CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

