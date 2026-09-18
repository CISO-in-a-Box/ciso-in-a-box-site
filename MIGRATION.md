# Publishing Migration — PR1

Status: **PR1, PR2, and PR3 complete.** The publishing repository owns
site generation, publishing configuration, verification, CI, and the
machine-readable publishing layer. The content repository's publishing
scripts are deleted; the content repository now contains content only
(the `ciso-in-a-box-site` submodule gitlink and `.gitmodules` remain
for now — see deferred work below).

## Ownership

```text
CroodSolutions/CISOinaBox          (content repository — READ-ONLY input)
        |
        | --source-root
        v
CISO-in-a-Box/ciso-in-a-box-site   (publishing repository — owns generation)
        |
        | compile, validate, publish
        v
GitHub Pages site
```

The content repository owns authoritative content. This repository owns
everything else: generation (`scripts/generate_site.py`), publishing
configuration (`scripts/site_config.py`), verification
(`scripts/verify_site.py`), Jekyll presentation, CI/CD, and the
generated publishing artifacts (`docs/`, `assets/content/`,
`_config.yml`, `index.markdown`, `sections.markdown`,
`contributing.markdown`, and the PR3 machine-readable layer:
`markdown/`, `llms.txt`, `manifest.json`, `search-index.json`).

The content-repository copies of `generate_site.py`, `site_config.py`,
and `verify_site.py` were deleted in PR2.

## Machine-readable layer — PR3

The same dynamic discovery and page model now also publishes static
machine-readable artifacts, extending the generator-owned set with
`markdown/`, `llms.txt`, `manifest.json`, and `search-index.json`:

- **Raw Markdown peers** — every source-backed Markdown page gets a
  raw `.md` peer derived deterministically from the canonical HTML
  route (`/foo/bar/` -> `/markdown/foo/bar.md`). Each peer is led by a
  compact provenance comment (canonical URL, source repository, source
  path, exact 40-character source commit) followed by the faithful
  source Markdown. The comment prefix is also what keeps the file raw
  through Jekyll: a peer starting with `---` would be consumed as
  front matter, so provenance and rawness are the same mechanism.
  Internal links in peers are absolute public URLs; no Liquid.
- **`llms.txt`** — concise discovery index at the site root: project
  identity, canonical site URL, authoritative content repository,
  exact source commit, the 22 section-home markdown peers plus
  Contributing, and links to the machine indexes.
- **`manifest.json`** — canonical machine-readable inventory:
  source repository, source commit, site URL, and a deterministically
  route-ordered page array with title, description, source path,
  canonical HTML URL, markdown peer URL, and section number
  (null for non-section pages such as Contributing).
- **`search-index.json`** — static lexical search corpus built from the
  same pages: metadata, markdown headings (ATX and setext, mirroring
  the published HTML), and normalized searchable text. No embeddings,
  ranking, database, or UI.

All four are deterministic: identical source content, source commit,
site configuration, and generator version produce byte-identical
output. Provenance is the exact source commit passed via
`--source-commit` (validated as a full 40-character SHA and passed
identically to generation and verification) — never a timestamp.

Crawler policy: `robots.txt` now allows all crawling and advertises
the sitemap, and the intentional `noindex, nofollow` meta tag was
removed from `_includes/custom.html`. `jekyll-sitemap` remains the
only sitemap generator; the verifier validates its output.

`verify_site.py` consumes the built `manifest.json` as the declaration
of expected pages and peers (no content checkout or rescanning): it
validates the manifest, the search index, `llms.txt`, the built raw
peers, the sitemap (existence, XML validity, configured URL prefix,
presence of every built canonical HTML route), robots.txt, and the
absence of noindex, then HTTP-checks all routes plus
`/llms.txt`, `/manifest.json`, `/search-index.json`, `/sitemap.xml`,
`/robots.txt`, and every markdown peer under the configured base URL.

Baseline parity for PR3: the 53 generated content pages, home, and
sections browse page are byte-identical to the pre-PR3 site; the only
built-HTML change is the intentional removal of the noindex meta tag
from the homepage. New artifacts are additive.

