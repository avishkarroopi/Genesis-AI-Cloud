"""
GENESIS Research Engine — Phase-3 Enhanced
DuckDuckGo Lite search with caching, multi-query fallback, and source validation.
"""

import requests
import re
import html
import time

# --- Phase-3: Search result cache ---
_search_cache = {}
_CACHE_MAX = 50
_CACHE_TTL = 300  # seconds


def _get_cached(query):
    """Return cached result if fresh, else None."""
    key = query.strip().lower()
    if key in _search_cache:
        result, ts = _search_cache[key]
        if time.time() - ts < _CACHE_TTL:
            print(f"[RESEARCH] Cache hit for: {key[:40]}", flush=True)
            return result
        else:
            del _search_cache[key]
    return None


def _set_cache(query, result):
    """Store result in cache, evict oldest if full."""
    if len(_search_cache) >= _CACHE_MAX:
        oldest_key = next(iter(_search_cache))
        del _search_cache[oldest_key]
    _search_cache[query.strip().lower()] = (result, time.time())


def _validate_snippet(snippet):
    """Basic source validation — reject empty, too short, or junk snippets."""
    if not snippet or len(snippet) < 15:
        return False
    # Reject common junk patterns
    junk_patterns = ["javascript", "enable cookies", "captcha", "access denied"]
    for junk in junk_patterns:
        if junk in snippet.lower():
            return False
    return True


def _run_search(query):
    """Execute a single DDG Lite search and return cleaned snippets."""
    url = "https://lite.duckduckgo.com/lite/"
    payload = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    r = requests.post(url, data=payload, headers=headers, timeout=10)
    r.raise_for_status()

    snippets = re.findall(r'<td class="result-snippet">(.*?)</td>', r.text, re.IGNORECASE | re.DOTALL)
    results = []
    for i, s in enumerate(snippets[:6]):
        clean = html.unescape(re.sub(r'<[^>]+>', '', s)).strip()
        if _validate_snippet(clean):
            results.append(f"- Source {len(results)+1}: {clean}")
        if len(results) >= 4:
            break
    return results


def search_and_summarize(query):
    """Search with caching and multi-query fallback."""
    print(f"[RESEARCH] Querying web for: {query[:50]}...", flush=True)

    # Check cache first
    cached = _get_cached(query)
    if cached:
        return cached

    try:
        results = _run_search(query)

        # --- Phase-3: Multi-query fallback if empty ---
        if not results:
            print("[RESEARCH] Primary search empty, trying fallback query...", flush=True)
            fallback_query = f"what is {query}" if len(query.split()) <= 3 else query + " explained"
            try:
                results = _run_search(fallback_query)
            except Exception:
                pass

        if results:
            output = "Research Results:\n" + "\n".join(results)
            _set_cache(query, output)
            return output

        return ""

    except Exception as e:
        print(f"[RESEARCH] Error: {e}", flush=True)
        return ""

