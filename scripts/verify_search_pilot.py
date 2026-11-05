#!/usr/bin/env python3
"""
Verification script for Global Search Enhancement and Docked Search Pilot Bar.
Asserts index.html markup, css/style.css selectors, and js/app.js integration.
"""

import sys
import re
from pathlib import Path

def test_html():
    html_path = Path("index.html")
    assert html_path.exists(), "index.html not found"
    content = html_path.read_text(encoding="utf-8")

    required_ids = [
        "modal-recent-searches",
        "recent-searches-chips",
        "recent-searches-clear",
        "search-nav-bar",
        "search-nav-reopen-btn",
        "search-nav-query",
        "search-nav-badge",
        "search-nav-prev",
        "search-nav-next",
        "search-nav-list",
        "search-nav-close"
    ]
    for element_id in required_ids:
        assert f'id="{element_id}"' in content, f"Missing id: {element_id} in index.html"

    print("PASS: index.html elements verified successfully.")

def test_css():
    css_path = Path("css/style.css")
    assert css_path.exists(), "css/style.css not found"
    content = css_path.read_text(encoding="utf-8")

    required_classes = [
        ".modal-recent-searches",
        ".recent-search-chip",
        ".recent-clear-btn",
        ".search-result-item.current-result",
        ".search-result-item.viewed",
        ".res-viewed-icon",
        ".search-nav-bar",
        ".search-nav-query-group",
        ".search-nav-query",
        ".search-nav-badge",
        ".search-nav-controls",
        ".search-nav-btn",
        ".search-nav-btn.disabled"
    ]
    for cls in required_classes:
        assert cls in content, f"Missing CSS selector: {cls} in css/style.css"

    print("PASS: css/style.css rules verified successfully.")

def test_js():
    js_path = Path("js/app.js")
    assert js_path.exists(), "js/app.js not found"
    content = js_path.read_text(encoding="utf-8")

    # Check bracket balance
    # Strip comments and strings for accurate brace matching
    cleaned = re.sub(r'//.*', '', content)
    cleaned = re.sub(r'/\*[\s\S]*?\*/', '', cleaned)
    # Simple balance counter for braces
    open_curly = cleaned.count('{')
    close_curly = cleaned.count('}')
    assert open_curly == close_curly, f"Mismatched curly braces in js/app.js: {open_curly} open, {close_curly} close"

    # Check key functions and variables
    required_symbols = [
        "activeSearchSession",
        "getRecentSearches",
        "saveRecentSearch",
        "clearRecentSearches",
        "renderRecentSearches",
        "updateSearchPilotBar",
        "closeSearchPilot",
        "navigateSearchResult",
        "modalRecentSearches",
        "recentSearchesChips",
        "recentSearchesClear",
        "searchNavBar",
        "searchNavQuery",
        "searchNavBadge",
        "searchNavPrev",
        "searchNavNext",
        "searchNavList",
        "searchNavClose",
        "current-result",
        "viewed",
        "res-viewed-icon"
    ]
    for sym in required_symbols:
        assert sym in content, f"Missing symbol or identifier: {sym} in js/app.js"

    print("PASS: js/app.js syntax balance and integration verified successfully.")

if __name__ == "__main__":
    test_html()
    test_css()
    test_js()
    print("ALL SEARCH PILOT TESTS PASSED!")
