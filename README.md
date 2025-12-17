# SpecterPortal 
<img width="1536" height="1024" alt="Logo Alternative Scure_remix_01kawz4dc0edtsgjw9f0f9xwv2" src="https://github.com/user-attachments/assets/04d48310-f803-4662-8625-648703a1c38e" />

<div align="center">

![SpecterPortal](https://img.shields.io/badge/SPECTER-PORTAL-blueviolet?style=for-the-badge&logo=microsoftazure)

 [+] by r3alm0m1x82 - safebreach.it

**Security Platform for Entra Cloud Token Enumeration & Reconnaissance**


[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-red?style=flat)](LICENSE)

---

**[Features](#key-features) • [Installation](#installation) • [Authentication](#authentication) • [Roadmap](#roadmap)**

</div>

---

## Overview

**SpecterPortal** is an advanced post-exploitation framework designed for Red Team operations in Entra ID and Microsoft 365 environments. Unlike basic enumeration tools, SpecterPortal provides a **complete offensive platform** with token management, deep content analysis, resource abuse capabilities, and privilege escalation vectors.

**What makes SpecterPortal unique:**
- FOCI token exchange across 36 Microsoft applications
- Permission-less Conditional Access Policy extraction
- Deep OneDrive/Teams secret scanning with pattern detection
- Azure Resource abuse (VM command execution, Managed Identity extraction etc..)
- Complete M365 operations (Email, Calendar, Teams, SharePoint etc..)
- 130+ pre-loaded Application IDs for Device Code Flow

---

## ⚠️ Disclaimer

**IMPORTANT - READ CAREFULLY**

This tool is provided **for educational and authorized security testing purposes only**. 

### Legal Notice

- ✅ **Authorized Use Only**: Use only on systems you own or have explicit written permission to test.
- ❌ **Unauthorized Access**: Using this tool without proper authorization may violate the laws of your country.

---

## Key Features

### Token Management & Authentication
<img width="2499" height="1002" alt="image" src="https://github.com/user-attachments/assets/f7f54772-198d-410e-944c-fbf451b45fd6" />



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
<img width="886" height="867" alt="image" src="https://github.com/user-attachments/assets/2228a3b4-5a9c-464f-aa07-7421bdcd72ac" />

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

**Tenant Configuration:**
- Custom domain enumeration
- Authentication methods analysis
- **Authorization Policy extraction** (guest rules, default permissions)
- Security defaults status


**Conditional Access Policies:**
- **Permission-less extraction** using legacy API technique
- **Complete policy enumeration without Directory.Read permissions**
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

**Automation Accounts:**
- Runbook enumeration and source code access
- **Runbook execution** capabilities
- **Hybrid Worker Group abuse** for on-premises access
- Automation credentials and variables
- Schedule manipulation

**SQL Databases:** NOT Complete
- SQL Server and Database discovery
- Connection string construction
- Firewall rule enumeration
- Credential recovery via Key Vault integration

**App Services & Functions:** NOT Complete
- Web app enumeration with runtime details
- **Application settings extraction** (secrets, connection strings)
- Deployment credential recovery
- Managed Identity configuration


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

### Token Import

**Using SpecterBroker:**
- **[SpecterBroker](https://github.com/r3alm0m1x82/SpecterBroker)** - Windows token extraction (TBRes/WAM Broker)
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

### Device Code Flow (Recommended)

Most versatile method with 130+ pre-loaded Application IDs:

1. Navigate to **Tokens** → **Authenticate**
2. Select **Device Code Flow**
3. Choose application (Office, Teams, Azure Portal, etc.)
4. Complete browser authentication
5. Tokens imported automatically


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

## Roadmap

### Version 2.1
- Full NGC token support for Windows Hello credential theft
- PRT (Primary Refresh Token) extraction capabilities
- Enhanced Conditional Access Policy risk scoring

---

## 🙏 Credits - Inspiration & Research

This tool is based on the inspiration of:

- **GrapSpy** by RedByte1337
- **TokenTactics v2** by f-bader
- **ROADtools** by Dirk-jan Mollema 


## 📜 License

```
MIT License

Copyright (c) 2025 r3alm0m1x82

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

**⚠️ Remember: With great power comes great responsibility. Use ethically and legally. ⚠️**

---

*Made with ❤️ for the red team community by r3alm0m1x82*

</div>
