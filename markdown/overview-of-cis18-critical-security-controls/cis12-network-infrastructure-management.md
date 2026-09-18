<!-- ciso-in-a-box
canonical_url: https://ciso-in-a-box.github.io/ciso-in-a-box-site/overview-of-cis18-critical-security-controls/cis12-network-infrastructure-management/
source_repository: https://github.com/CroodSolutions/CISOinaBox
source_path: 05 - CIS18 and Basic Security Controls/CIS12 - Network Infrastructure Management.md
source_commit: 2882c6067c3aa748d66152fb90540d71d74349da
-->
### CIS Control 12: Network Infrastructure Management

**What it requires:** Establish, implement, and actively manage network devices to prevent attackers from exploiting vulnerable network services and access points.

**ATT&CK Relevance:** Mitigates Lateral Movement (T1021, T1210 — Exploitation of Remote Services), Initial Access via exposed network services (T1133 — External Remote Services), and Defense Evasion through network-level manipulation.

**Solution Categories and Leading Brands:**

| Solution Category | What It Does | Leading Brands |
|---|---|---|
| Next-Generation Firewall (NGFW) | Application-aware, identity-aware perimeter and internal filtering | Palo Alto Networks, Fortinet FortiGate, Cisco Secure Firewall, Check Point |
| Network Access Control (NAC) | Enforces device health and identity before granting network access | Cisco ISE, Aruba ClearPass, Forescout, Portnox |
| Microsegmentation | Enforces granular, workload-level network policies | Illumio, Guardicore (Akamai), VMware NSX, Zscaler Workload Communications |
| SD-WAN / SASE | Secure, optimized WAN connectivity with integrated security | Zscaler, Palo Alto Prisma SASE, Fortinet Secure SD-WAN, Cato Networks |
| Network Configuration Management | Automates and audits network device configurations | Cisco DNA Center, Arista CloudVision, BackBox, SolarWinds NCM |

**Implementation Tip:** Network segmentation is the single most impactful control for limiting lateral movement. At minimum, segment the network into trust zones: user endpoints, servers, production databases, management networks, IoT/OT, and DMZ. The evolution beyond VLANs is microsegmentation, which enforces identity-based policies at the workload level regardless of network topology.

---
