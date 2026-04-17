---
layout: page
title: 'Overview of CIS18 Critical Security Controls'
permalink: /overview-of-cis18-critical-security-controls/
share-description: 'A structured walkthrough of CIS18 and the controls that reduce common risk.'
nav_category: 'Security Controls'
section_number: 5
---
For a general overview of the CIS18 controls and how they align with MITRE ATT&CK, check out [this](/overview-of-cis18-critical-security-controls/mitre-att-and-ck-and-cis18/) section.

For a more detailed look, check out the articles we have assembled for each control, organized by:
 - Logical groupings of controls, according to how you may want to think of them when building out a security program.
 - Controls listed in proper order, as they appear in CIS18. 

Note that this section is: **Still Under Construction**

## Logical Flow of Applying CIS18 Controls (According to Mike)

It has always been helpful for me, to think of these controls in a more logical grouping, aligned with how we build and manage a security program. Here is a logical grouping that may help you organize control categories, in a way that helps build out a strategy for effective defense. 

### Finding and Protecting Assets

It is frequently said that you cannot protect what you do not know about.  These controls including knowing what enterprise assets exist in your environment, what software is in use (including Cloud), and making sure both are configured properly.  

[CIS01 - Inventory and Control of Enterprise Assets](/overview-of-cis18-critical-security-controls/cis01-inventory-and-control-of-enterprise-assets/)

[CIS02 - Inventory and Control of Software Assets](/overview-of-cis18-critical-security-controls/cis02-inventory-and-control-of-software-assets/)

[CIS04 - Secure Configuration of Enterprise Assets and Software](/overview-of-cis18-critical-security-controls/cis04-secure-configuration-of-enterprise-assets-and-software/)

### Protecting Data

These controls relate to understanding what data you have, where it exists, and how to protect and recover that data.  

[CIS03 - Data Protection](/overview-of-cis18-critical-security-controls/cis03-data-protection/)


[CIS11 - Data Recovery](/overview-of-cis18-critical-security-controls/cis11-data-recovery/)


### Identity and Access Management 

Controls related to identity and access, including account lifecycle management, privildged access, single sign-on, and secure authentication principles such as multi-factor authentication (MFA) and zero trust network access (ZTNA).

[CIS05 - Account Management](/overview-of-cis18-critical-security-controls/cis05-account-management/)

[CIS06 - Access Control Management](/overview-of-cis18-critical-security-controls/cis06-access-control-management/)

### Managing Vulnerabilities and Risks

These controls include understanding and managing vulnerabilities across assets, software, and infrastructure - as well as, secure development and managing third-party service providers. Finally, this section includes the broad category of penetration testing, which includes red/purple team work, assume breach, adversary emulation, and other methods to provide assurance that expected vs actual performance of the defensive posture are in alignment. 

[CIS07 - Continuous Vulnerability Management](/overview-of-cis18-critical-security-controls/cis07-continuous-vulnerability-management/)

[CIS16 - Application Software Security](/overview-of-cis18-critical-security-controls/cis16-application-software-security/)

[CIS18 - Penetration Testing](/overview-of-cis18-critical-security-controls/cis18-penetration-testing/)

[CIS15 - Service Provider Management](/overview-of-cis18-critical-security-controls/cis15-service-provider-management/)

### Email and Web Protections

These controls relate to protecting against attacks that come inbound via email, chat, compromised web sites, or other methods involving a user. They often involve a user taking one of these actions:
 - Clicking a link.
 - Opening an attachment.
 - Visiting a compromised or attacker controlled web site.
 - Plugging in a USB or other malicious device.
 - Running malicious software (marketplace or social engineering).
 - Giving up an MFA token. 

[CIS09 - Email and Web Browser Protections](/overview-of-cis18-critical-security-controls/cis09-email-and-web-browser-protections/)

[CIS14 - Security Awareness and Skills Training](/overview-of-cis18-critical-security-controls/cis14-security-awareness-and-skills-training/)

### Network Defense

These controls relate to how a network is setup and what attack opportunities it may provide, as well as monitoring for when something suspicious happens on the network.  

[CIS12 - Network Infrastructure Management](/overview-of-cis18-critical-security-controls/cis12-network-infrastructure-management/)

[CIS13 - Network Monitoring and Defense](/overview-of-cis18-critical-security-controls/cis13-network-monitoring-and-defense/)

### Detection and Response

Controls related to seeing attacks and issues, prioritizing, and responding to / escalating as needed.

[CIS17 - Incident Response Management](/overview-of-cis18-critical-security-controls/cis17-incident-response-management/)

[CIS08 - Log Management](/overview-of-cis18-critical-security-controls/cis08-audit-log-management/)

### Malware Defense 

This section outlines controls specific to stopping malware, such as antivirus, endpoint detection and response (EDR), and malware sandboxing.

[CIS10 - Malware Defenses](/overview-of-cis18-critical-security-controls/cis10-malware-defenses/)

# Listing of CIS18 Controls 
## (In Sequential Order)

[CIS01 - Inventory and Control of Enterprise Assets](/overview-of-cis18-critical-security-controls/cis01-inventory-and-control-of-enterprise-assets/)

