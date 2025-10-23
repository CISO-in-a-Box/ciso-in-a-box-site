#!/usr/bin/env python3
"""
Improved CISOinaBox to Jekyll Converter
Enhanced with better title generation, logical grouping, and link validation
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class ImprovedCISOToJekyllConverter:
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.sections = []
        self.errors = []
        self.warnings = []
        
        # Define navigation categories based on content analysis
        self.nav_categories = {
            "Getting Started": {
                "keywords": ["getting started", "overview", "introduction"],
                "sections": [],
                "description": "Basic introduction and getting started guide"
            },
            "Risk & Threat Management": {
                "keywords": ["risk", "threat", "adversary", "attack surface"],
                "sections": [],
                "description": "Risk assessment and threat intelligence"
            },
            "Security Controls": {
                "keywords": ["cis18", "controls", "architecture", "engineering", "product security", "business process"],
                "sections": [],
                "description": "Technical security controls and architecture"
            },
            "Security Program": {
                "keywords": ["management", "leadership", "awareness", "operations", "incident response"],
                "sections": [],
                "description": "Security program management and operations"
            },
            "Compliance & Resilience": {
                "keywords": ["governance", "compliance", "continuity", "disaster recovery", "vulnerability"],
                "sections": [],
                "description": "Compliance, governance, and resilience planning"
            },
            "Advanced Topics": {
                "keywords": ["frameworks", "careers", "cyber insurance", "resources"],
                "sections": [],
                "description": "Advanced topics and career development"
            }
        }
    
    def find_sections(self) -> List[Dict]:
        """Find all numbered section directories."""
        sections = []
        
        for i in range(1, 23):  # 01-22
            dir_patterns = [
                f"{i:02d} - *",
                f"{i} - *"
            ]
            
            found = False
            for pattern in dir_patterns:
                matching_dirs = list(self.source_dir.glob(pattern))
                if matching_dirs:
                    for dir_path in matching_dirs:
                        if dir_path.is_dir():
                            sections.append({
                                'number': i,
                                'path': dir_path,
                                'name': dir_path.name
                            })
                            found = True
                            break
                if found:
                    break
            
            if not found:
                self.warnings.append(f"Section {i:02d} not found")
        
        sections.sort(key=lambda x: x['number'])
        return sections
    
    def extract_title_from_content(self, content: str) -> str:
        """Extract clean title from markdown content."""
        lines = content.split('\n')
        
        # Look for H1 title
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                title = line[2:].strip()
                # Clean up markdown artifacts
                title = re.sub(r'\*\*', '', title)  # Remove **bold**
                title = re.sub(r'---', '', title)   # Remove ---
                title = re.sub(r'#+$', '', title)   # Remove trailing #
                return title.strip()
        
        return "Untitled Section"
    
    def slugify_title(self, title: str) -> str:
        """Convert title to URL-friendly slug."""
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        # Handle special cases
        if slug == 'secops':
            slug = 'security-operations---soc'
        elif slug == 'ir':
            slug = 'response---ir'
        elif slug == 'bcp':
            slug = 'business-continuity-planning---bcp'
        elif slug == 'dr':
            slug = 'disaster-recovery---dr'
            
        return slug
    
    def categorize_section(self, title: str, content: str) -> str:
        """Automatically categorize a section based on title and content."""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Score each category
        category_scores = {}
        
        for category_name, category_info in self.nav_categories.items():
            score = 0
            keywords = category_info['keywords']
            
            for keyword in keywords:
                if keyword in title_lower:
                    score += 10  # Title matches are worth more
                if keyword in content_lower:
                    score += 3   # Content matches are worth less
            
            category_scores[category_name] = score
        
        # Return the category with highest score
        if max(category_scores.values()) == 0:
            # No matches, put in Getting Started by default
            return "Getting Started"
        
        return max(category_scores, key=category_scores.get)
    
    def process_section(self, section: Dict) -> Optional[Dict]:
        """Process a single section directory."""
        section_path = section['path']
        
        # Find readme file (multiple naming patterns)
        readme_files = ['Readme.md', 'README.md', 'readme.md']
        content_file = None
        
        for filename in readme_files:
            potential_file = section_path / filename
            if potential_file.exists():
                content_file = potential_file
                break
        
        if not content_file:
            self.errors.append(f"No content file found in {section_path}")
            return None
        
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading {content_file}: {e}")
            return None
        
        # Extract title and create clean version
        raw_title = self.extract_title_from_content(content)
        title = self.clean_title(raw_title)
        slug = self.slugify_title(title)
        
        # Categorize the section
        category = self.categorize_section(title, content)
        
        # Copy assets if they exist
        self.copy_section_assets(section_path)
        
        return {
            'number': section['number'],
            'title': title,
            'raw_title': raw_title,
            'slug': slug,
            'category': category,
            'content': content,
            'source_file': content_file
        }
    
    def clean_title(self, title: str) -> str:
        """Clean up title for navigation display."""
        # Remove common artifacts
        title = re.sub(r'[*#_]+', '', title)  # Remove markdown chars
        title = re.sub(r'---', '', title)      # Remove dashes
        title = re.sub(r'\s+', ' ', title)     # Normalize whitespace
        title = title.strip()
        
        # Fix common truncation issues
        if title.endswith('Manageme'):
            title = title.replace('Manageme', 'Management')
        elif title.endswith('Cont'):
            title = title.replace('Cont', 'Controls')
        elif title.endswith('Ove'):
            title = title.replace('Ove', 'Overview')
        elif title.endswith('Guid'):
            title = title.replace('Guid', 'Guide')
        elif title.endswith('Stra'):
            title = title.replace('Stra', 'Strategy')
        elif title.endswith('Prog'):
            title = title.replace('Prog', 'Program')
        elif title.endswith('Fir'):
            title = title.replace('Fir', 'Firewall')
            
        return title
    
    def copy_section_assets(self, section_path: Path):
        """Copy assets from a section to the main assets directory."""
        asset_types = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg']
        
        for asset_type in asset_types:
            for asset_file in section_path.glob(f'*.{asset_type}'):
                target_dir = self.output_dir / 'assets' / asset_type
                target_dir.mkdir(parents=True, exist_ok=True)
                
                target_file = target_dir / asset_file.name
                try:
                    shutil.copy2(asset_file, target_file)
                except Exception as e:
                    self.warnings.append(f"Could not copy asset {asset_file}: {e}")
    
    def update_internal_links(self, content: str) -> str:
        """Update internal links to use Jekyll permalinks."""
        # Update asset links
        content = re.sub(
            r'\[([^\]]*)\]\([^)]*\.(pdf|docx?|xlsx?)([^)]*)\)',
            lambda m: f'[{m.group(1)}](/assets/{m.group(2)}/{m.group(1).replace(" ", "%20")}.{m.group(2)}{m.group(3)})',
            content, flags=re.IGNORECASE
        )
        
        # Update section links - this will be handled after all sections are processed
        return content
    
    def generate_markdown_file(self, section_info: Dict) -> bool:
        """Generate Jekyll markdown file for a section."""
        output_path = self.output_dir / 'docs' / f"{section_info['slug']}.markdown"
        
        # Create front matter
        front_matter = f"""---
