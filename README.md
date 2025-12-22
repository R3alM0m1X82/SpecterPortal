# SpecterPortal 
<img width="1536" height="1024" alt="Logo Alternative Scure_remix_01kawz4dc0edtsgjw9f0f9xwv2" src="https://github.com/user-attachments/assets/04d48310-f803-4662-8625-648703a1c38e" />

<div align="center">

**Security Platform for Entra Cloud Token Enumeration & Reconnaissance**
  

**[#] by r3alm0m1x82 - safebreach.it [#]**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-red?style=flat)](LICENSE)

---

**[Features](#key-features) • [Installation](#installation) • [Authentication](#authentication) • [Roadmap](#roadmap)**

</div>

---

## Overview

**SpecterPortal** is an advanced post-exploitation framework designed for Red Team operations in Entra ID, Azure and Microsoft 365 environments. Unlike basic enumeration tools, SpecterPortal provides a **complete offensive platform** with token management, deep content analysis, resource abuse capabilities, and privilege escalation vectors.

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
<img width="2492" height="1016" alt="image" src="https://github.com/user-attachments/assets/cc2cf174-a368-4b84-8b76-1baa8b41bda8" />

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
<img width="1586" height="762" alt="image" src="https://github.com/user-attachments/assets/0222e68c-e450-4e1e-b383-cffbcaf2cdc4" />

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
<img width="2482" height="1006" alt="image" src="https://github.com/user-attachments/assets/1e694e74-0d8b-4c4c-a1ca-d007cf52516e" />

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
<img width="2517" height="908" alt="image" src="https://github.com/user-attachments/assets/77a5eecd-cfac-42e7-a941-771996e29c27" />

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
<img width="2493" height="996" alt="image" src="https://github.com/user-attachments/assets/e4ff7962-78a6-4131-8de7-290ded80e4bf" />
- Complete enumeration: Users, Groups, Devices, Contacts
- Guest account identification with external domain tracking
- On-premises sync status
- MFA status per user
- **Owned Objects**: User-owned apps, groups, devices
- CSV/JSON export capabilities

**Application Analysis:**
<img width="2477" height="971" alt="image" src="https://github.com/user-attachments/assets/66d56a62-976e-4200-9d4c-e762a1c510e4" />

- App Registration enumeration with owners
- Service Principal analysis
- **Managed Identity detection** (System/User-assigned)
- OAuth consent grants tracking
- Permission scope analysis (Delegated vs Application)
- **Client Secret & Certificate inventory** with expiration tracking
- App role assignments

**Privileged Access:**
<img width="2489" height="960" alt="image" src="https://github.com/user-attachments/assets/c42000ae-babb-452e-ba0a-14c1b3aad4b3" />

- Directory role enumeration with members
- **Administrative Unit nested roles** (not visible in JWT wids)
- Built-in vs custom role identification
- License tracking (E3, E5, F3, etc.)

**Tenant Configuration:**
<img width="2484" height="1008" alt="image" src="https://github.com/user-attachments/assets/a0c9e096-080f-427e-ac02-5ce30e51335a" />

- Custom domain enumeration
- Authentication methods analysis
- **Authorization Policy extraction** (guest rules, default permissions)
- Security defaults status


**Conditional Access Policies:**
<img width="2485" height="941" alt="image" src="https://github.com/user-attachments/assets/3d1fbf71-998a-40f6-9ba8-1c032507fff6" />

- **Permission-less extraction** using legacy API technique
- **Complete policy enumeration without Directory.Read permissions**
<img width="2495" height="807" alt="image" src="https://github.com/user-attachments/assets/1c516a27-3ef6-4fb4-8d8f-5a2836e4085e" />

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
cd SpecterPortal\backend
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
<img width="1443" height="1033" alt="image" src="https://github.com/user-attachments/assets/bfd85427-8d70-4965-9089-a3419197f3b9" />

Backend runs on `http://127.0.0.1:5000`

**5. Start the frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```
<img width="730" height="235" alt="image" src="https://github.com/user-attachments/assets/d2762933-48e8-4722-beef-832198b2b523" />

Frontend runs on `http://localhost:5173`

**6. Access the application:**
Open your browser and navigate to `http://localhost:5173`
<img width="2319" height="989" alt="image" src="https://github.com/user-attachments/assets/2343cbae-c9ab-48a5-a53c-b154bda1f0d2" />

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

## 💙 Support This Project

This project is developed with passion during nights and weekends alongside a full-time job. If you find it valuable, consider supporting its development:

[![Sponsor](https://img.shields.io/badge/💙_Become_a_Sponsor-blue?style=for-the-badge)](https://github.com/sponsors/R3alM0m1X82)
[![PayPal](https://img.shields.io/badge/☕_PayPal_Donation-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mohammedbellala)

Your support enables:
- ⚡ Faster feature development
- 🛠️ Better tools and documentation
- 🎓 Educational content for the community

See all [sponsorship tiers and benefits →](./SPONSORS.md)

---

## 🙏 Credits - Inspiration & Research

This tool is based on the inspiration of:

- **GrapSpy** by RedByte1337
- **TokenTactics v2** by f-bader
- **ROADtools** by Dirk-jan Mollema 

---

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