[CIS02 - Inventory and Control of Software Assets](/overview-of-cis18-critical-security-controls/cis02-inventory-and-control-of-software-assets/)

[CIS03 - Data Protection](/overview-of-cis18-critical-security-controls/cis03-data-protection/)

[CIS04 - Secure Configuration of Enterprise Assets and Software](/overview-of-cis18-critical-security-controls/cis04-secure-configuration-of-enterprise-assets-and-software/)

[CIS05 - Account Management](/overview-of-cis18-critical-security-controls/cis05-account-management/)

[CIS06 - Access Control Management](/overview-of-cis18-critical-security-controls/cis06-access-control-management/)

[CIS07 - Continuous Vulnerability Management](/overview-of-cis18-critical-security-controls/cis07-continuous-vulnerability-management/)

[CIS08 - Log Management](/overview-of-cis18-critical-security-controls/cis08-audit-log-management/)

[CIS09 - Email and Web Browser Protections](/overview-of-cis18-critical-security-controls/cis09-email-and-web-browser-protections/)

[CIS10 - Malware Defenses](/overview-of-cis18-critical-security-controls/cis10-malware-defenses/)

[CIS11 - Data Recovery](/overview-of-cis18-critical-security-controls/cis11-data-recovery/)

[CIS12 - Network Infrastructure Management](/overview-of-cis18-critical-security-controls/cis12-network-infrastructure-management/)

[CIS13 - Network Monitoring and Defense](/overview-of-cis18-critical-security-controls/cis13-network-monitoring-and-defense/)

[CIS14 - Security Awareness and Skills Training](/overview-of-cis18-critical-security-controls/cis14-security-awareness-and-skills-training/)

[CIS15 - Service Provider Management](/overview-of-cis18-critical-security-controls/cis15-service-provider-management/)

[CIS16 - Application Software Security](/overview-of-cis18-critical-security-controls/cis16-application-software-security/)

[CIS17 - Incident Response Management](/overview-of-cis18-critical-security-controls/cis17-incident-response-management/)

[CIS18 - Penetration Testing](/overview-of-cis18-critical-security-controls/cis18-penetration-testing/)

## Resources and References 

[CIS Critical Security Controls](https://www.cisecurity.org/controls)

[MITRE ATT&CK](https://attack.mitre.org/)

## Additional Pages in This Section

- [CIS 18 Security Controls: A Strategic Planning Guide for the Modern Enterprise](/overview-of-cis18-critical-security-controls/mitre-att-and-ck-and-cis18/)
- [CIS Control 10: Malware Defenses](/overview-of-cis18-critical-security-controls/cis10-malware-defenses/)
- [CIS Control 11: Data Recovery](/overview-of-cis18-critical-security-controls/cis11-data-recovery/)
- [CIS Control 12: Network Infrastructure Management](/overview-of-cis18-critical-security-controls/cis12-network-infrastructure-management/)
- [CIS Control 13: Network Monitoring and Defense](/overview-of-cis18-critical-security-controls/cis13-network-monitoring-and-defense/)
- [CIS Control 14: Security Awareness and Skills Training](/overview-of-cis18-critical-security-controls/cis14-security-awareness-and-skills-training/)
- [CIS Control 15: Service Provider Management](/overview-of-cis18-critical-security-controls/cis15-service-provider-management/)
- [CIS Control 16: Application Software Security](/overview-of-cis18-critical-security-controls/cis16-application-software-security/)
- [CIS Control 17: Incident Response Management](/overview-of-cis18-critical-security-controls/cis17-incident-response-management/)
- [CIS Control 18: Penetration Testing](/overview-of-cis18-critical-security-controls/cis18-penetration-testing/)
- [CIS Control 1: Inventory and Control of Enterprise Assets](/overview-of-cis18-critical-security-controls/cis01-inventory-and-control-of-enterprise-assets/)
- [CIS Control 2: Inventory and Control of Software Assets](/overview-of-cis18-critical-security-controls/cis02-inventory-and-control-of-software-assets/)
- [CIS Control 3: Data Protection](/overview-of-cis18-critical-security-controls/cis03-data-protection/)
- [CIS Control 4: Secure Configuration of Enterprise Assets and Software](/overview-of-cis18-critical-security-controls/cis04-secure-configuration-of-enterprise-assets-and-software/)
- [CIS Control 5: Account Management](/overview-of-cis18-critical-security-controls/cis05-account-management/)
- [CIS Control 6: Access Control Management](/overview-of-cis18-critical-security-controls/cis06-access-control-management/)
- [CIS Control 7: Continuous Vulnerability Management](/overview-of-cis18-critical-security-controls/cis07-continuous-vulnerability-management/)
- [CIS Control 8: Audit Log Management](/overview-of-cis18-critical-security-controls/cis08-audit-log-management/)
- [CIS Control 9: Email and Web Browser Protections](/overview-of-cis18-critical-security-controls/cis09-email-and-web-browser-protections/)
- [Overview of CIS18 Critical Security Controls](/overview-of-cis18-critical-security-controls/basic-high-level-overview/)

Previous: [Mapping Attack Surface](/mapping-your-attack-surface/)

Next: [Security Architecture and Engineering](/security-architecture-and-engineering/)