layout: page
title: "{section_info['title']}"
permalink: /{section_info['slug']}
nav_category: "{section_info['category']}"
section_number: {section_info['number']}
---
"""
        
        # Update content with proper links
        updated_content = self.update_internal_links(section_info['content'])
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(front_matter + updated_content)
            return True
        except Exception as e:
            self.errors.append(f"Error writing {output_path}: {e}")
            return False
    
    def generate_config_navigation(self) -> str:
        """Generate improved Jekyll navigation configuration."""
        nav_config = '# Navigation Bar\nnavbar-links:\n'
        
        # Generate categorized navigation
        for category_name, category_info in self.nav_categories.items():
            if not category_info['sections']:
                continue
                
            nav_config += f'  "{category_name}":\n'
            
            for section in category_info['sections']:
                title = section['title']
                slug = section['slug']
                nav_config += f'    - "{title}": "/{slug}"\n'
        
        # Add resources section
        nav_config += '''  Resources:
    - Contributing: "/contributing"
    - GitHub Repo: "https://github.com/CroodSolutions/CISOinaBox"
'''
        
        return nav_config
    
    def update_links_between_sections(self):
        """Update cross-references between sections."""
        docs_dir = self.output_dir / 'docs'
        
        for section in self.sections:
            filepath = docs_dir / f"{section['slug']}.markdown"
            if not filepath.exists():
                continue
                
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update section-to-section links
            for other_section in self.sections:
                # Look for references to other sections
                patterns = [
                    rf'\[([^\]]*{re.escape(other_section["raw_title"])}[^\]]*)\]\([^)]*\)',
                    rf'\[([^\]]*{re.escape(other_section["title"])}[^\]]*)\]\([^)]*\)',
                ]
                
                for pattern in patterns:
                    content = re.sub(
                        pattern,
                        f'[\\1]/{other_section["slug"]}',
                        content
                    )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def validate_site(self) -> Dict[str, List[str]]:
        """Validate the generated site for issues."""
        validation_results = {
            'missing_files': [],
            'broken_links': [],
            'missing_assets': []
        }
        
        # Check all markdown files exist
        for section in self.sections:
            filepath = self.output_dir / 'docs' / f"{section['slug']}.markdown"
            if not filepath.exists():
                validation_results['missing_files'].append(str(filepath))
        
        # Check for asset references
        docs_dir = self.output_dir / 'docs'
        for md_file in docs_dir.glob('*.markdown'):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find asset links
            asset_links = re.findall(r'\[([^\]]*)\]\(/assets/([^)]+)\)', content)
            for link_text, asset_path in asset_links:
                full_asset_path = self.output_dir / 'assets' / asset_path
                if not full_asset_path.exists():
                    validation_results['missing_assets'].append(f"{asset_path} referenced in {md_file.name}")
        
        return validation_results
    
    def convert(self) -> Dict:
        """Main conversion method."""
        print("🚀 Starting improved CISOinaBox to Jekyll conversion...")
        
        # Find all sections
        raw_sections = self.find_sections()
        print(f"📁 Found {len(raw_sections)} sections")
        
        # Process each section
        for section in raw_sections:
            print(f"📝 Processing section {section['number']:02d}: {section['name']}")
            section_info = self.process_section(section)
            
            if section_info:
                self.sections.append(section_info)
                # Add to appropriate category
                self.nav_categories[section_info['category']]['sections'].append(section_info)
                self.nav_categories[section_info['category']]['sections'].sort(key=lambda x: x['number'])
                
                # Generate markdown file
                if self.generate_markdown_file(section_info):
                    print(f"  ✅ Generated {section_info['slug']}.markdown")
                else:
                    print(f"  ❌ Failed to generate {section_info['slug']}.markdown")
            else:
                print(f"  ❌ Failed to process section {section['number']:02d}")
        
        # Update cross-links
        print("🔗 Updating cross-references...")
        self.update_links_between_sections()
        
        # Generate navigation config
        print("⚙️  Generating navigation configuration...")
        nav_config = self.generate_config_navigation()
        
        # Update _config.yml
        config_path = self.output_dir / '_config.yml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # Replace navbar-links section
        config_content = re.sub(
            r'# Navigation Bar\nnavbar-links:.*?(?=\n\n|\n#|\Z)',
            nav_config.strip(),
            config_content,
            flags=re.DOTALL
        )
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("💾 Updated _config.yml with improved navigation")
        
        # Validate the site
        print("🔍 Validating generated site...")
        validation_results = self.validate_site()
        
        # Generate report
        report = {
            'sections_processed': len(self.sections),
            'categories_created': len([cat for cat in self.nav_categories.values() if cat['sections']]),
            'errors': self.errors,
            'warnings': self.warnings,
            'validation': validation_results,
            'sections': self.sections,
            'categories': {name: {'count': len(info['sections']), 'sections': info['sections']} 
                          for name, info in self.nav_categories.items() if info['sections']}
        }
        
        return report

def main():
    """Main execution function."""
    source_dir = "/home/christian/github/CISOinaBox"
    output_dir = "/home/christian/github/CISOinaBox/ciso-in-a-box-site"
    
    converter = ImprovedCISOToJekyllConverter(source_dir, output_dir)
    report = converter.convert()
    
    print("\n" + "="*60)
    print("🎉 CONVERSION COMPLETE")
    print("="*60)
    
    print(f"✅ Sections processed: {report['sections_processed']}")
    print(f"✅ Categories created: {report['categories_created']}")
    
    if report['errors']:
        print(f"\n❌ ERRORS ({len(report['errors'])}):")
        for error in report['errors']:
            print(f"  • {error}")
    
    if report['warnings']:
        print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
        for warning in report['warnings']:
            print(f"  • {warning}")
    
    validation = report['validation']
    total_issues = sum(len(issues) for issues in validation.values())
    if total_issues > 0:
        print(f"\n🔍 VALIDATION ISSUES ({total_issues}):")
        for issue_type, issues in validation.items():
            if issues:
                print(f"  {issue_type}: {len(issues)}")
                for issue in issues[:3]:  # Show first 3
                    print(f"    • {issue}")
                if len(issues) > 3:
                    print(f"    ... and {len(issues) - 3} more")
    
    print(f"\n📋 CATEGORIES CREATED:")
    for cat_name, cat_info in report['categories'].items():
        print(f"  📁 {cat_name}: {cat_info['count']} sections")
        for section in cat_info['sections']:
            print(f"    • {section['title']}")
    
    print(f"\n🚀 Site is ready for testing!")
    print(f"Run: cd {output_dir} && export GEM_HOME=~/tmp/gems && ~/tmp/gems/bin/bundle exec jekyll serve")

if __name__ == "__main__":
    main()
