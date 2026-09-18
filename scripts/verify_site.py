#!/usr/bin/env python3
"""Site-owned verifier for the built CISO-in-a-Box site.

Inventories every built ``index.html`` under --build-root, validates
every configured internal route (navbar, homepage pathways, modules)
against that inventory, validates the built machine-readable layer
(markdown peers, manifest.json, search-index.json, llms.txt, sitemap.xml,
robots.txt, absence of noindex), validates the generated Skill artifacts
(public Skill files, deterministic skill.zip, the /use-with-ai/ page),
then HTTP-checks each path against a server serving the site under its
configured base URL.

The built manifest.json is the machine-readable declaration of expected
pages and Markdown peers; no content-repository checkout is needed.

Usage:
    python scripts/verify_site.py --build-root _site \\
        --base-url http://127.0.0.1:8765 \\
        --source-commit <40-character SHA>
"""

from __future__ import annotations

import argparse
import html
import http.client
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_config import (
    GITHUB_REPO_URL,
    HOMEPAGE_MODULES,
    NAVBAR_CONFIG,
    PATHWAY_CARDS,
    SITE_BASEURL,
    SKILL_DIR,
    SKILL_ENDPOINTS_PUBLIC_PATH,
    SKILL_MD_PUBLIC_PATH,
    SKILL_NAME,
    SKILL_YAML_PUBLIC_PATH,
    SKILL_ZIP_PUBLIC_PATH,
    USE_WITH_AI_ROUTE,
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
        marker = "OK  " if actual == expected else "FAIL"
        if not isinstance(actual, (int, tuple)) and len(repr(actual)) > 80:
            print(f"{marker} {message}")
            print(f"     (actual {repr(actual)[:60]}...)")
            if actual != expected:
                print(f"     (expected {repr(expected)[:60]}...)")
        else:
            print(f"{marker} {message} (got {actual!r}, expected {expected!r})")
        if actual != expected:
            self.failures.append(message)


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
        # Route-style targets (/use-with-ai/) resolve to their index.html.
        if asset.is_dir():
            asset = asset / "index.html"
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

    skill_routes = [u for u in sitemap_routes if u.startswith("/skill/")]
    report.check(
        not skill_routes,
        f"raw Skill artifacts are not listed in the sitemap (found: {skill_routes})",
    )


def verify_skill_files(build_root: Path, source_commit: str, report: Report) -> dict[str, str]:
    """Validate the built public Skill files; returns their contents."""
    paths = {
        "SKILL.md": build_root / SKILL_DIR / "SKILL.md",
        "agents/openai.yaml": build_root / SKILL_DIR / "agents" / "openai.yaml",
        "references/endpoints.md": build_root / SKILL_DIR / "references" / "endpoints.md",
    }
    contents: dict[str, str] = {}
    for rel, path in sorted(paths.items()):
        report.check(path.is_file(), f"built skill file exists: {rel}")
        if not path.is_file():
            raise VerifyError(f"missing built skill file: {rel}")
        contents[rel] = path.read_text(encoding="utf-8")

    skill_md = contents["SKILL.md"]
    lines = skill_md.splitlines()
    report.check(lines and lines[0] == "---", "SKILL.md starts with YAML front matter")
    if not (lines and lines[0] == "---"):
        raise VerifyError("SKILL.md has no front matter")
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        end = -1
    report.check(end > 0, "SKILL.md front matter closes")
    fm_lines = lines[1:end] if end > 0 else []
    fm_keys = [ln.split(":", 1)[0].strip() for ln in fm_lines if ln.strip()]
    report.check_eq(fm_keys, ["name", "description"], "SKILL.md front matter keys are exactly name and description")
    name = next(ln for ln in fm_lines if ln.startswith("name:"))
    report.check_eq(name.removeprefix("name:").strip(), SKILL_NAME, "SKILL.md name")
    description = next(ln for ln in fm_lines if ln.startswith("description:"))
    report.check(bool(description.removeprefix("description:").strip()), "SKILL.md description is non-empty")
    body = "\n".join(lines[end + 1 :]).strip()
    report.check(bool(body), "SKILL.md body is non-empty")
    report.check(
        len(lines) <= 120,
        f"SKILL.md stays compact ({len(lines)} lines, expected <= 120)",
    )
    # Live endpoints appear once as navigation facts, not duplicated.
    for label, url in (
        ("llms.txt", public_url("/llms.txt")),
        ("manifest.json", public_url("/manifest.json")),
        ("search-index.json", public_url("/search-index.json")),
    ):
        count = skill_md.count(url)
        report.check(count == 1, f"SKILL.md references {label} exactly once (found {count})")
    report.check(
        public_url("/markdown/") in skill_md,
        "SKILL.md points at the Markdown peer namespace",
    )

    yaml_text = contents["agents/openai.yaml"]
    report.check("interface:" in yaml_text, "openai.yaml contains an interface mapping")
    report.check("display_name:" in yaml_text, "openai.yaml contains display_name")
    report.check("short_description:" in yaml_text, "openai.yaml contains short_description")

    endpoints = contents["references/endpoints.md"]
    for label, needle in (
        ("canonical site URL", public_site_root() + "/"),
        ("llms.txt URL", public_url("/llms.txt")),
        ("manifest.json URL", public_url("/manifest.json")),
        ("search-index.json URL", public_url("/search-index.json")),
        ("markdown peer namespace", public_url("/markdown/")),
        ("source repository", GITHUB_REPO_URL),
        ("exact source SHA", source_commit),
    ):
        report.check(needle in endpoints, f"endpoints.md contains the {label}")
    return contents


def verify_skill_zip(build_root: Path, published: dict[str, str], report: Report) -> None:
    """Validate the deterministic skill.zip against the published files."""
    zip_path = build_root / SKILL_DIR / "skill.zip"
    report.check(zip_path.is_file(), "built skill.zip exists")
    if not zip_path.is_file():
        raise VerifyError("missing built skill.zip")
    try:
        archive = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        raise VerifyError(f"skill.zip does not parse: {exc}") from exc

    names = archive.namelist()
    expected = [f"{SKILL_NAME}/{rel}" for rel in sorted(published)]
    report.check_eq(sorted(names), expected, "skill.zip member inventory is exact")
    report.check(
        all(not n.startswith("/") and ".." not in Path(n).parts for n in names),
        "skill.zip members have no absolute or traversal paths",
    )
    for rel, text in sorted(published.items()):
        embedded = archive.read(f"{SKILL_NAME}/{rel}").decode("utf-8")
        report.check_eq(embedded, text, f"skill.zip embeds {rel} byte-identically")
    report.check(
        f"{SKILL_NAME}/skill.zip" not in names,
        "skill.zip does not embed itself",
    )
    for info in archive.infolist():
        report.check_eq(
            info.date_time,
            (1980, 1, 1, 0, 0, 0),
            f"skill.zip member {info.filename} has the fixed timestamp",
        )


def _extract_code_block(page_html: str, block_id: str) -> str | None:
    """Decode the exact text of a rouge-rendered copy block."""
    match = re.search(
        rf'<div id="{re.escape(block_id)}"[^>]*>.*?<code>(.*?)</code></pre></div>',
        page_html,
        re.S,
    )
    return html.unescape(match.group(1)) if match else None


def verify_use_with_ai_page(build_root: Path, skill_md: str, report: Report) -> None:
    """Validate the built /use-with-ai/ page against the Skill artifacts."""
    page_path = build_root / "use-with-ai" / "index.html"
    report.check(page_path.is_file(), "built /use-with-ai/ page exists")
    if not page_path.is_file():
        raise VerifyError("missing built /use-with-ai/ page")
    page = page_path.read_text(encoding="utf-8")

    def href_exists(path: str) -> bool:
        direct = f'href="{public_url(path)}"'
        relative = f'href="{SITE_BASEURL.rstrip("/")}{path}"'
        liquid = f"href=\"{{{{ '{path.lstrip('/')}' | relative_url }}}}\""
        return direct in page or relative in page or liquid in page

    report.check(href_exists(SKILL_ZIP_PUBLIC_PATH), "/use-with-ai/ links to skill.zip")
    report.check(href_exists(SKILL_MD_PUBLIC_PATH), "/use-with-ai/ links to the published SKILL.md")

    block = _extract_code_block(page, "skill-definition")
    report.check(block is not None, "/use-with-ai/ contains the SKILL.md display block")
    if block is not None:
        report.check_eq(block, skill_md, "/use-with-ai/ SKILL.md display block equals the published SKILL.md")

    bootstrap = _extract_code_block(page, "bootstrap-prompt")
    report.check(bootstrap is not None, "/use-with-ai/ contains the bootstrap prompt block")
    if bootstrap is not None:
        for needle in (public_url("/llms.txt"), public_url("/manifest.json"), public_url("/search-index.json")):
            report.check(needle in bootstrap, f"bootstrap prompt contains {needle}")

    coding = _extract_code_block(page, "coding-agent-prompt")
    report.check(coding is not None, "/use-with-ai/ contains the coding-agent prompt block")
    if coding is not None:
        report.check(public_url(SKILL_ZIP_PUBLIC_PATH) in coding, "coding-agent prompt contains the public skill.zip URL")

    report.check(
        'data-copy-target="skill-definition"' in page and "copy-btn" in page,
        "/use-with-ai/ provides copy controls",
    )

    home = (build_root / "index.html").read_text(encoding="utf-8")
    report.check(
        "/use-with-ai/" in home and "Use with AI" in home,
        "homepage links to /use-with-ai/",
    )


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
        skill_contents = verify_skill_files(build_root, source_commit, report)
        verify_skill_zip(build_root, skill_contents, report)
        verify_use_with_ai_page(build_root, skill_contents["SKILL.md"], report)
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
    add("use-with-ai page", USE_WITH_AI_ROUTE)
    add("skill SKILL.md", SKILL_MD_PUBLIC_PATH)
    add("skill openai.yaml", SKILL_YAML_PUBLIC_PATH)
    add("skill endpoints.md", SKILL_ENDPOINTS_PUBLIC_PATH)
    add("skill.zip", SKILL_ZIP_PUBLIC_PATH)
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