#!/usr/bin/env python3
"""Site-owned verifier for the built CISO-in-a-Box site.

Inventories every built ``index.html`` under --build-root, validates
every configured internal route (navbar, homepage pathways, modules)
against that inventory, then HTTP-checks each path against a server
serving the site under its configured base URL.

Requires no content-repository checkout and no regex parsing of the
generator: route configuration is imported directly from
scripts/site_config.py.

Usage:
    python scripts/verify_site.py --build-root _site \
        --base-url http://127.0.0.1:8765
"""

from __future__ import annotations

import argparse
import http.client
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_config import (
    HOMEPAGE_MODULES,
    NAVBAR_CONFIG,
    PATHWAY_CARDS,
    SITE_BASEURL,
)


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


def main(build_root: Path, base_url: str) -> int:
    build_root = build_root.resolve()
    if not build_root.is_dir():
        print(f"ERROR: build root not found: {build_root}", file=sys.stderr)
        return 2

    base = SITE_BASEURL.rstrip("/")

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

    check_set: dict[str, str] = {}

    def add(label: str, path: str) -> None:
        full = f"{base}{path}" if path != "/" else (base or "/")
        check_set.setdefault(full, label)

    for route in configured:
        add("configured-route", route)
    for path in built:
        add("built-site", path)

    print(f"Verifying {len(check_set)} paths against {base_url}")
    print("-" * 64)

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
    if failures:
        print(f"\n{len(failures)} FAILURES:")
        for path, label, status, reason in failures:
            print(f"  {path} [{label}] -> {status} {reason}")
        return 1
    print("All pages OK")
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
    args = parser.parse_args()
    raise SystemExit(main(args.build_root, args.base_url))