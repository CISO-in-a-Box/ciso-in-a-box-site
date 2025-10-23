#!/usr/bin/env python3
"""
Clean up duplicate entries and fix categorization
"""

import os
from pathlib import Path

docs_dir = Path("/home/christian/github/CISOinaBox/ciso-in-a-box-site/docs")

# Delete duplicates and keep only one version
files_to_check = [
    'identity-and-access-management-iam-overview.markdown',
    'overview-of-cis18-critical-security-controls.markdown'
]

for filename in files_to_check:
    file_path = docs_dir / filename
    if file_path.exists():
        file_path.unlink()
        print(f"🗑️  Deleted duplicate: {filename}")

# Create proper mapping based on actual sections from directories
source_dir = Path("/home/christian/github/CISOinaBox")
sections_map = [
    ('getting-started', 'Getting Started', 'Getting Started'),
    ('understanding-enterprise-risk-management-erm-for-cisos', 'Understanding Business Risk', 'Risk & Threat Management'),
    ('cyber-attacks-and-defense-threat-intelligence-adversaries-and-collective-defense', 'Understanding the Adversary', 'Risk & Threat Management'),
    ('mapping-your-attack-surface', 'Mapping Attack Surface', 'Risk & Threat Management'),
    ('overview-of-cis18-critical-security-controls', 'CIS18 and Basic Security Controls', 'Security Controls'),
    ('security-engineering-and-architecture', 'Security Architecture and Engineering', 'Security Controls'),
    ('product-and-software-security', 'Product and Software Security', 'Security Controls'),
    ('secure-business-process-optimization', 'Secure Business Process Design', 'Security Controls'),
    ('identity-and-access-management-iam-overview', 'Identity and Access Management', 'Security Program'),
    ('ciso-security-management-strategy-guide', 'Security Management', 'Security Program'),
    ('security-leadership-strategy-guide-for-cisos', 'Security Leadership', 'Security Program'),
    ('governance-risk-compliance-grc-strategy-guide-for-cybersecurity-programs', 'Governance Risk and Compliance', 'Compliance & Resilience'),
    ('security-awareness-building-a-human-firewall', 'Security Awareness', 'Security Program'),
    ('cybersecurity-operations-secops-program-maturity-guide', 'Security Operations', 'Security Program'),
    ('cyber-incident-response-strategy-guide-for-cisos', 'Response', 'Security Program'),
    ('business-continuity-planning---bcp', 'Business Continuity Planning', 'Compliance & Resilience'),
    ('disaster-recovery---dr', 'Disaster Recovery', 'Compliance & Resilience'),
    ('vulnerability-management-and-risk', 'Vulnerability Management', 'Compliance & Resilience'),
    ('frameworks-and-standards', 'Frameworks and Standards', 'Compliance & Resilience'),
    ('cybersecurity-and-it-career-pathways', 'Careers', 'Compliance & Resilience'),
    ('cyber-insurance', 'Cyber Insurance', 'Compliance & Resilience'),
    ('resources', 'Resources', 'Compliance & Resilience')
]

print("🔧 Reorganizing sections...")

# Categorize sections
categories = {
    "Getting Started": [],
    "Risk & Threat Management": [],
    "Security Controls": [],
    "Security Program": [],
    "Compliance & Resilience": []
}

# Build proper sections list
sections = []
for slug, title, category in sections_map:
    md_file = docs_dir / f"{slug}.markdown"
    if md_file.exists():
        section = {
            'slug': slug,
            'title': title,
            'category': category
        }
        sections.append(section)
        categories[category].append(section)
        print(f"  ✅ Found: {title} -> {category}")
    else:
        print(f"  ❌ Missing: {slug}")

# Generate proper navigation
nav_yaml = '# Navigation Bar\nnavbar-links:\n'

for cat_name, cat_sections in categories.items():
    if cat_sections:
        nav_yaml += f'  "{cat_name}":\n'
        
        # Sort sections by original order (from sections_map)
        cat_sections.sort(key=lambda x: sections.index(x))
        
        for section in cat_sections:
            nav_yaml += f'    - "{section["title"]}": "/{section["slug"]}"\n'

# Add resources
nav_yaml += '''  External Resources:
    - GitHub Repo: "https://github.com/CroodSolutions/CISOinaBox"
'''

# Update config file
config_file = Path("/home/christian/github/CISOinaBox/ciso-in-a-box-site/_config.yml")
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

print("✅ Fixed navigation structure")
print("📋 Final organization:")
for cat_name, cat_sections in categories.items():
    print(f"  📁 {cat_name}: {len(cat_sections)} sections")
    for section in cat_sections:
        print(f"    • {section['title']}")
