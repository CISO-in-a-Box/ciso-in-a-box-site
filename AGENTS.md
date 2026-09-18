# CISOinaBox Website Build - AGENTS.md

## Overview

**PR1 and PR2 of the publishing migration are complete.** The authoritative generation implementation now lives in this repository (the publishing repo), not the content repository. See `MIGRATION.md` for details.

This document describes the original conversion of CISOinaBox from a repository-based documentation structure to a GitHub Pages-hosted Jekyll website. The current authoritative build workflow is the site-owned generator described under **Development Workflow**; earlier conversion history is retained below for reference.

## Project Structure Conversion

### From Repository Organization
- **Original Structure**: 22 numbered directories (01-22) with varying Readme.md/README.md files
- **Main README.md**: Project overview and navigation
- **Assets**: PDFs, Excel files scattered across sections
- **Format**: Standard markdown with headers, lists, links, external images

### To Jekyll Website Structure
```
ciso-in-a-box-site/
├── _config.yml              # Jekyll configuration with navigation
├── index.markdown           # Home page (converted from main README.md)
├── docs/                    # All section content as Jekyll pages
│   ├── getting-started.markdown
│   ├── understanding-business-risk.markdown
│   ├── identity-and-access-management.markdown
│   └── ... (19 more sections)
├── assets/                  # Centralized asset management
│   ├── pdf/                 # All PDF documents
│   ├── excel/               # Excel files
│   └── ... (other assets)
├── Gemfile                  # Jekyll dependencies
└── _site/                   # Generated static site (auto-generated)
```

## Conversion Methodology

### 1. Content Processing Pipeline
- **Directory Name Slugification**: `01 - Getting Started` → `getting-started`
- **Case-Insensitive File Detection**: Handles `Readme.md`, `README.md`, `readme.md`
- **Title Extraction**:自动提取内容中的H1标题，或使用目录名生成
- **Jekyll Front Matter Addition**:
```yaml
---
layout: page
title: "Section Title"
permalink: /section-slug
---
```

### 2. Asset Management Strategy
- PDFs copied to `assets/pdf/` directory
- Excel files copied to `assets/excel/` directory
- All internal links updated to reference new asset paths
- Preserved original file naming for compatibility

### 3. Navigation Structure Generation
- Automatic navigation menu generation from directory structure
- Section grouping with logical dividers
- SEO-friendly clean URLs
- Consistent navigation across all pages

### 4. Link Conversion System
- Internal section links converted to Jekyll permalinks
- Relative path standardization
- Maintained external link integrity
- Updated README.md references to use new URL structure

## Technical Implementation

### Python Conversion Script (`convert_to_jekyll.py`)
**Key Components:**
- `CISOToJekyllConverter` class orchestrating the conversion
- `slugify_section_name()` - URL-safe filename generation
- `process_section()` - Content conversion with front matter
- `copy_assets()` - Asset management and organization
- `generate_config_navigation()` - Jekyll configuration
- `convert_main_readme()` - Homepage conversion

**File Processing:**
- Preserved markdown formatting and structure
- Maintained existing content hierarchy
- Added SEO metadata and page titles
- Ensured proper character encoding (UTF-8)

### Jekyll Configuration
**Theme Setup:**
- Beautiful Jekyll theme (`daattali/beautiful-jekyll`)
- Custom navigation structure
- Professional color scheme matching CISOinABranding
- Responsive design for mobile compatibility

**Build Configuration:**
- Ruby gem dependencies managed via bundler
- Local development server support
- GitHub Pages deployment ready
- Search functionality included

## Development Workflow

### Build Process

**The site-owned generator is authoritative.** Regeneration is driven
from this repository's scripts; the content repository is read-only
input.

