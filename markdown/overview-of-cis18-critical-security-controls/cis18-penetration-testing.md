<!-- ciso-in-a-box
canonical_url: https://ciso-in-a-box.github.io/ciso-in-a-box-site/overview-of-cis18-critical-security-controls/cis18-penetration-testing/
source_repository: https://github.com/CroodSolutions/CISOinaBox
source_path: 05 - CIS18 and Basic Security Controls/CIS18 - Penetration Testing.md
source_commit: 2882c6067c3aa748d66152fb90540d71d74349da
-->
### CIS Control 18: Penetration Testing

**What it requires:** Test the effectiveness and resiliency of enterprise assets through identifying and exploiting weaknesses in controls (people, processes, and technology), and simulating the objectives and actions of an attacker.

**ATT&CK Relevance:** Penetration testing validates the effectiveness of every other control by simulating real adversary behavior across the full ATT&CK matrix. Red teams specifically map their operations to ATT&CK techniques to measure defensive coverage.

**Solution Categories and Leading Brands:**

| Solution Category | What It Does | Leading Brands |
|---|---|---|
| Penetration Testing Services | Expert-led testing of networks, applications, and people | Bishop Fox, SecurIT360, Rapid7, NetSPI, Coalfire, Cobalt |
| Breach and Attack Simulation (BAS) | Continuous, automated testing of security controls | AttackIQ, SafeBreach, Cymulate, Picus Security |
| Red Team / Adversary Emulation | Simulates real threat actor TTPs against the environment | MITRE Caldera (open source), Atomic Red Team (open source), Cobalt Strike (Fortra), Brute Ratel, BeaconatorC2 |
| Attack Surface Management (ASM) | Discovers and tests the external attack surface continuously | Censys, Ionix, Shodan, Mandiant ASM, CrowdStrike Falcon Surface |

**Implementation Tip:** Breach and Attack Simulation (BAS) platforms are the force multiplier that connects CIS 18 to MITRE ATT&CK operationally. These tools continuously simulate specific ATT&CK techniques against your production environment and tell you, per technique, whether your SIEM detected it, whether your EDR blocked it, and whether your firewall filtered it. This gives you a quantifiable coverage map: "We detect 78% of ATT&CK techniques. Here are the 22% where we have gaps." That drives your investment roadmap.

---
