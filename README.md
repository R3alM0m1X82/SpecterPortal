# SpecterPortal 

<div align="center">

![SpecterPortal](https://img.shields.io/badge/SPECTER-PORTAL-blueviolet?style=for-the-badge&logo=microsoftazure)

### The Ultimate Post-Exploitation Framework for Azure AD & Microsoft 365

**First-of-its-kind integrated platform for Red Team operations**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-red?style=flat)](LICENSE)

---

**[Features](#key-features) • [Installation](#installation) • [Authentication](#authentication) • [Usage](#usage-examples) • [Roadmap](#roadmap)**

</div>

---

## Overview

**SpecterPortal** is an advanced post-exploitation framework designed for Red Team operations in Azure AD and Microsoft 365 environments. Unlike basic enumeration tools, SpecterPortal provides a **complete offensive platform** with token management, deep content analysis, resource abuse capabilities, and privilege escalation vectors.

**What makes SpecterPortal unique:**
- FOCI token exchange across 36 Microsoft applications
- Permission-less Conditional Access Policy extraction
- Deep OneDrive/Teams secret scanning with pattern detection
- Azure Resource abuse (VM command execution, Managed Identity extraction)
- Complete M365 operations (Email, Calendar, Teams, SharePoint)
- 130+ pre-loaded Application IDs for Device Code Flow

---

## Key Features

### Token Management & Authentication

**Advanced Token Operations:**
- **FOCI Token Exchange**: Generate tokens for 36 FOCI-enabled applications from a single Refresh Token
- **Multi-Audience Generation**: Create Access Tokens for Graph, ARM, KeyVault, Storage, legacy AzureAD
- **Auto-Refresh Scheduler**: Background service monitors and refreshes expiring tokens (configurable 5-30 min)
- **Smart Deduplication**: Prevents duplicate token imports via cache tracking
- **NGC Token Support**: Infrastructure ready for Windows Hello credentials (upcoming)

**Authentication Methods:**
- Device Code Flow with 130+ pre-configured Microsoft Application IDs
- ROPC (Username/Password) with MFA bypass scenarios
- Client Secret authentication for Service Principals
- Manual token import (TBRes cache, WAM Broker, raw JWT)
- SpecterBroker integration for Windows token extraction

**Token Analysis:**
- JWT decoding with claims visualization
- Scope and permission analysis
- Directory role detection (including Administrative Units)
- Microsoft 365 license identification
- FOCI family classification
- Expiration tracking with alerts

### Search & Pattern Detection

**Microsoft Search Integration:**
- Cross-platform search: OneDrive, SharePoint, Emails
- Advanced filtering by sender, recipient, subject, dates
- Attachment enumeration and bulk download

**OneDrive Deep Scanner:**
- Recursive file content analysis (not just metadata)
- Pattern detection: AWS keys, Azure secrets, API tokens, passwords, certificates
- Supported formats: TXT, JSON, XML, CSV, YAML, ENV, CONFIG, LOG
- Severity classification (HIGH/MEDIUM/LOW)
- Export findings with context and file paths

**Teams Secrets Scanner:**
- Message content analysis across conversations and channels
- Credential pattern detection: API keys, tokens, connection strings
- Both Graph API and Skype API support for comprehensive coverage
- Conversation metadata with participant tracking
- Image and attachment support

**Custom Patterns:**
- Configurable regex patterns for organization-specific secrets
- Built-in template library
- Match highlighting and context extraction

### Microsoft 365 Operations

**Email Management:**
- Full folder access (Inbox, Sent, Drafts, Deleted, Junk, Custom)
- HTML email composition with rich formatting
- Reply/Forward with message threading
- Attachment handling (upload/download)
- **Malicious Rule Injection**: Auto-forwarding, keyword monitoring, data exfiltration

**Calendar:**
- Event enumeration with attendee details
- Meeting information extraction
- Injected event tracking
- Calendar manipulation capabilities

**OneDrive:**
- Complete file/folder hierarchy navigation
- Upload, download, rename, delete, move operations
- Batch download with ZIP compression
- Shared file enumeration
- Permission analysis

**SharePoint:**
- Site discovery and access
- Document library enumeration
- Advanced file search
- Content download with permission validation

**Teams:**
- Channel and Team enumeration
- Message history retrieval (Graph + Skype APIs)
- Participant lists and presence
- Image/attachment rendering
- Private chat access

### Entra ID Enumeration

**Directory Intelligence:**
- Complete enumeration: Users, Groups, Devices, Contacts
- Guest account identification with external domain tracking
- On-premises sync status
- MFA status per user
- **Owned Objects**: User-owned apps, groups, devices
- CSV/JSON export capabilities

**Application Analysis:**
- App Registration enumeration with owners
- Service Principal analysis
- **Managed Identity detection** (System/User-assigned)
- OAuth consent grants tracking
- Permission scope analysis (Delegated vs Application)
- **Client Secret & Certificate inventory** with expiration tracking
- App role assignments

**Privileged Access:**
- Directory role enumeration with members
- **Administrative Unit nested roles** (not visible in JWT wids)
- Built-in vs custom role identification
- License tracking (E3, E5, F3, etc.)
- PIM eligible roles

**Tenant Configuration:**
- Custom domain enumeration
- Authentication methods analysis
- **Authorization Policy extraction** (guest rules, default permissions)
- Security defaults status
- External collaboration settings

**Conditional Access Policies:**
- **Permission-less extraction** using legacy API technique
- Complete policy enumeration without Directory.Read permissions
- Policy conditions: users, groups, locations, platforms
- Grant and session controls analysis
- Policy state identification (Enabled/Disabled/Report-Only)

### Azure Resource Operations

**Permission Analysis:**
- Role assignments per subscription (Owner, Contributor, Reader, custom)
- Resource group permissions
- Inherited vs direct assignments
- Deny assignments detection

**Virtual Machines:**
- VM inventory with status tracking
- **Remote Command Execution** via Run Command API
- **Managed Identity Token Extraction** from VM metadata endpoint
- Power operations: Start, Stop, Restart, Deallocate
- OS and configuration details

**Storage Accounts:**
- Storage enumeration across subscriptions
- **Firewall rule analysis** (public vs restricted)
- **Anonymous blob detection** for data exposure
- Service configuration (Blob, File, Queue, Table)
- Access tier and replication settings

**Key Vaults:**
- Vault enumeration with access policies
- **Secret extraction** (with appropriate permissions)
- **Certificate download** with private keys
- Key metadata and operations
- Access policy analysis per identity

**SQL Databases:**
- SQL Server and Database discovery
- Connection string construction
- Firewall rule enumeration
- Credential recovery via Key Vault integration

**App Services & Functions:**
- Web app enumeration with runtime details
- **Application settings extraction** (secrets, connection strings)
- Deployment credential recovery
- Managed Identity configuration

**Automation Accounts:**
- Runbook enumeration and source code access
- **Runbook execution** capabilities
- **Hybrid Worker Group abuse** for on-premises access
- Automation credentials and variables
- Schedule manipulation

### Advanced Capabilities

**Custom API Queries:**
- Direct Microsoft Graph queries
- Azure Resource Manager REST calls
- Key Vault and Storage API access
- Built-in template library (10+ queries)
- Query history with parameter persistence
- Raw JSON response inspection

**Administrative Actions:**
Requires appropriate permissions:
- User creation and deletion
- Password reset (including privileged accounts)
- **Temporary Access Pass (TAP)** generation for MFA bypass
- MFA enable/disable operations
- Group membership management
- Directory role assignments

**Dashboard:**
- Real-time database statistics
- Active token visualization with scopes
- Auto-refresh scheduler status
- Token expiration monitoring
- Quick access to critical operations

---

## Installation

### Requirements

- Python 3.9 or higher
- Node.js 16 or higher
- Git

### Setup Instructions

**1. Clone the repository:**
```bash
git clone https://github.com/r3alm0m1x82/SpecterPortal.git
cd SpecterPortal
```

**2. Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**3. Install Node.js dependencies:**
```bash
cd frontend
npm install
cd ..
```

**4. Start the backend (Terminal 1):**
```bash
python app.py
```
Backend runs on `http://127.0.0.1:5000`

**5. Start the frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:5173`

**6. Access the application:**
Open your browser and navigate to `http://localhost:5173`

---

## Authentication

### Device Code Flow (Recommended)

Most versatile method with 130+ pre-loaded Application IDs:

1. Navigate to **Tokens** → **Authenticate**
2. Select **Device Code Flow**
3. Choose application (Office, Teams, Azure Portal, etc.)
4. Complete browser authentication
5. Tokens imported automatically

### Token Import

**Using SpecterBroker:**
```powershell
# Extract tokens from Windows
.\SpecterBroker.exe

# Import into SpecterPortal
Tokens → Import JSON → Select cache_export_*.json
```

**Supported formats:**
- TBRes cache files
- WAM Broker tokens
- Raw JWT (paste directly)

### ROPC Authentication

Username/password flow:
1. Navigate to **Tokens** → **Authenticate**
2. Select **ROPC**
3. Enter credentials
4. May bypass certain MFA configurations

### Client Secret

Service Principal authentication:
1. Navigate to **Tokens** → **Authenticate**
2. Select **Client Secret**
3. Provide Tenant ID, Client ID, Secret
4. Generate tokens for app permissions

---

## Usage Examples

### FOCI Token Exchange

Convert a single Refresh Token into multiple application tokens:

1. Obtain initial Refresh Token (any FOCI app)
2. **Tokens** → Select token → **FOCI Exchange**
3. Generate tokens for 36 applications
4. Create Access Tokens for different audiences

**Applications:** Office, Teams, Outlook, OneDrive, Azure Portal, VS Code, Graph Explorer, PowerBI, etc.

### Conditional Access Enumeration Without Permissions

Extract policies without Directory.Read permissions:

1. Navigate to **Graph** → **Tenant Info**
2. Click **Authorization Policy** tab
3. View **Conditional Access** section
4. Policies extracted using legacy API technique

**Technical detail:** Uses `/.default` scope with deprecated endpoint to bypass Graph permission requirements.

### Managed Identity Token Extraction

Escalate from VM access to data plane permissions:

1. **Azure Resources** → **Virtual Machines**
2. Select VM with Managed Identity assigned
3. Run command: 
```bash
curl -H Metadata:true "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://graph.microsoft.com"
```
4. Extract Access Token from response
5. Import token into SpecterPortal

**Use case:** VM Contributor → Storage Blob Data Reader/Contributor

### Automation Runbook Abuse

Lateral movement from Azure to on-premises:

1. **Azure Resources** → **Automation Accounts**
2. Select account with Hybrid Worker Groups configured
3. Create or modify runbook with malicious payload
4. Execute runbook on Hybrid Worker
5. Commands execute on on-premises systems

**Use case:** Cloud-to-on-prem lateral movement, credential harvesting, persistence

### Email Rule Persistence

Maintain access after credential reset:

1. **MS 365** → **Emails** → **Rules**
2. Create forwarding rule with keywords
3. Example: Forward emails containing "password", "code", "verification"
4. Destination: attacker-controlled email
5. Rule persists after password changes

**Detection difficulty:** High - User-configurable feature rarely monitored

---

## Detection & Defense

### Blue Team Indicators

**Token Abuse Signals:**
- Unusual Application IDs in Azure AD sign-in logs
- Token requests from unexpected geolocations
- Multiple audience requests in short timeframe
- FOCI token exchange patterns
- Legacy authentication protocol usage

**Azure Resource Abuse:**
- VM Run Command executions (`AzureActivity` logs)
- Managed Identity token requests (169.254.169.254 access)
- Automation runbook modifications
- Key Vault secret access from non-standard sources
- Storage blob enumeration spikes

**M365 Abuse:**
- Inbox rule creation events (especially forwarding)
- Bulk OneDrive file downloads
- Unusual Graph API query patterns
- High-volume email searches
- Calendar rule modifications

### Defensive Recommendations

**Conditional Access:**
- Require MFA for all users
- Enforce compliant device requirements
- Implement location-based policies
- Block legacy authentication protocols

**Azure Resources:**
- Enable VM Just-In-Time access
- Restrict Run Command to specific IPs
- Implement Key Vault firewall rules
- Monitor Managed Identity token requests
- Review Automation Account permissions regularly

**M365 Monitoring:**
- Alert on inbox rule creation
- Monitor bulk download activities
- Track OAuth app consent grants
- Review mailbox forwarding configurations
- Enable unified audit logging

**Token Protection:**
- Implement Conditional Access device compliance
- Use Windows Hello for Business
- Enable Token Protection policies
- Monitor refresh token usage patterns
- Implement certificate-based authentication

---

## Operational Use Cases

### Attack Chain Examples

**Initial Access → Privilege Escalation:**
```
1. Phished credentials → Device Code Flow token
2. Enumerate directory roles → Identify privileged users
3. Target user owns App Registration → Extract client secret
4. Authenticate as application → Application permissions
5. Grant Directory.ReadWrite.All → Full tenant control
```

**Azure → M365 Lateral Movement:**
```
1. VM Contributor access → Run Command execution
2. Extract Managed Identity token → Storage access
3. Discover OneDrive sync folder → Access user files
4. Extract cached Refresh Token → M365 access
5. Email rule persistence → Maintain access
```

**Cloud → On-Premises:**
```
1. Automation Account access → Runbook modification
2. Hybrid Worker Group identified → On-prem connection
3. Malicious runbook execution → Domain credential dump
4. Lateral movement tools deployed → Persistent access
5. Export sensitive data → Cloud exfiltration
```

---

## Training & Education

SpecterPortal was developed for **SafeBreach Academy** Red Team training programs in corporate environments (500+ endpoints). The platform teaches:

- OAuth 2.0 and token-based authentication security
- Azure AD attack paths and privilege escalation
- Post-exploitation techniques in cloud environments
- Defensive countermeasures and detection strategies
- Lateral movement between cloud and on-premises

**Training scenarios:**
- Token acquisition and manipulation
- Permission enumeration and abuse
- Data exfiltration techniques
- Persistence mechanisms
- Detection evasion strategies

---

## Roadmap

### Version 2.1 (Q1 2025)
- Full NGC token support for Windows Hello credential theft
- PRT (Primary Refresh Token) extraction capabilities
- Enhanced Conditional Access Policy risk scoring
- Azure Blob Storage enumeration module
- Improved Graph API rate limiting handling

### Version 2.2 (Q2 2025)
- Automated attack chains (initial access → domain admin)
- Teams file content secret scanning
- Multi-factor authentication bypass techniques
- PowerShell Empire integration
- Custom exfiltration channels

### Version 3.0 (Q3 2025)
- Multi-tenant campaign management
- Collaborative Red Team features
- Custom plugin system for extensibility
- Advanced reporting with MITRE ATT&CK mapping
- AI-powered attack path discovery

---

## Comparison with Other Tools

| Feature | SpecterPortal | GraphSpy | AADInternals | ROADtools |
|---------|--------------|----------|--------------|-----------|
| Token Management | **Advanced** | Basic | CLI Only | None |
| FOCI Exchange | **✓** | ✗ | ✗ | ✗ |
| Auto-Refresh | **✓** | ✗ | ✗ | ✗ |
| Secret Scanning | **Deep** | ✗ | ✗ | ✗ |
| Azure Resources | **Full** | Basic | Partial | ✗ |
| M365 Operations | **Complete** | Basic | Partial | ✗ |
| CAP No-Perms | **✓** | ✗ | ✗ | **✓** |
| GUI | **✓** | CLI | PowerShell | CLI |
| Active Development | **✓** | ✗ | **✓** | **✓** |

---

## Responsible Use

### Legal Notice

**AUTHORIZED TESTING ONLY**

This tool is intended exclusively for:
- Authorized penetration testing with written consent
- Red Team engagements within defined scope
- Security research in controlled environments
- Corporate security training programs

### User Responsibilities

Users must:
1. Obtain written authorization before testing any system
2. Operate strictly within the defined scope of engagement
3. Follow responsible disclosure practices for discovered vulnerabilities
4. Comply with all applicable local and international laws
5. Document all activities professionally
6. Protect sensitive data discovered during testing

### Legal Warning

**Unauthorized access to computer systems is illegal and may result in criminal prosecution.**

The author and contributors:
- Assume no liability for misuse of this software
- Do not authorize or encourage illegal activities
- Provide this tool for legitimate security research only
- Are not responsible for any damages caused by users

**Use at your own risk. Know your laws. Get authorization.**

---

## Related Projects

- **[SpecterBroker](https://github.com/r3alm0m1x82/SpecterBroker)** - Windows token extraction (TBRes/WAM Broker)
- **[AADInternals](https://github.com/Gerenios/AADInternals)** - Azure AD management PowerShell module
- **[ROADtools](https://github.com/dirkjanm/ROADtools)** - Azure AD reconnaissance framework
- **[TokenTactics](https://github.com/rvrsh3ll/TokenTactics)** - Azure AD token manipulation toolkit
- **[GraphRunner](https://github.com/dafthack/GraphRunner)** - Microsoft Graph post-exploitation toolset
- **[MicroBurst](https://github.com/NetSPI/MicroBurst)** - Azure security assessment PowerShell toolkit

---

## Author

**Mohammed (r3alm0m1x82)**  
Red Team Operator & Security Researcher  
[SafeBreach Academy](https://safebreach.it)

**GitHub:** [@r3alm0m1x82](https://github.com/r3alm0m1x82)

For security research collaboration or responsible disclosure, contact via GitHub.

---

## Acknowledgments

Special thanks to:
- **SafeBreach Academy** students and instructors for operational feedback
- **Microsoft Security Research** for comprehensive Azure documentation
- **ROADtools** project for CAP extraction techniques
- **AADInternals** for Entra ID internals insights
- **The offensive security community** for continuous innovation

Recognition to all red teamers who provided real-world validation during development.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

**Disclaimer:** This software is provided "as is" without warranty of any kind. The author is not responsible for any damage or misuse resulting from the use of this software.

---

<div align="center">

### Star this repository if SpecterPortal enhances your Red Team operations

**Made with 💜 for the offensive security community**

*"The most comprehensive Azure AD post-exploitation framework available"*

</div>
