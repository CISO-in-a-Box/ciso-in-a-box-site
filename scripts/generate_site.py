#!/usr/bin/env python3
"""Site-owned generator for the CISO-in-a-Box publishing repository.

Reads authoritative content from an explicit --source-root (a read-only
CroodSolutions/CISOinaBox checkout) and writes Jekyll source into an
explicit --site-root (this publishing repository). Neither root is ever
derived from __file__, the current working directory, or repository
names; the two roots may be nested siblings or independent checkouts.

Content inventory is discovered dynamically from the filesystem:
top-level ``NN - Section Name`` directories, each section README, every
other ``.md`` file beneath a section, and every non-Markdown file as an
asset under ``assets/content/``. Adding a valid Markdown file to a
section makes it publishable without any Python change; no per-section
metadata table exists.

Public routes: a section slug comes from LEGACY_SECTION_ROUTES in
site_config.py when the current public route cannot be derived from the
directory name, otherwise it is derived from the directory name with
the numeric prefix removed. Child routes are derived from the
source-relative path; a nested README's filename never becomes a route
component. Page titles and descriptions are extracted from the content
itself with general algorithms.

Configured presentation routes (navbar, homepage pathways, modules)
are validated against the discovered pages and fail generation if they
do not resolve.

Usage:
    python scripts/generate_site.py --source-root <dir> --site-root <dir>
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_config import (
    GITHUB_BRANCH,
    GITHUB_ORG,
    GITHUB_REPO_URL,
    HOMEPAGE_MODULES,
    LEGACY_SECTION_ROUTES,
    NAVBAR_CONFIG,
    PATHWAY_CARDS,
    SITE_AUTHOR,
    SITE_BASEURL,
    SITE_DESCRIPTION,
    SITE_EMAIL,
    SITE_TITLE,
    SITE_URL,
)

SECTION_DIR_RE = re.compile(r"^(\d+)\s*-\s*(.+)$")
README_NAMES = {"readme.md"}
REPO_PREFIXES = (
    f"{GITHUB_REPO_URL}/blob/{GITHUB_BRANCH}/",
    f"{GITHUB_REPO_URL}/tree/{GITHUB_BRANCH}/",
)
EXCLUDED_SOURCE_DIRS = {"ciso-in-a-box-site", "__pycache__", ".git"}
DEFAULT_DESCRIPTION = "Guidance and reference material from the CISO-in-a-Box repository."
FALLBACK_TITLE = "Untitled Page"


class GenerationError(RuntimeError):
    """Fatal, actionable generation error."""


@dataclass
class Section:
    number: int
    source_title: str
    directory: Path


@dataclass
class Page:
    source_path: Path
    title: str
    permalink: str
    output_path: Path
    description: str
    section: Section | None = None
    is_section_home: bool = False
    related_pages: list["Page"] = field(default_factory=list)
    previous_page: "Page | None" = None
    next_page: "Page | None" = None


# ---- Text helpers ---------------------------------------------------------


def slugify(value: str) -> str:
    value = unquote(value).strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "page"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def strip_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_atx_h1(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") or stripped == "#":
            return strip_markdown(stripped.lstrip("#").strip()) or None
    return None


def first_setext_h1(text: str) -> str | None:
    previous: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if previous is not None and re.fullmatch(r"=+", stripped):
            return strip_markdown(previous) or None
        if stripped and not stripped.startswith(("#", "-", "*", "|", ">", "`")):
            previous = stripped
        else:
            previous = None
    return None


def first_atx_heading(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return strip_markdown(stripped.lstrip("#").strip()) or None
    return None


def title_from_filename(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").strip().title()


def extract_title(source_path: Path, *, is_readme: bool, directory_title: str) -> str:
    text = read_text(source_path)
    h1 = first_atx_h1(text) or first_setext_h1(text)
    if h1:
        return h1
    if is_readme:
        return directory_title
    heading = first_atx_heading(text)
    if heading:
        return heading
    return title_from_filename(source_path) or FALLBACK_TITLE


def remove_first_h1(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("# "):
            del lines[index]
            if index < len(lines) and not lines[index].strip():
                del lines[index]
            break
    return "\n".join(lines).strip() + "\n"


def repair_table_rows(text: str) -> str:
    lines = text.split("\n")
    table_active = False
    pipe_count = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            table_active = False
            continue
        if re.match(r"^\|[\s\-:|]+\|?$", stripped):
            continue
        parts = [p.strip() for p in stripped.split("|") if p.strip() != ""]
        if not table_active:
            table_active = True
            pipe_count = stripped.count("|") - (1 if stripped.endswith("|") else 0)
        if pipe_count > 0 and not stripped.endswith("|"):
            lines[i] = line + " |"
    result = "\n".join(lines)
    result = re.sub(r"(?<!\n)(#{1,6}\s[^\n]+)\n(\|)", r"\1\n\n\2", result)
    result = re.sub(r"\n(#{1,6}\s[^\n]+)\n(\|)", r"\n\1\n\n\2", result)
    return result


def strip_excluded_sections(text: str) -> str:
    patterns = [
        r"\n## Updating the Wiki\n.*$",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "\n", text, flags=re.DOTALL)
    return text.strip() + "\n"


def description_from_text(text: str) -> str:
    cleaned = strip_excluded_sections(remove_first_h1(text))
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
    for paragraph in paragraphs:
        first = paragraph.splitlines()[0].strip()
        if first.startswith(("#", "-", "*", "|", "```")):
            continue
        # Drop setext underlines so a heading never leaks into a description.
        lines = [ln for ln in paragraph.splitlines() if not re.fullmatch(r"[=\-]+", ln.strip())]
        summary = strip_markdown("\n".join(lines))
        if summary:
            return summary[:220].rstrip()
    return DEFAULT_DESCRIPTION


# ---- Discovery -------------------------------------------------------------


def discover_sections(source_root: Path) -> list[Section]:
    sections: list[Section] = []
    for path in source_root.iterdir():
        if not path.is_dir() or path.name in EXCLUDED_SOURCE_DIRS:
            continue
        match = SECTION_DIR_RE.match(path.name)
        if not match:
            continue
        sections.append(Section(int(match.group(1)), match.group(2).strip(), path))
    sections.sort(key=lambda section: section.number)
    numbers = [section.number for section in sections]
    if len(numbers) != len(set(numbers)):
        raise GenerationError(f"Duplicate section numbers discovered: {numbers}")
    return sections


def find_section_readme(section_dir: Path) -> Path | None:
    readme = None
    for child in sorted(
        (p for p in section_dir.iterdir() if p.is_file()),
        key=lambda p: (p.name.lower(), p.name),
    ):
        if child.name.lower() in README_NAMES:
            readme = child
            break
    return readme


def find_markdown_files(section_dir: Path) -> list[Path]:
    return sorted(
        [path for path in section_dir.rglob("*.md") if path.is_file()],
        key=lambda path: (
            len(path.relative_to(section_dir).parts),
            path.as_posix().lower(),
        ),
    )


def section_slug(section: Section) -> str:
    legacy = LEGACY_SECTION_ROUTES.get(section.directory.name)
    if legacy is not None:
        return legacy
    return slugify(section.source_title)


def validate_section_routes(sections: list[Section]) -> None:
    discovered = {section.directory.name for section in sections}
    stale = sorted(set(LEGACY_SECTION_ROUTES) - discovered)
    if stale:
        raise GenerationError(
            "LEGACY_SECTION_ROUTES contains entries that no longer match any "
            "discovered section directory (remove them): " + ", ".join(stale)
        )
    slugs = [section_slug(section) for section in sections]
    duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
    if duplicates:
        raise GenerationError(f"Duplicate section slugs discovered: {duplicates}")


# ---- Page model --------------------------------------------------------------


def build_pages(source_root: Path, site_root: Path) -> tuple[list[Page], list[Page]]:
    docs_root = site_root / "docs"
    sections = discover_sections(source_root)
    validate_section_routes(sections)

    pages: list[Page] = []
    section_pages: list[Page] = []

    for section in sections:
        readme = find_section_readme(section.directory)
        slug = section_slug(section)
        section_page = Page(
            source_path=readme if readme is not None else section.directory,
            title=(
                extract_title(
                    readme, is_readme=True, directory_title=section.source_title
                )
                if readme is not None
                else section.source_title
            ),
            permalink=f"/{slug}/",
            output_path=docs_root / f"{slug}.markdown",
            description=(
                description_from_text(read_text(readme))
                if readme is not None
                else DEFAULT_DESCRIPTION
            ),
            section=section,
            is_section_home=True,
        )
        pages.append(section_page)
        section_pages.append(section_page)

        related: list[Page] = []
        for source_path in find_markdown_files(section.directory):
            if readme is not None and source_path == readme:
                continue
            rel = source_path.relative_to(section.directory)
            relative_parts = rel.with_suffix("").parts
            is_readme = rel.name.lower() in README_NAMES
            if is_readme and len(relative_parts) > 1:
                # A nested README's filename is never a route component.
                slug_parts = [slugify(part) for part in relative_parts[:-1]]
            else:
                slug_parts = [slugify(part) for part in relative_parts]
            # A README page without a usable H1 falls back to the title of
            # the directory containing it, mirroring the section-home rule.
            directory_title = (
                source_path.parent.name
                if is_readme and len(relative_parts) > 1
                else section.source_title
            )
            page = Page(
                source_path=source_path,
                title=extract_title(
                    source_path,
                    is_readme=is_readme,
                    directory_title=directory_title,
                ),
                permalink="/" + "/".join([slug, *slug_parts]) + "/",
                output_path=docs_root.joinpath(*([slug, *slug_parts[:-1]]))
                / f"{slug_parts[-1]}.markdown",
                description=description_from_text(read_text(source_path)),
                section=section,
            )
            pages.append(page)
            related.append(page)

        section_page.related_pages = sorted(
            related, key=lambda page: page.title.lower()
        )

    for index, page in enumerate(section_pages):
        if index > 0:
            page.previous_page = section_pages[index - 1]
        if index < len(section_pages) - 1:
            page.next_page = section_pages[index + 1]

    contributing = source_root / "CONTRIBUTING.md"
    if contributing.exists():
        pages.append(
            Page(
                source_path=contributing,
                title="Contributing",
                permalink="/contributing/",
                output_path=site_root / "contributing.markdown",
                description=description_from_text(read_text(contributing)),
            )
        )

    return pages, section_pages


def build_lookup(pages: list[Page]) -> dict[Path, str]:
    return {page.source_path.resolve(): page.permalink for page in pages}


# ---- Link rewriting ------------------------------------------------------------


def resolve_local_target(
    raw_url: str, base_file: Path, source_root: Path
) -> tuple[Path | None, str | None]:
    if raw_url.startswith(("mailto:", "tel:")):
        return None, None

    split = raw_url.split("#", 1)
    url_without_fragment = split[0]
    fragment = split[1] if len(split) == 2 else None
    decoded = unquote(url_without_fragment)

    for prefix in REPO_PREFIXES:
        if decoded.startswith(prefix):
            rel = decoded.removeprefix(prefix)
            target = source_root / rel
            return target.resolve() if target.exists() else None, fragment

    parsed = urlparse(decoded)
    if parsed.scheme or parsed.netloc:
        return None, None

    if not decoded:
        return None, fragment

    if decoded.startswith("/"):
        target = source_root / decoded.lstrip("/")
    else:
        target = (base_file.parent / decoded).resolve()

    if target.exists():
        return target, fragment

    return None, fragment


def relative_asset_url(source_root: Path, path: Path) -> str:
    rel = path.relative_to(source_root)
    return jekyll_relative_url(
        "/assets/content/" + "/".join(quote(part) for part in rel.parts)
    )


def jekyll_relative_url(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return "{{ '" + path + "' | relative_url }}"


def jekyll_permalink(path: str, fragment: str | None = None) -> str:
    url = jekyll_relative_url(path)
    if fragment:
        return f"{url}#{fragment}"
    return url


def rewrite_links(
    text: str,
    source_path: Path,
    permalink_lookup: dict[Path, str],
    source_root: Path,
) -> str:
    pattern = re.compile(r"(!?\[[^\]]*\]\()([^()]+)(\))")

    def replace(match: re.Match[str]) -> str:
        prefix, raw_url, suffix = match.groups()
        if raw_url.startswith("#"):
            return match.group(0)

        target, fragment = resolve_local_target(raw_url, source_path, source_root)
        if target is None:
            return match.group(0)

        target = target.resolve()
        if target.is_dir():
            for child in target.iterdir():
                if child.is_file() and child.name.lower() in README_NAMES:
                    target = child.resolve()
                    break

        if target in permalink_lookup:
            url = jekyll_permalink(permalink_lookup[target])
        elif target.is_file() and target.suffix.lower() != ".md":
            url = relative_asset_url(source_root, target)
        else:
            return match.group(0)

        if fragment:
            url = f"{url}#{fragment}"
        return f"{prefix}{url}{suffix}"

    return pattern.sub(replace, text)


def autolink_plain_urls(text: str) -> str:
    url_pattern = re.compile(r'(?<!\]\()(?<!")(?P<url>https?://[^\s<]+)')

    def replace(match: re.Match[str]) -> str:
        url = match.group("url")
        trimmed = url.rstrip(".,;:!?)]")
        suffix = url[len(trimmed):]
        return f"<{trimmed}>{suffix}"

    return url_pattern.sub(replace, text)


# ---- Page assembly ----------------------------------------------------------------


def yaml_quote(value: str) -> str:
    return "'" + value.replace("\\", "").replace("'", "''") + "'"


def front_matter(page: Page) -> str:
    lines = [
        "---",
        "layout: page",
        f"title: {yaml_quote(page.title)}",
        f"permalink: {page.permalink}",
        f"share-description: {yaml_quote(page.description)}",
    ]
    if page.section:
        lines.append(f"section_number: {page.section.number}")
    lines.append("---\n")
    return "\n".join(lines)


def build_related_links(page: Page) -> str:
    if not page.related_pages:
        return ""
    lines = ["## Additional Pages in This Section", ""]
    for related in page.related_pages:
        lines.append(f"- [{related.title}]({jekyll_permalink(related.permalink)})")
    return "\n".join(lines) + "\n"


def build_section_pager(page: Page) -> str:
    lines: list[str] = []
    if page.previous_page:
        prev = page.previous_page
        lines.extend(
            [
                "",
                f"Previous: [{prev.section.source_title}]({jekyll_permalink(prev.permalink)})",
            ]
        )
    if page.next_page:
        nxt = page.next_page
        lines.extend(
            [
                "",
                f"Next: [{nxt.section.source_title}]({jekyll_permalink(nxt.permalink)})",
            ]
        )
    return "\n".join(lines) + ("\n" if lines else "")


def build_child_intro(page: Page) -> str:
    assert page.section is not None
    return f"[Back to {page.section.source_title}]({jekyll_permalink(section_slug(page.section))})\n\n"


def copy_assets(source_root: Path, site_root: Path) -> list[Path]:
    assets_root = site_root / "assets" / "content"
    if assets_root.exists():
        shutil.rmtree(assets_root)
    assets_root.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for section in discover_sections(source_root):
        for path in section.directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() == ".md":
                continue
            destination = assets_root / path.relative_to(source_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            copied.append(destination)
    return copied


def sections_cards(section_pages: list[Page]) -> str:
    blocks: list[str] = []
    blocks.extend(["## All Sections", "", '<div class="section-browser-grid">'])
    for page in section_pages:
        count = len(page.related_pages)
        count_text = (
            f"{count} additional page{'s' if count != 1 else ''}"
            if count
            else "Section overview"
        )
        blocks.extend(
            [
                '<a class="section-browser-card" href="%s">'
                % jekyll_permalink(page.permalink),
                '  <div class="section-browser-number">%d</div>' % page.section.number,
                '  <div class="section-browser-body">',
                "    <h3>%s</h3>" % escape(page.section.source_title),
                "    <p>%s</p>" % escape(page.description),
                "    <span>%s</span>" % count_text,
                "  </div>",
                "</a>",
            ]
        )
    blocks.extend(["</div>", ""])
    return "\n".join(blocks).strip() + "\n"


def write_sections_page(section_pages: list[Page], site_root: Path) -> None:
    content = "\n".join(
        [
            "---",
            "layout: page",
            "title: 'Browse All Sections'",
            "permalink: /sections/",
            "share-description: 'Browse all sections of the CISO-in-a-Box content library.'",
            "---",
            "",
            sections_cards(section_pages).strip(),
            "",
        ]
    )
    write_text(site_root / "sections.markdown", content)


def write_contributing_page(
    page: Page, lookup: dict[Path, str], source_root: Path
) -> None:
    body = repair_table_rows(
        autolink_plain_urls(
            rewrite_links(
                strip_excluded_sections(remove_first_h1(read_text(page.source_path))),
                page.source_path,
                lookup,
                source_root,
            )
        )
    )
    write_text(page.output_path, front_matter(page) + body)


def generated_fixed_routes(pages: list[Page]) -> set[str]:
    """Routes of pages the generator itself emits (home and sections)."""
    routes = {"/", "/sections/"}
    routes.update(page.permalink for page in pages)
    return routes


def resolve_route(route: str, pages: list[Page]) -> str:
    known = generated_fixed_routes(pages)
    if route in known:
        return route
    raise GenerationError(
        f"Configured internal route {route!r} does not match any generated page. "
        "Update scripts/site_config.py or check the source content."
    )


def validate_configured_routes(pages: list[Page]) -> None:
    known = generated_fixed_routes(pages)
    routes = set()
    for card in PATHWAY_CARDS:
        routes.add(card["link_route"])
    for module in HOMEPAGE_MODULES:
        routes.add(module["route"])
    for group in NAVBAR_CONFIG:
        for item in group["items"]:
            if "route" in item:
                routes.add(item["route"])
    unknown = sorted(routes - known)
    if unknown:
        raise GenerationError(
            "Configured internal routes do not match any generated page: "
            + ", ".join(unknown)
            + ". Update scripts/site_config.py or check the source content."
        )


def write_config(site_root: Path, pages: list[Page]) -> None:
    navbar_lines: list[str] = []
    for group in NAVBAR_CONFIG:
        navbar_lines.append(f'  "{group["label"]}":')
        for item in group["items"]:
            label = item["label"]
            if item.get("url") == "github":
                navbar_lines.append(f'    - "{label}": "{GITHUB_REPO_URL}"')
            elif "route" in item:
                resolve_route(item["route"], pages)
                navbar_lines.append(f'    - "{label}": "{item["route"]}"')

    start_url = jekyll_relative_url(resolve_route("/getting-started/", pages))
    sections_url = jekyll_relative_url("/sections/")

    pathways_html: list[str] = []
    for card in PATHWAY_CARDS:
        resolve_route(card["link_route"], pages)
        link_url = jekyll_relative_url(card["link_route"])
        topics_html = "\n".join(f"      <li>{t}</li>" for t in card["topics"])
        color = card["color"]
        border_style = f' style="border-top-color: {color};"' if color != "#289dff" else ""
        icon_color_style = f' style="color: {color};"' if color != "#289dff" else ""
        btn_style = f' style="color: {color}; border-color: {color};"' if color != "#289dff" else ""
        pathways_html.extend(
            [
                f'  <div class="pathway-card"{border_style}>',
                f'    <div class="pathway-icon"{icon_color_style}>',
                f'      <i class="{card["icon"]}"></i>',
                "    </div>",
                f'    <div class="pathway-title">{card["title"]}</div>',
                f'    <div class="pathway-desc">',
                f'      {card["description"]}',
                "    </div>",
                '    <ul class="topic-list">',
                topics_html,
                "    </ul>",
                f'    <a href="{link_url}" class="pathway-btn"{btn_style}>',
                f'      {card["title"].removeprefix("The ")} &rarr;</a>',
                "  </div>",
            ]
        )

    modules_html: list[str] = []
    for module in HOMEPAGE_MODULES:
        resolve_route(module["route"], pages)
        module_url = jekyll_relative_url(module["route"])
        modules_html.extend(
            [
                f'  <a href="{module_url}" class="module-card">',
                f'    <div class="module-icon"><i class="{module["icon"]}"></i></div>',
                '    <div class="module-info">',
                f'      <h4>{module["short_title"]}</h4>',
                f'      <span>{module["subtitle"]}</span>',
                "    </div>",
                "  </a>",
            ]
        )

    lines = [
        "###########################################################",
        "### CISOinaBox Jekyll Configuration",
        "",
        f"title: {SITE_TITLE}",
        f"author: {SITE_AUTHOR}",
        f"email: {SITE_EMAIL}",
        "description: >-",
        f"  {SITE_DESCRIPTION}",
        f'baseurl: "{SITE_BASEURL}"',
        f'url: "{SITE_URL}"',
        "",
        "navbar-links:",
        "\n".join(navbar_lines),
        "",
        "remote_theme: daattali/beautiful-jekyll@6.0.1",
        "plugins:",
        "  - jekyll-remote-theme",
        "  - jekyll-include-cache",
        "  - jekyll-feed",
        "  - jekyll-sitemap",
        "  - jekyll-seo-tag",
        "",
        "site-css:",
        '  - "/assets/css/custom.css"',
        "",
        'timezone: "America/Phoenix"',
        "highlighter: rouge",
        "markdown: kramdown",
        "",
        'navbar-col: "#0e0e0e"',
        'navbar-text-col: "#FFFFFF"',
        'navbar-border-col: "#0e0e0e"',
        'page-col: "#FFFFFF"',
        'text-col: "#0e0e0e"',
        'link-col: "#289dff"',
        'hover-col: "#289dff"',
        'footer-col: "#0e0e0e"',
        'footer-text-col: "#FFFFFF"',
        'footer-link-col: "#289dff"',
        'footer-hover-col: "#289dff"',
        "",
        "social-network-links:",
        f"  github: {GITHUB_ORG}",
        "",
        'site-logo: "/assets/img/avatar-icon.png"',
    ]
    write_text(site_root / "_config.yml", "\n".join(lines) + "\n")

    content = "\n".join(
        [
            "---",
            "layout: home",
            'title: "CISO-in-a-Box"',
            'subtitle: "Your Complete Cybersecurity Guide"',
            "permalink: /",
            "head-extra: ",
            "  - custom.html",
            "---",
            "",
            '<div class="hero-section">',
            '  <h1 class="hero-title">The Open Source CISO Guide \U0001f6e1\ufe0f</h1>',
            '  <p class="hero-subtitle">',
            '    From "Day 1" to program maturity. A community-driven framework for building, managing, and scaling modern cybersecurity programs.',
            "  </p>",
            '  <div style="margin-top: 30px;">',
            f'    <a href="{start_url}" class="btn btn-primary btn-lg" style="border-radius: 50px; padding: 12px 30px;">Start the Journey</a>',
            f'    <a href="{sections_url}" class="btn btn-outline-primary btn-lg" style="border-radius: 50px; padding: 12px 30px; margin-left: 10px;">',
            "      Browse Sections",
            "    </a>",
            f'    <a href="{GITHUB_REPO_URL}" class="btn btn-outline-dark btn-lg" style="border-radius: 50px; padding: 12px 30px; margin-left: 10px;">',
            '      <i class="fab fa-github"></i> View Source',
            "    </a>",
            "  </div>",
            "</div>",
            "",
            '<div class="section-header">',
            '  <h2 class="section-title">Choose Your Path</h2>',
            '  <p class="section-desc">Tailored guides depending on where you are in your journey.</p>',
            "</div>",
            "",
            '<div class="pathways-grid">',
            "\n".join(pathways_html),
            "</div>",
            "",
            '<div class="section-header">',
            '  <h2 class="section-title">Core Knowledge Modules</h2>',
            '  <p class="section-desc">Comprehensive guides covering every domain of information security.</p>',
            "</div>",
            "",
            '<div class="modules-grid">',
            "\n".join(modules_html),
            "</div>",
            "",
            '<div class="community-section">',
            "  <h3>Built by the Community, For the Community \U0001f91d</h3>",
            "  <p>",
            "    This project is open source. We believe in sharing knowledge to make the digital world safer.",
            "    <br>Whether you're an expert or just starting, your contribution matters.",
            "  </p>",
            f'  <a href="{GITHUB_REPO_URL}/blob/{GITHUB_BRANCH}/CONTRIBUTING.md" class="community-btn">',
            '    <i class="fas fa-code-branch"></i> Contribute Now',
            "  </a>",
            "</div>",
        ]
    )
    write_text(site_root / "index.markdown", content + "\n")


# ---- Entry point --------------------------------------------------------------


def generate(source_root: Path, site_root: Path) -> None:
    source_root = source_root.resolve()
    site_root = site_root.resolve()
    if not source_root.is_dir():
        raise GenerationError(f"Source root does not exist: {source_root}")

    docs_root = site_root / "docs"
    if docs_root.exists():
        shutil.rmtree(docs_root)
    docs_root.mkdir(parents=True, exist_ok=True)

    pages, section_pages = build_pages(source_root, site_root)
    lookup = build_lookup(pages)
    validate_configured_routes(pages)

    copy_assets(source_root, site_root)
    write_config(site_root, pages)
    write_sections_page(section_pages, site_root)

    for page in pages:
        if page.permalink == "/contributing/":
            write_contributing_page(page, lookup, source_root)
            continue

        if page.source_path.is_file():
            raw_text = read_text(page.source_path)
            body = (
                repair_table_rows(
                    autolink_plain_urls(
                        rewrite_links(
                            strip_excluded_sections(remove_first_h1(raw_text)),
                            page.source_path,
                            lookup,
                            source_root,
                        )
                    )
                ).strip()
                + "\n"
            )
        else:
            # Documented general behavior: a numbered section without a
            # README still gets a section home with navigation only.
            body = ""

        if page.is_section_home:
            body += "\n" + build_related_links(page) + build_section_pager(page)
        elif page.section:
            body = build_child_intro(page) + body
        write_text(page.output_path, front_matter(page) + body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Read-only content checkout (CroodSolutions/CISOinaBox)",
    )
    parser.add_argument(
        "--site-root",
        type=Path,
        required=True,
        help="Publishing repository root to write generated Jekyll source into",
    )
    args = parser.parse_args()
    try:
        generate(args.source_root, args.site_root)
    except GenerationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)