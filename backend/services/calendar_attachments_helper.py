"""
SpecterPortal - Calendar Attachments Helper
Handles cid: image references in event bodies

Location: backend/services/calendar_attachments_helper.py
"""

import re
import base64
import requests
from typing import Dict, Optional


def process_event_body(body_obj, event_id: str, access_token: str) -> str:
    """
    Process event body HTML and replace cid: references with proxy URLs.
    
    Args:
        body_obj: Event body (dict with 'content' key, string, or None)
        event_id: The event ID
        access_token: Microsoft Graph access token
        
    Returns:
        Processed HTML with cid: replaced by proxy URLs
    """
    # Handle multiple input types
    if body_obj is None:
        return ''
    
    if isinstance(body_obj, dict):
        body_html = body_obj.get('content', '')
    elif isinstance(body_obj, str):
        body_html = body_obj
    else:
        return ''
    
    if not body_html:
        return ''
    
    # Find all cid: references in the body
    # Pattern: src="cid:image001.png@01DC683C.4D6FC7D0"
    cid_pattern = r'src=["\'](cid:[^"\']+)["\']'
    
    def replace_cid_with_proxy(match):
        """Replace cid: URL with backend proxy URL"""
        cid_full = match.group(1)  # e.g., "cid:image001.png@01DC683C.4D6FC7D0"
        cid = cid_full.replace('cid:', '')  # Remove "cid:" prefix
        
        # Create proxy URL
        proxy_url = f'/api/emails/calendar/events/{event_id}/attachment/{cid}'
        return f'src="{proxy_url}"'
    
    try:
        # Replace all cid: references with proxy URLs
        processed_body = re.sub(cid_pattern, replace_cid_with_proxy, body_html)
        return processed_body
    except Exception as e:
        print(f"[ERROR] Failed to process event body: {e}")
        # Return original body if processing fails (non-destructive)
        return body_html


def get_event_attachment(event_id: str, attachment_cid: str, access_token: str) -> Optional[Dict]:
    """
    Fetch a specific attachment from an event by its Content-ID.
    
    Args:
        event_id: The event ID
        attachment_cid: The attachment Content-ID (without "cid:" prefix)
        access_token: Microsoft Graph access token
        
    Returns:
        Dict with 'content_bytes' and 'content_type' or None if not found
    """
    try:
        # Get all attachments for the event
        response = requests.get(
            f'https://graph.microsoft.com/v1.0/me/events/{event_id}/attachments',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch attachments: HTTP {response.status_code}")
            return None
        
        data = response.json()
        attachments = data.get('value', [])
        
        # Find the attachment with matching Content-ID
        for attachment in attachments:
            content_id = attachment.get('contentId', '')
            
            # Match with or without angle brackets: <image001.png@01DC683C.4D6FC7D0>
            if content_id == attachment_cid or content_id == f'<{attachment_cid}>' or content_id.strip('<>') == attachment_cid:
                # Found the attachment!
                content_bytes_b64 = attachment.get('contentBytes')
                content_type = attachment.get('contentType', 'image/png')
                
                if not content_bytes_b64:
                    print(f"[ERROR] Attachment found but no contentBytes")
                    return None
                
                # Decode base64
                try:
                    content_bytes = base64.b64decode(content_bytes_b64)
                    return {
                        'content_bytes': content_bytes,
                        'content_type': content_type
                    }
                except Exception as e:
                    print(f"[ERROR] Failed to decode base64: {e}")
                    return None
        
        print(f"[WARNING] Attachment with CID '{attachment_cid}' not found among {len(attachments)} attachments")
        return None
        
    except Exception as e:
        print(f"[ERROR] Exception in get_event_attachment: {e}")
        return None
