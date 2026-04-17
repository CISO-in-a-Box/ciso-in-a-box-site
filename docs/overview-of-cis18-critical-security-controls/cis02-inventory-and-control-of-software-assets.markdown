---
layout: page
title: 'CIS Control 2: Inventory and Control of Software Assets'
permalink: /overview-of-cis18-critical-security-controls/cis02-inventory-and-control-of-software-assets/
share-description: 'The goal is to understand, track, and manage the different kinds of software deployed across the environment.'
nav_category: 'Security Controls'
section_number: 5
---
[Back to CIS18 and Basic Security Controls](/overview-of-cis18-critical-security-controls/)

## Overview

**What it requires:** Actively manage all software across the environment, including programs running on/in:
 - User Workstations
 - Servers and Containers
 - Kiosks
 - Cloud Workloads
   - Software as a Service (SaaS)
   - Infrastructure as a Service (IaaS)
   - Platform as a Service (PaaS)
 - Extension Ecosystems (Browsers, IDEs, and other applications with extensions)
 - AI Skills

The goal is to understand, track, and manage the different kinds of software deployed across the environment.

In most modern enterprise environments, this also includes managing cloud software such as Software-as-a-Service (SaaS) applications, as well as software running in cloud platforms such as Amazon (AWS), Google (GCP), or Microsoft (Azure). 

A huge portion of this also has cross-over into [Data Protection](/overview-of-cis18-critical-security-controls/cis03-data-protection/), as Enterprise Software solutions and projects require integrations between software systems; as well as [Account](/overview-of-cis18-critical-security-controls/cis05-account-management/) and [Access Control](/overview-of-cis18-critical-security-controls/cis06-access-control-management/) since non-human identities, proper scoping of access levels and permissions, and BYOID/SSO are often important elements of such projects. 

## MITRE ATT&CK Techniques Mitigated 

**ATT&CK Relevance:** Directly counters Execution tactics (T1204, T1059) and Persistence via trojaned software (T1554). Application allowlisting is one of the single most effective controls against malware execution, although in large and complex environments and ecosystems it can prove elusive at times. This is where control of software assets will often lead into the [Malware Defence](/overview-of-cis18-critical-security-controls/cis10-malware-defenses/) and [Incident Response](/overview-of-cis18-critical-security-controls/cis17-incident-response-management/) topics.  

## Solutions and Products 

**Solution Categories and Example Brands:**

| Solution Category | What It Does | Example Brands |
|---|---|---|
| Software Asset Management (SAM) | Tracks installed software, versions, and license compliance | Flexera, Snow Software, ServiceNow SAM |
| Application Control / Allowlisting | Prevents unauthorized executables from running | Microsoft AppLocker / WDAC, Carbon Black App Control, Airlock Digital, ThreatLocker |
| Endpoint Management / UEM | Deploys, patches, and manages software across endpoints | Microsoft Intune, Jamf, SCCM, NinjaOne |

## Key Points

**Implementation Tip:** As pointed out above, application allowlisting is often viewed as too difficult to implement broadly, at least in the beginning. Start in audit mode — log what would be blocked without actually blocking it. This builds your baseline. Then roll out enforcement to high-value targets (servers, privileged workstations) first, using that baseline, and expand from there.

---
