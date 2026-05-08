#!/usr/bin/env python3
"""Fetch initial HTML and stylesheet evidence for a website URL."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stylesheets: list[str] = []
        self.scripts: list[str] = []
        self.assets: list[str] = []
        self.anchors: list[str] = []
        self.route_hints: list[dict] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "link" and values.get("rel"):
            rel = " ".join(values.get("rel", "").split()).lower()
            href = values.get("href")
            if href and "stylesheet" in rel:
                self.stylesheets.append(href)
            elif href and any(token in rel for token in ["canonical", "alternate", "sitemap"]):
                self.route_hints.append({"url": href, "source": f"link rel={rel}"})
        if tag == "a" and values.get("href"):
            self.anchors.append(values["href"])
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])
        if tag in {"img", "source", "video"}:
            src = values.get("src") or values.get("srcset")
            if src:
                self.assets.append(src)


def fetch(url: str, timeout: int = 20) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 web-style-skill-maker"})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        return response.read(), content_type


def fetch_text(url: str, timeout: int = 8) -> str:
    data, _ = fetch(url, timeout=timeout)
    return data.decode("utf-8", errors="replace")


def safe_name(url: str, fallback: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/") or fallback
    name = re.sub(r"[^a-zA-Z0-9._-]+", "-", path).strip("-")
    if not name:
        name = fallback
    if "." not in Path(name).name:
        name = f"{name}.css"
    return name[:120]


def html_name(url: str, fallback: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/") or fallback
    name = re.sub(r"[^a-zA-Z0-9._-]+", "-", path).strip("-") or fallback
    if "." in Path(name).name:
        name = Path(name).stem
    return f"{name[:110]}.html"


def same_origin(base: str, candidate: str) -> bool:
    base_host = urlparse(base).netloc
    candidate_host = urlparse(candidate).netloc
    return not candidate_host or candidate_host == base_host


def canonical_route(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return parsed._replace(path=path, params="", query="", fragment="").geturl()


def route_bucket(url: str) -> str:
    path = urlparse(url).path.lower().strip("/")
    if not path:
        return "home"
    if re.search(r"(pricing|plans|billing)", path):
        return "pricing"
    if re.search(r"(product|features?|platform|solutions?)", path):
        return "product"
    if re.search(r"(docs?|developers?|api|guides?|learn)", path):
        return "docs"
    if re.search(r"(blog|news|articles?|stories)", path):
        return "blog"
    if re.search(r"(customers?|case-stud|showcase|work)", path):
        return "case-study"
    if re.search(r"(about|company|team|careers?)", path):
        return "company"
    if re.search(r"(contact|support|help)", path):
        return "contact"
    if re.search(r"(events?|campaign|conference|webinar)", path):
        return "campaign"
    return "other"


def unsafe_route(url: str) -> str:
    path = urlparse(url).path.lower()
    if re.search(r"/(login|log-in|signin|sign-in|signup|sign-up|auth|account|dashboard|admin)(/|$)", path):
        return "private/auth route skipped"
    if re.search(r"/(checkout|cart|billing|payment)(/|$)", path):
        return "transaction route skipped"
    if urlparse(url).query:
        return "query-heavy route skipped"
    if re.search(r"\.(pdf|zip|png|jpe?g|gif|webp|svg|mp4|mov|css|js|json|xml)$", path):
        return "asset route skipped"
    return ""


def priority_for(url: str, source: str) -> int:
    bucket = route_bucket(url)
    scores = {
        "home": 100,
        "product": 92,
        "pricing": 90,
        "campaign": 86,
        "case-study": 82,
        "docs": 76,
        "blog": 72,
        "company": 68,
        "contact": 60,
        "other": 45,
    }
    score = scores.get(bucket, 40)
    if "sitemap" in source:
        score -= 4
    if len(urlparse(url).path.strip("/").split("/")) > 3:
        score -= 12
    return max(score, 1)


def add_candidate(candidates: dict, base_url: str, href: str, source: str) -> None:
    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
        return
    absolute = canonical_route(urljoin(base_url, href))
    if not same_origin(base_url, absolute):
        return
    if absolute not in candidates:
        blocked = unsafe_route(absolute)
        candidates[absolute] = {
            "url": absolute,
            "source": source,
            "archetype": route_bucket(absolute),
            "priority": priority_for(absolute, source),
            "decision": "skipped" if blocked else "candidate",
            "reason": blocked or "same-site public route candidate",
        }


def discover_sitemap_routes(base_url: str, candidates: dict, max_sitemaps: int = 3) -> list[str]:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    sitemap_urls = [urljoin(origin, "/sitemap.xml")]
    methods = []
    try:
        robots = fetch_text(urljoin(origin, "/robots.txt"))
        for line in robots.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_urls.append(line.split(":", 1)[1].strip())
        methods.append("robots sitemap")
    except Exception:
        pass

    seen = set()
    for sitemap_url in sitemap_urls[:max_sitemaps]:
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        try:
            sitemap = fetch_text(sitemap_url)
        except Exception:
            continue
        methods.append("sitemap.xml")
        for loc in re.findall(r"<loc>\s*([^<]+)\s*</loc>", sitemap, flags=re.I):
            if loc.strip().lower().endswith(".xml"):
                continue
            add_candidate(candidates, base_url, loc.strip(), "sitemap")
    return methods


def select_routes(candidates: dict, max_routes: int) -> tuple[list[dict], list[dict]]:
    public = [item for item in candidates.values() if item["decision"] == "candidate"]
    public.sort(key=lambda item: (-int(item["priority"]), len(urlparse(item["url"]).path), item["url"]))
    selected = []
    selected_urls = set()

    for bucket in ["home", "product", "pricing", "campaign", "case-study", "docs", "blog", "company", "contact", "other"]:
        for item in public:
            if item["archetype"] == bucket and item["url"] not in selected_urls:
                selected.append({**item, "decision": "selected", "tier": "A" if len(selected) < 5 else "B"})
                selected_urls.add(item["url"])
                break
        if len(selected) >= max_routes:
            break

    for item in public:
        if len(selected) >= max_routes:
            break
        if item["url"] not in selected_urls:
            selected.append({**item, "decision": "selected", "tier": "B" if len(selected) < 10 else "C"})
            selected_urls.add(item["url"])

    skipped = []
    for item in candidates.values():
        if item["url"] in selected_urls:
            continue
        reason = item["reason"] if item["decision"] == "skipped" else "duplicate or lower-priority route after budget"
        skipped.append({**item, "decision": item["decision"] if item["decision"] == "skipped" else "duplicate", "reason": reason})
    return selected, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture source evidence for a website.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True, help="Output evidence directory, usually front-site/evidence")
    parser.add_argument("--allow-cross-origin-css", action="store_true")
    parser.add_argument("--max-routes", type=int, default=12, help="Maximum representative same-site routes to select for the inventory")
    parser.add_argument("--fetch-selected-routes", action="store_true", help="Also fetch HTML for selected representative routes")
    args = parser.parse_args()

    out = Path(args.out).expanduser().resolve()
    source_dir = out / "source"
    css_dir = out / "css"
    routes_dir = out / "routes"
    source_dir.mkdir(parents=True, exist_ok=True)
    css_dir.mkdir(parents=True, exist_ok=True)
    routes_dir.mkdir(parents=True, exist_ok=True)

    html_bytes, content_type = fetch(args.url)
    html = html_bytes.decode("utf-8", errors="replace")
    html_path = source_dir / "index.html"
    html_path.write_text(html, encoding="utf-8", newline="\n")

    parser_obj = LinkParser()
    parser_obj.feed(html)

    candidates: dict[str, dict] = {}
    add_candidate(candidates, args.url, args.url, "seed url")
    parsed = urlparse(args.url)
    add_candidate(candidates, args.url, f"{parsed.scheme}://{parsed.netloc}/", "root page")
    for href in parser_obj.anchors:
        add_candidate(candidates, args.url, href, "anchor")
    for hint in parser_obj.route_hints:
        add_candidate(candidates, args.url, hint["url"], hint["source"])
    discovery_methods = ["seed url", "root page", "anchors"]
    discovery_methods.extend(discover_sitemap_routes(args.url, candidates))
    selected_routes, skipped_routes = select_routes(candidates, max(1, min(args.max_routes, 12)))

    css_files = []
    css_failures = []
    for index, href in enumerate(parser_obj.stylesheets):
        absolute = urljoin(args.url, href)
        if not args.allow_cross_origin_css and not same_origin(args.url, absolute):
            css_failures.append({"url": absolute, "reason": "cross-origin skipped"})
            continue
        try:
            css_bytes, _ = fetch(absolute)
            css_path = css_dir / safe_name(absolute, f"stylesheet-{index + 1}.css")
            css_path.write_bytes(css_bytes)
            css_files.append({"url": absolute, "path": str(css_path.relative_to(out.parent))})
        except Exception as error:
            css_failures.append({"url": absolute, "reason": str(error)})

    route_files = []
    if args.fetch_selected_routes:
        for index, route in enumerate(selected_routes):
            route_url = route["url"]
            if canonical_route(route_url) == canonical_route(args.url):
                continue
            try:
                route_bytes, route_type = fetch(route_url, timeout=12)
                route_path = routes_dir / html_name(route_url, f"route-{index + 1}")
                route_path.write_bytes(route_bytes)
                route_files.append({
                    "url": route_url,
                    "content_type": route_type,
                    "path": str(route_path.relative_to(out.parent)),
                    "archetype": route.get("archetype", "route"),
                    "tier": route.get("tier", "B"),
                })
            except Exception as error:
                route_files.append({
                    "url": route_url,
                    "error": str(error),
                    "archetype": route.get("archetype", "route"),
                    "tier": route.get("tier", "B"),
                })

    coverage_level = "site-level" if len(selected_routes) >= 4 else ("partial-site" if len(selected_routes) > 1 else "page-level")
    page_inventory = {
        "entry_url": args.url,
        "canonical_origin": f"{parsed.scheme}://{parsed.netloc}",
        "coverage_level": coverage_level,
        "route_budget": {
            "selected_default": "6-10",
            "hard_cap": 12,
            "actual_selected": len(selected_routes),
        },
        "discovery_methods": sorted(set(discovery_methods)),
        "candidate_routes": list(candidates.values())[:80],
        "selected_routes": selected_routes,
        "skipped_route_classes": skipped_routes[:40],
        "stop_reason": "route budget reached" if len(selected_routes) >= min(args.max_routes, 12) else "public route candidates exhausted",
        "coverage_summary": f"Selected {len(selected_routes)} representative public route(s) from {len(candidates)} candidate(s). Treat as {coverage_level} evidence.",
    }
    inventory_path = out.parent / "references" / "page-inventory.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(json.dumps(page_inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    source_map = {
        "url": args.url,
        "content_type": content_type,
        "page_inventory": str(inventory_path.relative_to(out.parent)),
        "selected_routes": selected_routes,
        "route_files": route_files,
        "html_files": [str(html_path.relative_to(out.parent))],
        "css_files": css_files,
        "css_failures": css_failures,
        "script_files": [urljoin(args.url, src) for src in parser_obj.scripts],
        "asset_files": [urljoin(args.url, src.split()[0]) for src in parser_obj.assets],
    }
    map_path = out.parent / "references" / "source-map.json"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps(source_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(map_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