```bash
# Regenerate Jekyll source from the content repo
python scripts/generate_site.py \
  --source-root <content-checkout> \
  --site-root . \
  --source-commit "$(git -C <content-checkout> rev-parse HEAD)"

# Verify a built site (served under the configured base URL)
python scripts/verify_site.py \
  --build-root _site \
  --base-url http://127.0.0.1:8765 \
  --source-commit "$(git -C <content-checkout> rev-parse HEAD)"
```

The same exact 40-character source SHA must be passed to generation and
verification. The generator also produces the machine-readable layer
alongside the Jekyll source: raw Markdown peers under `markdown/`,
`llms.txt`, `manifest.json`, and `search-index.json` — all deterministic
(no timestamps).

The old content-side converter scripts (`build.sh`,
`convert_to_jekyll_improved.py`, `rebuild_navigation.py`,
`trigger-rebuild.sh`) were deleted in PR2. CI
(`rebuild-site.yml`) regenerates and verifies on every relevant push
using the scripts above; see `MIGRATION.md` for the architecture.

### Generated Skill (PR4)

The same generator invocation also produces a lightweight
CISO-in-a-Box Skill and the `/use-with-ai/` page. The Skill is a
control plane, not a knowledge copy: it contains no bundled content and
teaches progressive retrieval from the published static interface
(`llms.txt` / `manifest.json` -> relevant pages -> only the relevant
`markdown/*.md` peers; `search-index.json` only when page selection is
unclear).

Generated, generator-owned outputs:

```text
skill/ciso-in-a-box/SKILL.md                  # compact instructions
skill/ciso-in-a-box/agents/openai.yaml        # minimal UI metadata
skill/ciso-in-a-box/references/endpoints.md   # publishing endpoints
skill/ciso-in-a-box/skill.zip                 # deterministic archive
use-with-ai.markdown                          # /use-with-ai/ page
```

In `SKILL.md` front matter, `name` is `ciso-in-a-box` and the
`description` is the Skill trigger. `skill.zip` is deterministic (fixed
timestamps, sorted members, stable permissions; standard library only).
The `SKILL.md` displayed on `/use-with-ai/`, the published file, and
the ZIP member are byte-equivalent by construction. `verify_site.py`
validates the Skill files, the ZIP inventory and byte-equality, the
`/use-with-ai/` page, and HTTP-serves all five Skill paths.

### Machine-Readable Layer (PR3)

The same discovered page model also publishes static machine-readable
artifacts next to the HTML site:

- `markdown/` — one raw `.md` peer per source-backed Markdown page
  (`/foo/bar/` HTML route -> `/markdown/foo/bar.md` peer), each led by
  a compact provenance comment (canonical URL, source repository,
  source path, exact source commit) followed by the faithful source
  Markdown. No Jekyll front matter; the leading comment is what keeps
  the file raw through Jekyll.
- `llms.txt` — concise discovery index: 22 section-home peers,
  Contributing, and the machine indexes.
- `manifest.json` — canonical page inventory (title, description,
  source path, canonical HTML URL, markdown peer URL, section number),
  deterministically ordered by route.
- `search-index.json` — static lexical search corpus per page:
  metadata, headings, and normalized text. No embeddings, no ranking,
  no UI.

All four are deterministic generator-owned outputs (no timestamps, no
environment paths). `robots.txt` is a simple site-owned crawler policy
that now allows crawling and advertises the sitemap; the intentional
`noindex` meta tag was removed. `verify_site.py` validates the
artifacts, the built peers, the sitemap, robots, and the absence of
noindex, using the built `manifest.json` as the declaration of expected
pages — no content checkout needed.

### Local Development (Jekyll - requires Ruby)
```bash
# Set up environment
cd ciso-in-a-box-site
export GEM_HOME=~/tmp/gems
~/tmp/gems/bin/bundle install

# Development server
~/tmp/gems/bin/bundle exec jekyll serve --host 0.0.0.0 --port 4000

# Build verification
~/tmp/gems/bin/bundle exec jekyll build --verbose
```

