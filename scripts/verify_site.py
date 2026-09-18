#!/usr/bin/env python3
"""Site-owned verifier for the built CISO-in-a-Box site.

Inventories every built ``index.html`` under --build-root, validates
every configured internal route (navbar, homepage pathways, modules)
against that inventory, validates the built machine-readable layer
(markdown peers, manifest.json, search-index.json, llms.txt, sitemap.xml,
robots.txt, absence of noindex), then HTTP-checks each path against a
server serving the site under its configured base URL.

The built manifest.json is the machine-readable declaration of expected
pages and Markdown peers; no content-repository checkout is needed.

Usage:
    python scripts/verify_site.py --build-root _site \\
        --base-url http://127.0.0.1:8765 \\
        --source-commit <40-character SHA>
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_config import (
    GITHUB_REPO_URL,
    HOMEPAGE_MODULES,
    NAVBAR_CONFIG,
    PATHWAY_CARDS,
    SITE_BASEURL,
    public_site_root,
    public_url,
)

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class VerifyError(RuntimeError):
    """Fatal verification error."""


def configured_internal_routes() -> list[str]:
    """Internal routes the curated presentation references."""
    routes: set[str] = set()
    for card in PATHWAY_CARDS:
        routes.add(card["link_route"])
    for module in HOMEPAGE_MODULES:
        routes.add(module["route"])
    for group in NAVBAR_CONFIG:
        for item in group["items"]:
            if "route" in item:
                routes.add(item["route"])
    return sorted(routes)


def built_site_paths(build_root: Path) -> list[str]:
    """Baseurl-relative directory routes for each built index.html."""
    paths: set[str] = set()
    for html in build_root.rglob("index.html"):
        rel = html.relative_to(build_root).parent.as_posix()
        paths.add("/" if rel == "." else f"/{rel}/")
    return sorted(paths)


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def check(self, ok: bool, message: str) -> None:
        marker = "OK  " if ok else "FAIL"
        print(f"{marker} {message}")
        if not ok:
            self.failures.append(message)

    def check_eq(self, actual, expected, message: str) -> None:
        self.check(actual == expected, f"{message} (got {actual!r}, expected {expected!r})")


def load_json(build_root: Path, name: str, report: Report):
    path = build_root / name
    report.check(path.is_file(), f"{name} exists")
    if not path.is_file():
        raise VerifyError(f"missing required artifact: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VerifyError(f"{name} is not valid JSON: {exc}") from exc


def verify_manifest(build_root: Path, source_commit: str, report: Report) -> dict:
    manifest = load_json(build_root, "manifest.json", report)

    report.check_eq(manifest.get("source_repository"), GITHUB_REPO_URL, "manifest source_repository")
    report.check_eq(manifest.get("source_commit"), source_commit, "manifest source_commit")
    report.check_eq(manifest.get("site_url"), public_site_root(), "manifest site_url")

    pages = manifest.get("pages")
    report.check(isinstance(pages, list) and bool(pages), "manifest has a non-empty pages array")
    if not isinstance(pages, list):
        raise VerifyError("manifest pages is not a list")

    html_urls = [p.get("html_url") for p in pages]
    md_urls = [p.get("markdown_url") for p in pages]
    report.check(len(html_urls) == len(set(html_urls)), "manifest html_url values are unique")
    report.check(len(md_urls) == len(set(md_urls)), "manifest markdown_url values are unique")
    report.check(
        all(u and u.startswith(public_site_root() + "/") for u in html_urls + md_urls),
        "manifest URLs use the configured canonical site URL",
    )

    ordered = [p.get("html_url") for p in pages]
    report.check(ordered == sorted(ordered), "manifest pages are deterministically ordered by html_url")

    for entry in pages:
        missing = [
            key
            for key in ("title", "description", "source_path", "html_url", "markdown_url", "section")
            if key not in entry
        ]
        if missing:
            report.check(False, f"manifest entry {entry.get('title')!r} missing fields: {missing}")
            break
    else:
        report.check(True, "manifest entries have all required fields")

    site_root = public_site_root() + "/"
    for entry in pages:
        peer = build_root / entry["markdown_url"].removeprefix(site_root)
        if not peer.is_file():
            report.check(False, f"manifest references missing markdown peer: {peer}")
            break
    else:
        report.check(True, "all manifest markdown peers exist on disk")

    # Manifest content pages must match the built canonical HTML routes.
    manifest_routes = {u.removeprefix(public_site_root()) for u in html_urls}
    built = set(built_site_paths(build_root))
    missing_built = sorted(manifest_routes - built)
    report.check(not missing_built, f"manifest pages all have built HTML routes (missing: {missing_built})")
    return manifest


def verify_search_index(build_root: Path, manifest: dict, source_commit: str, report: Report) -> list[dict]:
    index = load_json(build_root, "search-index.json", report)
    report.check(isinstance(index, list) and bool(index), "search-index is a non-empty array")
    if not isinstance(index, list):
        raise VerifyError("search index is not a list")

    manifest_routes = {p["html_url"] for p in manifest["pages"]}
    index_routes = [r.get("html_url") for r in index]
    report.check(
        sorted(index_routes) == sorted(manifest_routes),
        "search-index records correspond to manifest content pages",
    )
    report.check(len(index_routes) == len(set(index_routes)), "search-index has no duplicate canonical routes")
    report.check(
        all(r.get("source_commit") == source_commit for r in index),
        "search-index source_commit values match",
    )

    for record in index:
        missing = [
            key
            for key in (
                "title", "description", "html_url", "markdown_url",
                "source_path", "source_commit", "section", "headings", "text",
            )
            if key not in record
        ]
        if missing:
            report.check(False, f"search-index record missing fields: {missing}")
            break
    else:
        report.check(True, "search-index records have all required fields")

    ordered = [r.get("html_url") for r in index]
    report.check(ordered == sorted(ordered), "search-index records are deterministically ordered")
    return index


def verify_llms_txt(build_root: Path, manifest: dict, source_commit: str, report: Report) -> None:
    path = build_root / "llms.txt"
    report.check(path.is_file(), "llms.txt exists")
    if not path.is_file():
        raise VerifyError("missing llms.txt")
    text = path.read_text(encoding="utf-8")

    report.check(source_commit in text, "llms.txt contains the exact source commit")

    markdown_urls = re.findall(r"\((https?://[^)]+)\)", text)
    missing = [u for u in markdown_urls if not u.startswith(public_site_root() + "/")]
    report.check(not missing, f"llms.txt links use the canonical public site URL (bad: {missing})")

    local_targets = [u.removeprefix(public_site_root()) for u in markdown_urls]
    absent = []
    for target in local_targets:
        asset = build_root / target.lstrip("/")
        if not asset.is_file():
            absent.append(target)
    report.check(not absent, f"llms.txt referenced targets all exist (missing: {absent})")

    manifest_url = public_url("/manifest.json")
    search_url = public_url("/search-index.json")
    report.check(f"({manifest_url})" in text, "llms.txt links the manifest")
    report.check(f"({search_url})" in text, "llms.txt links the search index")

    guide_peers = {u for u in markdown_urls if "/markdown/" in u}
    report.check(
        bool(guide_peers),
        "llms.txt guide section lists markdown peers",
    )
    known_peers = {p["markdown_url"] for p in manifest["pages"]}
    unknown = sorted(guide_peers - known_peers)
    report.check(not unknown, f"llms.txt guide peers are declared in the manifest (unknown: {unknown})")


def verify_markdown_peers(build_root: Path, manifest: dict, source_commit: str, report: Report) -> None:
    peers = build_root / "markdown"
    report.check(peers.is_dir(), "built markdown/ peer directory exists")
    if not peers.is_dir():
        raise VerifyError("missing built markdown/ directory")

    site_root = public_site_root() + "/"
    expected = {}
    for entry in manifest["pages"]:
        rel = entry["markdown_url"].removeprefix(site_root)
        assert rel.startswith("markdown/")
        expected[rel.removeprefix("markdown/")] = entry
    built = {
        p.relative_to(peers).as_posix() for p in peers.rglob("*.md")
    }
    missing_peers = sorted(set(expected) - built)
    orphan_peers = sorted(built - set(expected))
    report.check(
        not missing_peers and not orphan_peers,
        "built peer set matches the manifest declaration "
        f"(missing: {missing_peers}, unexpected: {orphan_peers})",
    )

    bad_peer = None
    for rel, entry in sorted(expected.items()):
        peer = peers / rel
        content = peer.read_text(encoding="utf-8")
        # Raw markdown: no Jekyll front matter may lead the file.
        if content.startswith("---"):
            bad_peer = f"{rel} starts with Jekyll front matter"
            break
        if "{{" in content or "{%" in content:
            bad_peer = f"{rel} contains Liquid tags"
            break
        if f"source_commit: {source_commit}" not in content:
            bad_peer = f"{rel} missing source_commit {source_commit}"
            break
        if not content.startswith("<!-- ciso-in-a-box"):
            bad_peer = f"{rel} missing provenance comment"
            break
    report.check(bad_peer is None, f"peers stay raw markdown with provenance (problem: {bad_peer})")

    site_root = public_site_root() + "/"
    expected = {}


def verify_sitemap(build_root: Path, report: Report) -> None:
    path = build_root / "sitemap.xml"
    report.check(path.is_file(), "sitemap.xml exists")
    if not path.is_file():
        raise VerifyError("missing sitemap.xml")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise VerifyError(f"sitemap.xml is not valid XML: {exc}") from exc

    locs = [el.text or "" for el in root.iter(f"{{{SITEMAP_NS}}}loc")]
    report.check(bool(locs), "sitemap.xml contains URL entries")

    site_root = public_site_root() + "/"
    bad = [u for u in locs if not u.startswith(site_root)]
    report.check(not bad, f"sitemap URLs use the configured SITE_URL/SITE_BASEURL (bad: {bad[:3]})")

    expected_html = set(built_site_paths(build_root))
    sitemap_routes = {"/" + u.removeprefix(site_root) for u in locs}
    missing = sorted(r for r in expected_html if r not in sitemap_routes)
    report.check(not missing, f"expected built canonical HTML pages are in the sitemap (missing: {missing})")


def verify_robots_and_noindex(build_root: Path, report: Report) -> None:
    robots = build_root / "robots.txt"
    report.check(robots.is_file(), "robots.txt exists")
    if robots.is_file():
        text = robots.read_text(encoding="utf-8")
        report.check(
            re.search(r"(?mi)^User-agent:\s*\*\s*$", text) is not None,
            "robots.txt has a User-agent: * rule",
        )
        report.check(
            re.search(r"(?mi)^Allow:\s*/\s*$", text) is not None,
            "robots.txt allows all crawling",
        )
        report.check(
            re.search(r"(?mi)^Disallow:\s*/\s*$", text) is None,
            "robots.txt no longer blocks all crawling",
        )
        report.check(
            public_url("/sitemap.xml") in text,
            "robots.txt advertises the sitemap",
        )

    noindex_hits = [
        html.relative_to(build_root).as_posix()
        for html in build_root.rglob("index.html")
        if re.search(r'name="robots"[^>]*noindex', html.read_text(encoding="utf-8"), re.I)
    ]
    report.check(not noindex_hits, f"no built page emits a noindex robots meta tag (hits: {noindex_hits[:3]})")


def check(base_url: str, path: str) -> tuple[int | str, str]:
    """GET base_url+path; return (status, reason)."""
    url = urllib.parse.urljoin(base_url + "/", path.lstrip("/"))
    parsed = urllib.parse.urlparse(url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=10)
    try:
        conn.request("GET", parsed.path or "/", headers={"Host": parsed.hostname})
        resp = conn.getresponse()
        resp.read()
        return resp.status, resp.reason
    except Exception as exc:
        return f"ERR:{exc}", ""
    finally:
        conn.close()


def main(build_root: Path, base_url: str, source_commit: str) -> int:
    build_root = build_root.resolve()
    if not build_root.is_dir():
        print(f"ERROR: build root not found: {build_root}", file=sys.stderr)
        return 2
    if not SHA1_RE.match(source_commit):
        print(
            f"ERROR: --source-commit must be a full 40-character hex Git SHA, got: {source_commit!r}",
            file=sys.stderr,
        )
        return 2

    base = SITE_BASEURL.rstrip("/")
    report = Report()

    configured = configured_internal_routes()
    built = built_site_paths(build_root)
    if not built:
        print(f"ERROR: no built index.html found under {build_root}", file=sys.stderr)
        return 2

    missing = [route for route in configured if route not in set(built)]
    if missing:
        print(
            "ERROR: configured internal routes missing from the built site:",
            file=sys.stderr,
        )
        for route in missing:
            print(f"  {route}", file=sys.stderr)
        return 2

    print(f"Verifying built site at {build_root}")
    print("-" * 64)

    try:
        manifest = verify_manifest(build_root, source_commit, report)
        verify_search_index(build_root, manifest, source_commit, report)
        verify_llms_txt(build_root, manifest, source_commit, report)
        verify_markdown_peers(build_root, manifest, source_commit, report)
        verify_sitemap(build_root, report)
        verify_robots_and_noindex(build_root, report)
    except VerifyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print("-" * 64)
    print(f"Verifying {len(built) + 5} HTTP paths against {base_url}")
    print("-" * 64)

    check_set: dict[str, str] = {}

    def add(label: str, path: str) -> None:
        path = "/" + path.strip("/")
        full = f"{base}{path}" if path != "/" else (base or "/")
        check_set.setdefault(full, label)

    for route in configured:
        add("configured-route", route)
    for path in built:
        add("built-site", path)

    add("llms.txt", "/llms.txt")
    add("manifest.json", "/manifest.json")
    add("search-index.json", "/search-index.json")
    add("sitemap.xml", "/sitemap.xml")
    add("robots.txt", "/robots.txt")
    site_root = public_site_root() + "/"
    for entry in manifest["pages"]:
        add("markdown-peer", entry["markdown_url"].removeprefix(site_root))

    failures: list[tuple[str, str, int | str, str]] = []
    for path in sorted(check_set):
        label = check_set[path]
        status, reason = check(base_url, path)
        ok = status == 200 or (isinstance(status, int) and 300 <= status < 400)
        marker = "OK " if ok else "FAIL"
        line = f"{marker} {status:>4} {path:<70} [{label}]"
        if ok and status != 200:
            line += f"  -> redirected ({reason})"
        if reason and not ok:
            line += f"  {reason}"
        print(line)
        if not ok:
            failures.append((path, label, status, reason))

    print("-" * 64)
    total = len(check_set)
    passed = total - len(failures)
    print(f"{passed}/{total} pages returned 200 OK")

    if report.failures:
        print(f"\n{len(report.failures)} ARTIFACT FAILURES:")
        for message in report.failures:
            print(f"  {message}")
    if failures:
        print(f"\n{len(failures)} HTTP FAILURES:")
        for path, label, status, reason in failures:
            print(f"  {path} [{label}] -> {status} {reason}")
    if report.failures or failures:
        return 1
    print("All checks OK")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-root",
        type=Path,
        default=Path("_site"),
        help="Directory containing the built site (default: _site)",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8765",
        help="Server serving the site at its configured base URL",
    )
    parser.add_argument(
        "--source-commit",
        required=True,
        help="Full 40-character SHA of the content revision the site was generated from",
    )
    args = parser.parse_args()
    raise SystemExit(main(args.build_root, args.base_url, args.source_commit))