#!/usr/bin/env python3
"""
Rebuild complete navigation with all sections
"""

import os
from pathlib import Path

docs_dir = Path("/home/christian/github/CISOinaBox/ciso-in-a-box-site/docs")
config_file = Path("/home/christian/github/CISOinaBox/ciso-in-a-box-site/_config.yml")

# Get all sections
sections = []
for md_file in docs_dir.glob("*.markdown"):
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract info from front matter
    title = ""
    slug = md_file.stem
    category = "Getting Started"
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('title: '):
            title = line.replace('title: "', '').replace('"', '').strip()
        elif line.startswith('permalink: /'):
            slug = line.replace('permalink: /', '').strip()
        elif line.startswith('nav_category: '):
            category = line.replace('nav_category: "', '').replace('"', '').strip()
    
    if title:
        sections.append({
            'title': title,
            'slug': slug, 
            'category': category
        })

# Sort by title
sections.sort(key=lambda x: x['title'])

# Define categories
categories = {
    "Getting Started": [],
    "Risk & Threat Management": [], 
    "Security Controls": [],
    "Security Program": [],
    "Compliance & Resilience": []
}

# Auto-categorize by title keywords and slug
for section in sections:
    title_lower = section['title'].lower()
    slug_lower = section['slug'].lower()
    
    if ("getting started" in title_lower or "overview" in title_lower) or section['category'] == "Getting Started":
        categories["Getting Started"].append(section)
    elif any(kw in title_lower for kw in ["risk", "threat", "adversary", "attack surface"]):
        categories["Risk & Threat Management"].append(section)
    elif any(kw in title_lower for kw in ["cis18", "controls", "architecture", "engineering", "product security", "business process"]):
        categories["Security Controls"].append(section)
    elif any(kw in title_lower for kw in ["management", "leadership", "identity", "awareness", "operations", "incident response", "careers"]):
        categories["Security Program"].append(section)
    else:
        categories["Compliance & Resilience"].append(section)

# Generate navigation YAML
nav_yaml = '# Navigation Bar\nnavbar-links:\n'

for cat_name, cat_sections in categories.items():
    if cat_sections:
        nav_yaml += f'  "{cat_name}":\n'
        
        # Sort by logical order or title
        cat_sections.sort(key=lambda x: x['title'])
        
        for section in cat_sections:
            nav_yaml += f'    - "{section["title"]}": "/{section["slug"]}"\n'

# Add resources
nav_yaml += '''  External Resources:
    - GitHub Repo: "https://github.com/CroodSolutions/CISOinaBox"
'''

# Update config
with open(config_file, 'r', encoding='utf-8') as f:
    config_content = f.read()

new_config = config_content
config_start = config_content.find('# Navigation Bar')
if config_start != -1:
    config_end = config_content.find('\n\n#', config_start)
    if config_end == -1:
        config_end = len(config_content)
    
    new_config = config_content[:config_start] + nav_yaml.strip() + config_content[config_end:]

with open(config_file, 'w', encoding='utf-8') as f:
    f.write(new_config)

print("✅ Navigation rebuilt with all sections")
for cat_name, cat_sections in categories.items():
    print(f"  📁 {cat_name}: {len(cat_sections)} sections")
    for section in cat_sections:
        print(f"    • {section['title']}")
