"""
Microsoft Client ID to Application Name Mapping
Full FOCI (Family of Client IDs) list from Secureworks Research
Source: https://github.com/secureworks/family-of-client-ids-research
"""

# FOCI Applications - Can share refresh tokens across family
# Sorted alphabetically by application name
FOCI_APPS = {
    'a40d7d7d-59aa-447e-a655-679a4107e548': 'Accounts Control UI',
    '14638111-3389-403d-b206-a6a71d9f8f16': 'Copilot App',
    '598ab7bb-a59c-4d31-ba84-ded22c220dbd': 'Designer App',  # NEW - Has Chat.Read scope
    'cde6adac-58fd-4b78-8d6d-9beaf1b0d668': 'Global Secure Access Client',
    'be1918be-3fe3-4be9-b32b-b542fc27f02e': 'M365 Compliance Drive Client',
    'eb20f3e3-3dce-4d2c-b721-ebb8d4414067': 'Managed Meeting Rooms',
    '04b07795-8ddb-461a-bbee-02f9e1bf7b46': 'Microsoft Azure CLI',
    '1950a258-227b-4e31-a9cf-717495945fc2': 'Microsoft Azure PowerShell',
    '4813382a-8fa7-425e-ab75-3b753aab3abb': 'Microsoft Authenticator App',
    '2d7f3606-b07d-41d1-b9d2-0d0c9296a6e8': 'Microsoft Bing Search for Microsoft Edge',
    'cf36b471-5b44-428c-9ce7-313bf84528de': 'Microsoft Bing Search',
    'cab96880-db5b-4e15-90a7-f3f1d62ffe39': 'Microsoft Defender Platform',
    'dd47d17a-3194-4d86-bfd5-c6ae6f5651e3': 'Microsoft Defender for Mobile',
    'e9c51622-460d-4d3d-952d-966a5b1da34c': 'Microsoft Edge',
    'd7b530a4-7680-4c23-a8bf-c52c121d2e87': 'Microsoft Edge Enterprise New Tab Page',
    '82864fa0-ed49-4711-8395-a0e6003dca1f': 'Microsoft Edge MSAv2',
    'ecd6b820-32c2-49b6-98a6-444530e5a77a': 'Microsoft Edge (variant 2)',
    'f44b1140-bc5e-48c6-8dc0-5cf5a53c0e34': 'Microsoft Edge (variant 3)',
    '57fcbcfa-7cee-4eb1-8b25-12d2030b4ee0': 'Microsoft Flow',
    '9ba1a5c7-f17a-4de9-a1f1-6178c8d51223': 'Microsoft Intune Company Portal',
    'a670efe7-64b6-454f-9ae9-4f1cf27aba58': 'Microsoft Lists App on Android',
    '0922ef46-e1b9-4f7e-9134-9ad00547eb41': 'Microsoft Loop',
    'd3590ed6-52b3-4102-aeff-aad2292ab01c': 'Microsoft Office',
    '66375f6b-983f-4c2c-9701-d680650f588f': 'Microsoft Planner',
    'c0d2a505-13b8-4ae0-aa9e-cddd5eab0b12': 'Microsoft Power BI',
    '844cca35-0656-46ce-b636-13f48b0eecbd': 'Microsoft Stream Mobile Native',
    '1fec8e78-bce4-4aaf-ab1b-5451cc387264': 'Microsoft Teams',
    '87749df4-7ccf-48f8-aa87-704bad0e0e16': 'Microsoft Teams - Device Admin Agent',
    '8ec6bc83-69c8-4392-8f08-b3c986009232': 'Microsoft Teams-T4L',
    '22098786-6e16-43cc-a27d-191a01a1e3b5': 'Microsoft To-Do client',
    'eb539595-3fe1-474e-9c1d-feb3625d1be5': 'Microsoft Tunnel',
    '57336123-6e14-4acc-8dcf-287b6088aa28': 'Microsoft Whiteboard Client',
    '540d4ff4-b4c0-44c1-bd06-cab1782d582a': 'ODSP Mobile Lists App',
    '00b41c95-dab0-4487-9791-b9d2c32c80f2': 'Office 365 Management',
    '0ec893e0-5785-4de6-99da-4ed124e5296c': 'Office UWP PWA',
    'ab9b8c07-8f02-4f72-87fa-80105867a763': 'OneDrive SyncEngine',
    'af124e86-4e96-495a-b70a-90f90ab96707': 'OneDrive iOS App',
    'b26aadf8-566f-4478-926f-589f601d9c74': 'OneDrive',
    'e9b154d0-7658-433b-bb25-6b8e0a8a7c59': 'Outlook Lite',
    '27922004-5251-4030-b22d-91ecd9a37ea4': 'Outlook Mobile',
    '4e291c71-d680-4d0e-9640-0a3358e31177': 'PowerApps',
    'd326c1ce-6cc6-4de2-bebc-4591e5e13ef0': 'SharePoint',
    'f05ff7c9-f75a-4acd-a3b5-f4b6a870245d': 'SharePoint Android',
    '872cd9fa-d31f-45e0-9eab-6e460a02d1f1': 'Visual Studio - Legacy',
    '26a7ee05-5602-4d76-a7ba-eae8b7b67941': 'Windows Search',
    'e9cee14e-f26a-4349-886f-10048e3ef4b8': 'Yammer Android',
    'b87b6fc6-536c-411d-9005-110ee6db77dc': 'Yammer iPad',
    'a569458c-7f2b-45cb-bab9-b7dee514d112': 'Yammer iPhone',
    '038ddad9-5bbe-4f64-b0cd-12434d1e633b': 'ZTNA Network Access Client',
    'd5e23a82-d7e1-4886-af25-27037a0fdc2a': 'ZTNA Network Access Client -- M365',
    '760282b4-0cfc-4952-b467-c8e0298fee16': 'ZTNA Network Access Client -- Private',
}

