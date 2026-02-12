"""
Lightweight web research utilities.

Goals:
- Search for related pages
- Fetch page text
- Rank candidate sources by a simple originality heuristic
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, urlparse

import requests
from bs4 import BeautifulSoup


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

_STOPWORDS = {
    "a", "o", "os", "as", "de", "da", "do", "das", "dos", "e", "ou", "em", "no", "na",
    "nos", "nas", "um", "uma", "uns", "umas", "para", "por", "com", "sem", "que", "se",
    "ao", "aos", "the", "and", "or", "to", "in", "on", "for", "of", "is", "are", "this",
    "that", "it", "you", "your", "me", "my",
}

_SITE_TO_DOMAIN = {
    "youtube": "youtube.com",
    "google": "google.com",
    "github": "github.com",
    "wikipedia": "wikipedia.org",
    "reddit": "reddit.com",
    "x": "x.com",
}


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _normalize_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""

    parsed = urlparse(raw)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        uddg = qs.get("uddg")
        if uddg:
            return uddg[0]

    if raw.startswith("//"):
        return "https:" + raw
    return raw


def _domain(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _tokenize(text: str) -> set:
    tokens = re.findall(r"[a-zA-Z0-9]{3,}", (text or "").lower())
    return {t for t in tokens if t not in _STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a.union(b)
    if not union:
        return 0.0
    return len(a.intersection(b)) / float(len(union))


def _collect_result_links(soup: BeautifulSoup, max_results: int) -> List[Dict[str, str]]:
    nodes = soup.select(".result")
    if not nodes:
        nodes = soup.select("a.result__a")

    sources: List[Dict[str, str]] = []
    seen_urls = set()

    for node in nodes:
        if len(sources) >= max_results:
            break

        if getattr(node, "name", "") == "a":
            link = node
            container = node.parent
        else:
            link = node.select_one("a.result__a")
            container = node

        if not link:
            continue

        url = _normalize_url(link.get("href", ""))
        if not url:
            continue

        parsed = urlparse(url)
        if not parsed.scheme.startswith("http"):
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = _clean_text(link.get_text(" ", strip=True))
        snippet_node = None
        if container:
            snippet_node = container.select_one(".result__snippet")
        snippet = _clean_text(snippet_node.get_text(" ", strip=True) if snippet_node else "")

        sources.append(
            {
                "title": title or url,
                "url": url,
                "snippet": snippet,
                "domain": _domain(url),
            }
        )

    return sources


def _search_ddg(query: str, max_results: int, timeout: int) -> List[Dict[str, str]]:
    for endpoint in ("https://duckduckgo.com/html/", "https://lite.duckduckgo.com/lite/"):
        try:
            response = requests.get(
                endpoint,
                params={"q": query},
                headers=_HEADERS,
                timeout=timeout,
            )
            if response.status_code >= 500:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            sources = _collect_result_links(soup, max_results)
            if sources:
                return sources
        except Exception:
            continue
    return []


def _search_bing(query: str, max_results: int, timeout: int) -> List[Dict[str, str]]:
    try:
        response = requests.get(
            "https://www.bing.com/search",
            params={"q": query},
            headers=_HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    sources: List[Dict[str, str]] = []
    seen = set()

    nodes = soup.select("li.b_algo")
    if nodes:
        for node in nodes:
            if len(sources) >= max_results:
                break
            link = node.select_one("h2 a")
            if not link:
                continue
            url = _normalize_url(link.get("href", ""))
            if not url or url in seen:
                continue
            seen.add(url)
            title = _clean_text(link.get_text(" ", strip=True))
            snippet_node = node.select_one(".b_caption p")
            snippet = _clean_text(snippet_node.get_text(" ", strip=True) if snippet_node else "")
            sources.append(
                {
                    "title": title or url,
                    "url": url,
                    "snippet": snippet,
                    "domain": _domain(url),
                }
            )
        if sources:
            return sources

    # Fallback for pages where result cards are rendered differently.
    for a in soup.select("a[href]"):
        if len(sources) >= max_results:
            break
        url = _normalize_url(a.get("href", ""))
        if not url.startswith("http"):
            continue
        domain = _domain(url)
        if not domain or "bing.com" in domain or domain.endswith(".bing.com"):
            continue
        if url in seen:
            continue
        seen.add(url)
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        sources.append(
            {
                "title": title,
                "url": url,
                "snippet": "",
                "domain": domain,
            }
        )
    return sources


def _search_brave(query: str, max_results: int, timeout: int) -> List[Dict[str, str]]:
    try:
        response = requests.get(
            "https://search.brave.com/search",
            params={"q": query, "source": "web"},
            headers=_HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    sources: List[Dict[str, str]] = []
    seen = set()
    for a in soup.select("a[href]"):
        if len(sources) >= max_results:
            break
        url = _normalize_url(a.get("href", ""))
        if not url.startswith("http"):
            continue
        domain = _domain(url)
        if not domain or "search.brave.com" in domain:
            continue
        if url in seen:
            continue
        seen.add(url)
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        sources.append(
            {
                "title": title,
                "url": url,
                "snippet": "",
                "domain": domain,
            }
        )
    return sources


def search_sources(query: str, max_results: int = 10, timeout: int = 15) -> List[Dict[str, str]]:
    """Search result candidates with provider fallback."""
    q = (query or "").strip()
    if not q:
        return []

    sources = _search_ddg(q, max_results=max_results, timeout=timeout)
    if sources:
        return sources

    sources = _search_bing(q, max_results=max_results, timeout=timeout)
    if sources:
        return sources

    return _search_brave(q, max_results=max_results, timeout=timeout)


def fetch_page_text(url: str, timeout: int = 15, max_chars: int = 8000) -> Dict[str, str]:
    """Fetch and extract readable text from a web page."""
    out = {"title": "", "text": "", "url": url}
    if not url:
        return out

    try:
        response = requests.get(url, headers=_HEADERS, timeout=timeout)
        response.raise_for_status()
    except Exception:
        return out

    content_type = (response.headers.get("Content-Type") or "").lower()
    if "text/html" not in content_type:
        return out

    soup = BeautifulSoup(response.text, "html.parser")

    if soup.title:
        out["title"] = _clean_text(soup.title.get_text(" ", strip=True))

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "aside"]):
        tag.decompose()

    candidates: List[str] = []
    for selector in ("article", "main", "[role='main']", ".post-content", ".entry-content", ".article-content"):
        for node in soup.select(selector):
            text = _clean_text(node.get_text(" ", strip=True))
            if len(text) >= 200:
                candidates.append(text)

    if not candidates:
        paragraphs = []
        for p in soup.select("p"):
            text = _clean_text(p.get_text(" ", strip=True))
            if len(text) >= 50:
                paragraphs.append(text)
        if paragraphs:
            candidates.append(_clean_text(" ".join(paragraphs)))

    if candidates:
        extracted = max(candidates, key=len)
        out["text"] = extracted[:max_chars]

    return out


def _rank_originality(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not items:
        return items

    domain_count: Dict[str, int] = {}
    for item in items:
        d = item.get("domain", "")
        domain_count[d] = domain_count.get(d, 0) + 1

    token_sets = [_tokenize(item.get("text", "") or item.get("snippet", "")) for item in items]

    for i, item in enumerate(items):
        sims = []
        for j, other_tokens in enumerate(token_sets):
            if i == j:
                continue
            sims.append(_jaccard(token_sets[i], other_tokens))

        avg_sim = sum(sims) / len(sims) if sims else 0.0
        domain_bonus = 1.0 / float(domain_count.get(item.get("domain", ""), 1))
        text_bonus = min(1.0, len(item.get("text", "")) / 3000.0)
        score = (1.0 - avg_sim) * 0.65 + domain_bonus * 0.2 + text_bonus * 0.15
        item["originality_score"] = round(score, 3)

    items.sort(key=lambda x: x.get("originality_score", 0.0), reverse=True)
    return items


def _summary(text: str, max_chars: int = 240) -> str:
    t = _clean_text(text)
    if not t:
        return ""
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 3] + "..."


def run_research(
    query: str,
    max_results: int = 10,
    top_k: int = 5,
    site_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Research pipeline:
    - search sources
    - fetch article text
    - rank by originality score
    """
    q = _clean_text(query)
    if not q:
        return {
            "query": "",
            "items": [],
            "report_text": "Pesquisa vazia. Nenhum resultado.",
        }

    search_query = q
    if site_hint and site_hint in _SITE_TO_DOMAIN:
        domain = _SITE_TO_DOMAIN[site_hint]
        if f"site:{domain}" not in search_query:
            search_query = f"{search_query} site:{domain}"

    candidates = search_sources(search_query, max_results=max_results * 2)
    if not candidates:
        return {
            "query": search_query,
            "items": [],
            "report_text": f"Nao foi possivel obter resultados para: {search_query}",
        }

    enriched: List[Dict[str, Any]] = []
    for cand in candidates:
        if len(enriched) >= max_results:
            break
        page = fetch_page_text(cand["url"])
        text = page.get("text") or cand.get("snippet") or ""
        if len(_clean_text(text)) < 80:
            continue
        enriched.append(
            {
                "title": page.get("title") or cand.get("title") or cand["url"],
                "url": cand["url"],
                "domain": cand.get("domain") or _domain(cand["url"]),
                "snippet": cand.get("snippet", ""),
                "text": text,
            }
        )

    if not enriched:
        enriched = [
            {
                "title": c.get("title") or c["url"],
                "url": c["url"],
                "domain": c.get("domain") or _domain(c["url"]),
                "snippet": c.get("snippet", ""),
                "text": c.get("snippet", ""),
            }
            for c in candidates[:max_results]
        ]

    ranked = _rank_originality(enriched)
    selected = ranked[: max(1, top_k)]

    lines = [
        f"Relatorio de pesquisa - {datetime.now().isoformat(timespec='seconds')}",
        f"Consulta: {search_query}",
        f"Fontes analisadas: {len(ranked)}",
        f"Top fontes por originalidade estimada: {len(selected)}",
        "",
    ]

    for i, item in enumerate(selected, 1):
        lines.append(f"{i}. {item.get('title', 'Sem titulo')}")
        lines.append(f"   URL: {item.get('url', '')}")
        lines.append(f"   Fonte: {item.get('domain', '')}")
        lines.append(f"   Originalidade: {item.get('originality_score', 0.0):.3f}")
        highlight = _summary(item.get("text") or item.get("snippet") or "", max_chars=260)
        if highlight:
            lines.append(f"   Destaque: {highlight}")
        lines.append("")

    report_text = "\n".join(lines).strip()
    return {"query": search_query, "items": selected, "report_text": report_text}


__all__ = ["run_research"]