### Site Structure Verification
```bash
# Check generated site
ls _site/                    # Verify all HTML files generated
curl -s http://localhost:4000  # Test server response
curl -w "%{http_code}" -o /dev/null -s http://localhost:4000  # HTTP status check
```

## Asset Management Guidelines

### File Organization
- **Generated content assets**: `/assets/content/<source-relative-path>/` - copied from the content repository by the generator
- **Site-owned static files**: `/assets/css/`, `/assets/img/` - theme resources

### Link Management
- Internal links use Jekyll permalinks (`/section-name`)
- Content asset links reference `assets/content/`
- External links maintain original targets
- GitHub links preserved for repository access

## Content Update Process

Content lives in the CroodSolutions/CISOinaBox repository (read-only
input for this publishing repository).

### Adding New Sections
1. Create new section directory in the content repo: `XX - Section Name/`
2. Add a `Readme.md` with section content
3. The generator discovers it dynamically on the next CI rebuild - no Python or config changes needed

### Modifying Existing Content
1. Edit source `.md` files in the content repository
2. CI regenerates the site automatically (scheduled weekly or on push)
3. Generated changes are committed to this repo and deployed to GitHub Pages

### Asset Updates
1. Place new non-Markdown files in the appropriate content section directory
2. The generator copies them to `assets/content/` on the next rebuild

## Quality Assurance

### Automated Verification
- **Build Process**: `jekyll build --verbose` for detailed output
- **Link Checking**: Verify internal/external links are functioning
- **Asset Verification**: Ensure all PDFs/Excel files accessible
- **Responsive Testing**: Check mobile and desktop rendering

### Content Integrity
- Maintained original markdown formatting
- Preserved section numbering and order
- Kept original content hierarchy
- Ensured proper encoding for special characters

## Deployment Strategy

### GitHub Pages Ready
- Site configured for automatic GitHub Pages deployment
- Custom domain support (ciso-in-a-box.github.io)
- SSL certificates automatically handled
- CDN delivery through GitHub's infrastructure

### Continuous Updates
- Source content remains in original repository
- Conversion script regenerates entire site structure
- Maintained synchronization between source and deployed content
- Version control for both source and generated site

## Future Enhancements

### Potential Improvements
- **Search Optimization**: Enhanced metadata for better search
- **Interactive Elements**: Consider adding interactive tools or demos
- **User Feedback**: Integration for community contributions
- **Analytics**: Site usage tracking and improvement metrics
- **Multi-language Support**: Internationalization capabilities

### Maintenance Plan
- **Regular Content Reviews**: Quarterly section updates
- **Link Monitoring**: Automated external link validation
- **Performance Optimization**: Image optimization and loading improvements
- **Security Updates**: Theme and dependency security patches

## Troubleshooting Guide

### Common Issues
- **Permission Errors**: Use local gem directory (`export GEM_HOME=~/tmp/gems`)
- **Build Failures**: Check _config.yml syntax and Ruby version compatibility
- **Missing Assets**: Verify asset paths in generated content
- **Navigation Issues**: Review navbar-links structure in _config.yml

### Debug Commands
```bash
# Check Jekyll version
~/tmp/gems/bin/bundle exec jekyll --version

# Verify configuration
~/tmp/gems/bin/bundle exec jekyll doctor

# Detailed build output
~/tmp/gems/bin/bundle exec jekyll build --verbose --trace
```

## Conclusion

The CISOinaBox website conversion successfully transformed a repository-based documentation structure into a professional, maintainable Jekyll website. The automated conversion process ensures consistency, preserves content integrity, and provides a scalable foundation for future enhancements.

The website is now ready for GitHub Pages deployment and provides an improved user experience with better navigation, responsive design, and accessibility. The conversion methodology ensures future updates remain straightforward while maintaining professional web standards.

---

**Last Updated**: 2025-10-22  
**Conversion Version**: 1.0  
**Jekyll Theme**: Beautiful Jekyll 6.0.1  
**Ruby Version**: Compatible with 3.3.0+