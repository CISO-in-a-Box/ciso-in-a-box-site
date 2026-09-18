---
# skill-raw: publishes the generated SKILL.md byte-for-byte.
#
# The front matter of this layout is the empty block above (the first
# --- pair). Jekyll's page front-matter parser consumes the closing
# --- line of SKILL.md plus exactly one following newline, so what
# follows reconstructs the file exactly: the front-matter block, one
# blank line, then the raw page body.
---
---
name: {{ page.skill_name }}
description: {{ page.description }}
---

{{ content }}