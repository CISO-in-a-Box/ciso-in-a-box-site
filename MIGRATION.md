# Publishing Migration — PR1

Status: **PR1 and PR2 complete.** The publishing repository owns site
generation, publishing configuration, verification, and CI. The
content repository's publishing scripts are deleted; the content
repository now contains content only (the `ciso-in-a-box-site`
submodule gitlink and `.gitmodules` remain for now — see deferred
work below).

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
`contributing.markdown`).

The content-repository copies of `generate_site.py`, `site_config.py`,
and `verify_site.py` were deleted in PR2.

## Site-owned tooling

Generate (explicit roots; works from nested or independent checkouts):

```bash
python scripts/generate_site.py --source-root <content> --site-root <site>
```

Verify (against a server exposing the built site under the configured
base URL `/ciso-in-a-box-site`):

```bash
python scripts/verify_site.py --build-root _site \
  --base-url http://127.0.0.1:8765
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
- Optionally revisit the 8 re-derived page titles and 22 derived
  section descriptions if curated wording is wanted (a content
  decision, not a publishing one).