# Additional known applications (non-FOCI)
OTHER_APPS = {
    '0c1307d4-29d6-4389-a11c-5cbe7f65d7fa': 'Azure Mobile App',  # NOT FOCI
    '29d9ed98-a469-4536-ade2-f981bc1d605e': 'Microsoft Authentication Broker',
    '00000003-0000-0000-c000-000000000000': 'Microsoft Graph',
    'de50c81f-5f80-4771-b66b-cebd28ccdfc1': 'Microsoft Intune',
    '26a4ae64-5862-427f-a9b0-044e62572a4f': 'Intune Company Portal',
    'fc0f3af4-6835-4174-b806-f7db311fd2f3': 'Office Desktop',
    '4765445b-32c6-49b0-83e6-1d93765276ca': 'Office Mobile',
    '268761a2-03f3-40df-8a8b-c3db24145b6b': 'Microsoft Store',
    '4b0964e4-58f1-47f4-a552-e2e1fc56dcd7': 'Microsoft Edge (Legacy)',
}

# CRITICAL: Client ID → Expected Resource/Audience Mapping
# When Microsoft returns JWT with aud=client_id (GUID), we normalize to the resource
RESOURCE_MAP = {
    # Azure Key Vault - CRITICAL FIX
    'cfa8b339-82a2-471a-a3c9-0fc0be7a4093': 'https://vault.azure.net',
    
    # Microsoft Graph
    '00000003-0000-0000-c000-000000000000': 'https://graph.microsoft.com',
    
    # Azure AD Graph (legacy)
    '00000002-0000-0000-c000-000000000000': 'https://graph.windows.net',
    
    # Azure Management
    '797f4846-ba00-4fd7-ba43-dac1f8f63013': 'https://management.azure.com',
    'https://management.core.windows.net/': 'https://management.azure.com',
    
    # Office 365 Exchange
    '00000002-0000-0ff1-ce00-000000000000': 'https://outlook.office365.com',
    
    # SharePoint
    '00000003-0000-0ff1-ce00-000000000000': 'https://microsoft.sharepoint.com',
    
    # Windows Azure Active Directory
    '00000002-0000-0000-c000-000000000000': 'https://graph.windows.net',
}

# Reverse mapping: Resource → Client ID (for lookup)
RESOURCE_TO_CLIENT = {v: k for k, v in RESOURCE_MAP.items()}

# Combined mapping
CLIENT_ID_MAP = {**FOCI_APPS, **OTHER_APPS}

# Alias for backward compatibility
CLIENT_NAMES = CLIENT_ID_MAP
FOCI_CLIENTS = set(FOCI_APPS.keys())


def get_app_name(client_id):
    """Get application name from client ID"""
    return CLIENT_ID_MAP.get(client_id, client_id)


def get_client_name(client_id):
    """Alias for get_app_name() - backward compatibility"""
    return get_app_name(client_id)


def is_foci_app(client_id):
    """Check if client ID is part of FOCI (Family of Client IDs)"""
    return client_id in FOCI_APPS


def is_known_client(client_id):
    """Check if client ID is a known Microsoft app"""
    if not client_id:
        return False
    return client_id in CLIENT_ID_MAP


def get_all_foci_apps():
    """Get list of all FOCI application IDs"""
    return list(FOCI_APPS.keys())


def get_foci_count():
    """Get total count of FOCI apps"""
    return len(FOCI_APPS)


def normalize_audience(audience, requested_scope=None):
    """
    Normalize audience - convert client_id GUID to proper resource URL
    
    When Microsoft returns JWT with aud=client_id instead of resource,
    we normalize it to the expected resource URL.
    
    Args:
        audience: Audience from JWT (could be GUID or URL)
        requested_scope: The scope that was requested (optional, for fallback)
    
    Returns:
        Normalized audience URL
    
    Examples:
        normalize_audience('cfa8b339-82a2-471a-a3c9-0fc0be7a4093')
        → 'https://vault.azure.net'
        
        normalize_audience('https://vault.azure.net')
        → 'https://vault.azure.net'
    """
    if not audience:
        return audience
    
    # Already a URL - return as-is
    if audience.startswith('http://') or audience.startswith('https://'):
        return audience.rstrip('/')
    
    # Check if it's a known client_id that should be mapped
    if audience in RESOURCE_MAP:
        normalized = RESOURCE_MAP[audience]
        print(f"[AUDIENCE FIX] {audience[:8]}... → {normalized}")
        return normalized
    
    # Fallback: try to extract from requested_scope
    if requested_scope:
        # scope format: "https://vault.azure.net/.default"
        if requested_scope.endswith('/.default'):
            resource = requested_scope.replace('/.default', '')
            print(f"[AUDIENCE FIX] Using scope-based: {resource}")
            return resource
        elif requested_scope.startswith('http'):
            return requested_scope.rstrip('/')
    
    # Return original if no mapping found
    return audience


def get_resource_for_client(client_id):
    """Get expected resource/audience for a client_id"""
    return RESOURCE_MAP.get(client_id)