## Site-owned tooling

Generate (explicit roots; works from nested or independent checkouts):

```bash
python scripts/generate_site.py \
  --source-root <content> --site-root <site> \
  --source-commit "$(git -C <content> rev-parse HEAD)"
```

Verify (against a server exposing the built site under the configured
base URL `/ciso-in-a-box-site`):

```bash
python scripts/verify_site.py --build-root _site \
  --base-url http://127.0.0.1:8765 \
  --source-commit "$(git -C <content> rev-parse HEAD)"
```

## Content model

There is no per-section Python metadata table. Inventory is discovered
dynamically:

- Sections: top-level `NN - Section Name` directories, ordered by the
  numeric prefix. Any valid numbered section is discoverable; no
  changes to Python are needed to add one.
- Section home: the section README (detected case-insensitively). A
  numbered section without a README still publishes a section home
  (navigation only) — that is the documented general behavior.
- Child pages: every other `.md` file beneath the section, routes
  derived from the source-relative path. A nested README's filename is
  never a route component.
- Assets: every non-Markdown file beneath sections, copied to
  `assets/content/<source-relative-path>`. No extension whitelist.
- Titles: first ATX H1, then first Setext H1, then (README pages) the
  containing directory title, then the first ATX heading of any level,
  then the filename-derived title.
- Descriptions: derived from the first prose paragraph; deterministic
  fallback otherwise.

## Public URL compatibility

`LEGACY_SECTION_ROUTES` in `scripts/site_config.py` maps section
directory names to published slugs for routes that cannot be derived
from the directory name (for example
`04 - Mapping Attack Surface` -> `/mapping-your-attack-surface/`).
It contains only slug facts — no titles, summaries, or content
metadata. Sections not listed derive their slug from the directory name
with the numeric prefix removed.

Configured presentation routes (navbar, homepage pathways, modules)
are validated against discovered pages at generation time; a broken
configured route fails the build instead of silently emitting a broken
link.

## Baseline parity (content@6d3dd06 -> site@11bee37)

Routes, files, `_config.yml`, `index.markdown`, and
`contributing.markdown` are byte-identical to the previous generator's
output. Intentional metadata differences, all caused by replacing
hard-coded per-section metadata with general derivation:

- 8 page `title:` values now come from content H1s instead of curated
  text (routes unchanged).
- 22 section `share-description:` values are derived from prose instead
  of hand-written summaries.
- The unused `nav_category` front-matter key was removed.
- `sections.markdown` lists sections in one "All Sections" group
  instead of curated categories, with derived descriptions.

## Transitional legacy files (deleted in PR2)

- `convert_to_jekyll_improved.py`, `rebuild_navigation.py`,
  `build.sh`, `trigger-rebuild.sh` — old content-side conversion path.
- `assets/pdf/`, `assets/excel/`, `assets/xlsx/`, `assets/Resources.txt`
  — artifacts of the old conversion pipeline, superseded by
  `assets/content/`.

## Deferred work (PR3 candidates)

- Remove the `ciso-in-a-box-site` submodule gitlink and `.gitmodules`
  from the content repository (deferred at review time; kept working
  until the site-owned pipeline has run stably in production for a
  while).

## Curated editorial overrides (restored)

The 8 re-derived titles and 22 derived section descriptions noted
above were addressed after review: `CURATED_SECTION_TITLES` and
`CURATED_SECTION_DESCRIPTIONS` in `scripts/site_config.py` hold
optional route-keyed overrides applied to section homes. Publishing
does not require any entry (absent routes fall back to derivation),
and stale entries fail generation. The published titles and summaries
are restored; the only intentionally kept derivation improvement is
`/resources/book-list/` titled "Book List" (was "Readme").

The `/sections/` browse-page category grouping is also restored via
`SECTION_CATEGORY_ORDER` + `CURATED_SECTION_CATEGORIES`. A section
absent from the category map still publishes and appears under a
trailing "Additional Sections" group, so grouping is presentation
only and never gates discovery. With these, 53 of 55 built pages are
byte-identical to the pre-migration published site; the two remaining
differences are the intentional "Book List" naming.