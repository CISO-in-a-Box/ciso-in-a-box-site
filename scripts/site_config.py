#!/usr/bin/env python3
"""Publishing configuration for the CISO-in-a-Box site.

This file is the publishing repository's authority for site-owned facts:
identity, URL structure, curated presentation, and public-route
compatibility. The content repository is read-only input; nothing here
describes content inventory. Pages are discovered dynamically from the
filesystem by scripts/generate_site.py.

Configuration rules:
- Curated entries (navbar, pathways, modules) reference discovered pages
  by their public route. Generation fails clearly if a configured route
  does not exist.
- LEGACY_SECTION_ROUTES holds only public-slug compatibility facts for
  sections whose published route cannot be derived from the source
  directory name. Do not put titles, summaries, prose, or any other
  content metadata here.
"""

# ---- Site identity -----------------------------------------------------

SITE_TITLE = "CISO-in-a-Box"
SITE_AUTHOR = "CISOinaBox Contributors"
SITE_EMAIL = "contributors@ciso-in-a-box.org"
SITE_DESCRIPTION = (
    "A comprehensive guide to cybersecurity and risk management "
    "for organizations, aspiring CISOs, and security professionals."
)

SITE_URL = "https://ciso-in-a-box.github.io"
SITE_BASEURL = "/ciso-in-a-box-site"

# ---- Source repository (read-only content input) ------------------------

GITHUB_REPO_URL = "https://github.com/CroodSolutions/CISOinaBox"
GITHUB_ORG = "CroodSolutions"
GITHUB_REPO_NAME = "CISOinaBox"
GITHUB_BRANCH = "main"

# ---- Public URL compatibility -------------------------------------------

# Section directory name -> published route slug, for sections whose
# current public route is not derivable from the directory name.
# Sections not listed here derive their slug from the directory name
# (with the numeric prefix removed). A key that matches no discovered
# section fails generation so stale entries get cleaned up.
LEGACY_SECTION_ROUTES = {
    "02 - Understanding Business Risk":
        "understanding-enterprise-risk-management-erm-for-cisos",
    "03 - Understanding the Adversary":
        "cyber-attacks-and-defense-threat-intelligence-adversaries-and-collective-defense",
    "04 - Mapping Attack Surface":
        "mapping-your-attack-surface",
    "05 - CIS18 and Basic Security Controls":
        "overview-of-cis18-critical-security-controls",
    "08 - Secure Business Process Design":
        "secure-business-process-optimization",
    "09 - Identity and Access Management":
        "identity-and-access-management-iam-overview",
    "10 - Security Management":
        "ciso-security-management-strategy-guide",
    "11 - Security Leadership":
        "security-leadership-strategy-guide-for-cisos",
    "12 - Governance Risk and Compliance":
        "governance-risk-compliance-grc-strategy-guide-for-cybersecurity-programs",
    "13 - Security Awareness":
        "security-awareness-building-a-human-firewall",
    "14 - Security Operations - SOC":
        "cybersecurity-operations-secops-program-maturity-guide",
    "15 - Response - IR":
        "cyber-incident-response-strategy-guide-for-cisos",
    "16 - Business Continuity Planning - BCP":
        "business-continuity-planning---bcp",
    "17 - Disaster Recovery - DR":
        "disaster-recovery---dr",
    "20 - Careers - The Road to CISO":
        "cybersecurity-and-it-career-pathways",
}

# ---- Curated presentation ------------------------------------------------
# These reference discovered pages by public route. All routes listed
# here must exist as generated pages; generation fails otherwise.

PATHWAY_CARDS = [
    {
        "title": "The New CISO",
        "description": (
            "Just landed the role? Start here to navigate your first "
            "90 days, build relationships, and set the strategy."
        ),
        "icon": "fas fa-flag",
        "topics": [
            "Getting Started (First 90 Days)",
            "Security Leadership Strategy",
            "Enterprise Risk Management",
        ],
        "link_route": "/getting-started/",
        "color": "#289dff",
    },
    {
        "title": "The Program Builder",
        "description": (
            "Focus on architecture, engineering, and operations. "
            "Build the systems that defend the business."
        ),
        "icon": "fas fa-tools",
        "topics": [
            "Security Architecture",
            "SecOps & Incident Response",
            "Vulnerability Management",
        ],
        "link_route": "/security-architecture-and-engineering/",
        "color": "#7952b3",
    },
    {
        "title": "The Strategist",
        "description": (
            "Align security with business goals. "
            "Master GRC, compliance, insurance, and resilience."
        ),
        "icon": "fas fa-chess",
        "topics": [
            "Governance, Risk & Compliance",
            "Business Continuity (BCP)",
            "Cyber Insurance",
        ],
        "link_route": "/governance-risk-compliance-grc-strategy-guide-for-cybersecurity-programs/",
        "color": "#ffc107",
    },
]

HOMEPAGE_MODULES = [
    {"route": "/overview-of-cis18-critical-security-controls/", "icon": "fas fa-shield-alt", "short_title": "CIS18 Controls", "subtitle": "Critical Framework"},
    {"route": "/mapping-your-attack-surface/", "icon": "fas fa-map-marked-alt", "short_title": "Attack Surface", "subtitle": "Know your perimeter"},
    {"route": "/identity-and-access-management-iam-overview/", "icon": "fas fa-id-card", "short_title": "IAM Overview", "subtitle": "Identity is the perimeter"},
    {"route": "/product-and-software-security/", "icon": "fas fa-code", "short_title": "AppSec", "subtitle": "Secure Development"},
    {"route": "/security-awareness-building-a-human-firewall/", "icon": "fas fa-users", "short_title": "Security Awareness", "subtitle": "Human Firewall"},
    {"route": "/frameworks-and-standards/", "icon": "fas fa-book", "short_title": "Standards", "subtitle": "ISO, NIST, SOC2"},
    {"route": "/cyber-attacks-and-defense-threat-intelligence-adversaries-and-collective-defense/", "icon": "fas fa-user-secret", "short_title": "Threat Intel", "subtitle": "Know your adversary"},
    {"route": "/resources/", "icon": "fas fa-box-open", "short_title": "Resources", "subtitle": "Tools & Templates"},
]

NAVBAR_CONFIG = [
    {
        "label": "Browse the Guide",
        "items": [
            {"label": "Start Here", "route": "/getting-started/"},
            {"label": "Browse All Sections", "route": "/sections/"},
            {"label": "Resources", "route": "/resources/"},
        ],
    },
    {
        "label": "Learning Paths",
        "items": [
            {"label": "The New CISO", "route": "/getting-started/"},
            {"label": "The Program Builder", "route": "/security-architecture-and-engineering/"},
            {"label": "The Strategist", "route": "/governance-risk-compliance-grc-strategy-guide-for-cybersecurity-programs/"},
        ],
    },
    {
        "label": "Project and Source",
        "items": [
            {"label": "Contributing", "route": "/contributing/"},
            {"label": "GitHub Repo", "url": "github"},
        ],
    },
]