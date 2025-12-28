#!/usr/bin/env python3
"""
Fix title extraction and link generation issues
"""

import os
import re
from pathlib import Path

def extract_title_from_content(content: str) -> str:
    """Extract title from content with better fallbacks."""
    lines = content.split('\n')
    
    # Look for H1 title (with or without bold)
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            title = re.sub(r'\*\*', '', title)  # Remove **bold**
            return title.strip()
        
        # Look for bold text that might be a title
        if line.startswith('**') and line.endswith('**'):
            title = line[2:-2].strip()
            if len(title) > 10 and len(title) < 100:  # Reasonable length
                return title.strip()

def extract_title_from_directory(dir_path: Path) -> str:
    """Extract title from directory name."""
    dir_name = dir_path.name
    
    # Extract title after "XX - "
    if ' - ' in dir_name:
        title = dir_name.split(' - ', 1)[1]
    else:
        title = dir_name
    
    # Clean up
    title = title.replace('-', ' ')
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Capitalize properly
    words = title.split()
    capitalized_words = []
    for word in words:
        if word.lower() in ['and', 'the', 'for', 'of', 'in', 'on', 'with']:
            capitalized_words.append(word.lower())
        else:
            capitalized_words.append(word.capitalize())
    
    return ' '.join(capitalized_words)

# Fix generated markdown files
docs_dir = Path("/home/christian/github/CISOinaBox/ciso-in-a-box-site/docs")
source_dir = Path("/home/christian/github/CISOinaBox")

print("🔧 Fixing titles and links...")

# Mapping of sections to their info
section_info = {}

# Get all sections
for i in range(1, 23):
    pattern_dirs = list(source_dir.glob(f"{i:02d} - *"))
    if pattern_dirs:
        dir_path = pattern_dirs[0]
        # Read content
        readme_files = ['Readme.md', 'README.md', 'readme.md']
        content = ""
        for filename in readme_files:
            content_file = dir_path / filename
            if content_file.exists():
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                break
        
        # Extract title with fallbacks
        title = extract_title_from_content(content)
        if not title or title == "Untitled Section":
            title = extract_title_from_directory(dir_path)
        
        # Find the corresponding markdown file
        for md_file in docs_dir.glob("*.markdown"):
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Check if this matches our content
            if len(content) > 100:
                content_snippet = content.replace('\n', '').replace(' ', '').lower()[:200]
                md_snippet = md_content.replace('\n', '').replace(' ', '').lower()[:200]
                
                if content_snippet in md_snippet or md_snippet in content_snippet:
                    section_info[md_file.name] = {
                        'title': title,
                        'slug': md_file.stem,
                        'content': content
                    }
                    break
                # Also check by section number
                if f"section_number: {i}" in md_content:
                    section_info[md_file.name] = {
                        'title': title,
                        'slug': md_file.stem,
                        'content': content
                    }
                    break

print(f"Found {len(section_info)} sections to fix")

# Update markdown files with correct titles
for filename, info in section_info.items():
    md_file = docs_dir / filename
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update title in front matter
    new_content = re.sub(
        r'title: "[^"]*"',
        f'title: "{info["title"]}"',
        content
    )
    
    # Update actual content with proper title if missing
    if info['content'].startswith('# ') is False and info['title']:
        new_content = re.sub(
            r'---\n\n',
            f'---\n\n# {info["title"]}\n\n',
            new_content
        )
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Updated {filename} with title: {info['title']}")

# Update config with proper navigation
config_file = Path("/home/christian/github/CISOinaBox/ciso-in-a-box-site/_config.yml")
with open(config_file, 'r', encoding='utf-8') as f:
    config_content = f.read()

# Define categories
categories = {
    "Getting Started": {
        "keywords": ["getting started", "overview"],
        "sections": []
    },
    "Risk & Threat Management": {
        "keywords": ["risk", "threat", "adversary", "attack surface"],
        "sections": []
    },
    "Security Controls": {
        "keywords": ["cis18", "controls", "architecture", "engineering", "product security", "business process"],
        "sections": []
    },
    "Security Program": {
        "keywords": ["management", "leadership", "identity", "awareness", "operations", "incident response", "careers"],
        "sections": []
    },
    "Compliance & Resilience": {
        "keywords": ["governance", "compliance", "continuity", "disaster recovery", "vulnerability", "frameworks", "cyber insurance", "resources"],
        "sections": []
    }
}

# Categorize sections
for info in section_info.values():
    title_lower = info['title'].lower()
    
    categorized = False
    for cat_name, cat_info in categories.items():
        for keyword in cat_info['keywords']:
            if keyword in title_lower:
                cat_info['sections'].append(info)
                categorized = True
                break
        if categorized:
            break
    
    if not categorized:
        categories["Getting Started"]['sections'].append(info)

# Sort sections within categories
for cat in categories.values():
    cat['sections'].sort(key=lambda x: x['title'])

# Generate navigation yaml
nav_yaml = '# Navigation Bar\nnavbar-links:\n'

for cat_name, cat_info in categories.items():
    if cat_info['sections']:
        nav_yaml += f'  "{cat_name}":\n'
        
        for section in cat_info['sections']:
            nav_yaml += f'    - "{section["title"]}": "/{section["slug"]}/"\n'

# Add resources
nav_yaml += '''  Resources:
    - Contributing: "/contributing/"  
    - GitHub Repo: "https://github.com/CroodSolutions/CISOinaBox"
'''

# Update config
new_config = re.sub(
    r'# Navigation Bar\nnavbar-links:.*?(?=\n\n|\n#|\Z)',
    nav_yaml.strip(),
    config_content,
    flags=re.DOTALL
)

with open(config_file, 'w', encoding='utf-8') as f:
    f.write(new_config)

print("✅ Updated navigation configuration")
print("🎉 Title and link fixes complete!")
