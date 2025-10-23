#!/usr/bin/env python3
"""
Generate missing sections that weren't captured
"""

import os
from pathlib import Path

source_dir = Path("/home/christian/github/CISOinaBox")
output_dir = Path("/home/christian/github/CISOinaBox/ciso-in-a-box-site")

# Define missing sections with their proper titles
missing_sections = [
    {
        'number': 1,
        'title': 'Getting Started',
        'slug': 'getting-started',
        'category': 'Getting Started',
        'content_dir': '01 - Getting Started'
    },
    {
        'number': 7,
        'title': 'Product and Software Security', 
        'slug': 'product-and-software-security',
        'category': 'Security Controls',
        'content_dir': '07 - Product and Software Security'
    },
    {
        'number': 16,
        'title': 'Business Continuity Planning - BCP',
        'slug': 'business-continuity-planning---bcp', 
        'category': 'Compliance & Resilience',
        'content_dir': '16 - Business Continuity Planning - BCP'
    },
    {
        'number': 17,
        'title': 'Disaster Recovery - DR',
        'slug': 'disaster-recovery---dr',
        'category': 'Compliance & Resilience', 
        'content_dir': '17 - Disaster Recovery - DR'
    },
    {
        'number': 18,
        'title': 'Vulnerability Management and Risk',
        'slug': 'vulnerability-management-and-risk',
        'category': 'Compliance & Resilience',
        'content_dir': '18 - Vulnerability Management and Risk'
    },
    {
        'number': 19,
        'title': 'Frameworks and Standards',
        'slug': 'frameworks-and-standards',
        'category': 'Compliance & Resilience',
        'content_dir': '19 - Frameworks and Standards'
    },
    {
        'number': 21,
        'title': 'Cyber Insurance',
        'slug': 'cyber-insurance',
        'category': 'Compliance & Resilience',
        'content_dir': '21 - Cyber Insurance'
    },
    {
        'number': 22,
        'title': 'Resources',
        'slug': 'resources',
        'category': 'Compliance & Resilience',
        'content_dir': '22 - Resources'
    }
]

for section in missing_sections:
    print(f"Generating {section['title']}...")
    
    # Find content
    source_path = source_dir / section['content_dir']
    content = f"# {section['title']}\n\n"
    
    # Try to read content from source
    for readme_name in ['Readme.md', 'README.md', 'readme.md']:
        readme_file = source_path / readme_name
        if readme_file.exists():
            with open(readme_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()
                if raw_content.strip() and raw_content.strip() != "Placeholder":
                    content = raw_content
                    break
    
    # Create Jekyll file
    front_matter = f"""---
layout: page
title: "{section['title']}"
permalink: /{section['slug']}
nav_category: "{section['category']}"
section_number: {section['number']}
---

"""
    
    # Write file
    output_file = output_dir / 'docs' / f"{section['slug']}.markdown"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(front_matter + content)
    
    print(f"  ✅ Created {output_file.name}")

print("✅ All missing sections generated!")
