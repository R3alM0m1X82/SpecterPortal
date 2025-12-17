"""
Secret Detector - Advanced Pattern Detection for Teams Messages
Detects secrets, credentials, API keys in Teams conversations
"""
import re
import math
import html
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum


class SecretType(Enum):
    """Types of secrets that can be detected"""
    AWS_ACCESS_KEY = "AWS Access Key"
    AWS_SECRET_KEY = "AWS Secret Key"
    AZURE_CLIENT_SECRET = "Azure Client Secret"
    AZURE_CONNECTION_STRING = "Azure Connection String"
    AZURE_STORAGE_KEY = "Azure Storage Key"
    GITHUB_TOKEN = "GitHub Token"
    GITHUB_PAT = "GitHub Personal Access Token"
    SLACK_TOKEN = "Slack Token"
    SLACK_WEBHOOK = "Slack Webhook"
    GOOGLE_API_KEY = "Google API Key"
    PRIVATE_KEY = "Private Key"
    SSH_KEY = "SSH Key"
    JWT_TOKEN = "JWT Token"
    BEARER_TOKEN = "Bearer Token"
    BASIC_AUTH = "Basic Auth"
    DATABASE_URL = "Database Connection String"
    WEBHOOK_URL = "Webhook URL"
    DISCORD_TOKEN = "Discord Token"
    STRIPE_KEY = "Stripe API Key"
    SENDGRID_KEY = "SendGrid API Key"
    TWILIO_KEY = "Twilio API Key"
    OPENAI_KEY = "OpenAI API Key"
    GENERIC_API_KEY = "Generic API Key"
    PASSWORD_PATTERN = "Password Pattern"
    CREDENTIAL_EXCHANGE = "Credential Exchange"
    CONNECTION_STRING = "Connection String"


@dataclass
class SecretMatch:
    """Represents a detected secret"""
    secret_type: SecretType
    raw_value: str
    redacted_value: str
    confidence: float
    entropy: float
    severity: str
    context_before: str
    context_after: str
    message_id: str
    conversation_id: str
    conversation_name: str
    sender: str
    timestamp: str
    message_content: str
    extra_data: Dict = field(default_factory=dict)


class SecretDetector:
    """Detector for secrets in text content"""
    
    # Entropy thresholds
    MIN_ENTROPY_GENERIC = 3.0
    MIN_ENTROPY_HIGH = 4.0
    
    # Severity mapping
    SEVERITY_MAP = {
        SecretType.AWS_ACCESS_KEY: 'critical',
        SecretType.AWS_SECRET_KEY: 'critical',
        SecretType.AZURE_CLIENT_SECRET: 'critical',
        SecretType.AZURE_CONNECTION_STRING: 'critical',
        SecretType.AZURE_STORAGE_KEY: 'critical',
        SecretType.PRIVATE_KEY: 'critical',
        SecretType.SSH_KEY: 'critical',
        SecretType.DATABASE_URL: 'high',
        SecretType.GITHUB_TOKEN: 'high',
        SecretType.GITHUB_PAT: 'high',
        SecretType.SLACK_TOKEN: 'high',
        SecretType.SLACK_WEBHOOK: 'high',
        SecretType.STRIPE_KEY: 'high',
        SecretType.OPENAI_KEY: 'high',
        SecretType.JWT_TOKEN: 'medium',
        SecretType.PASSWORD_PATTERN: 'medium',
        SecretType.CREDENTIAL_EXCHANGE: 'medium',
        SecretType.GENERIC_API_KEY: 'low',
    }
    
    # Detection patterns (regex + confidence)
    PATTERNS: Dict[SecretType, List[Tuple[str, float]]] = {
        # AWS Keys
        SecretType.AWS_ACCESS_KEY: [
            (r'\b((?:AKIA|ABIA|ACCA)[A-Z0-9]{16})\b', 0.95),
        ],
        SecretType.AWS_SECRET_KEY: [
            (r'(?i)(?:aws)?_?(?:secret)?_?(?:access)?_?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})["\']?', 0.9),
        ],
        
        # Azure
        SecretType.AZURE_CLIENT_SECRET: [
            (r'(?i)(?:client[_-]?secret|azure[_-]?secret)["\']?\s*[:=]\s*["\']?([A-Za-z0-9~._-]{34,40})["\']?', 0.85),
        ],
        SecretType.AZURE_CONNECTION_STRING: [
            (r'(?i)(DefaultEndpointsProtocol=https?;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{86,88};EndpointSuffix=[^;\s]+)', 0.95),
        ],
        SecretType.AZURE_STORAGE_KEY: [
            (r'AccountKey=([A-Za-z0-9+/=]{88})', 0.95),
        ],
        
        # GitHub
        SecretType.GITHUB_TOKEN: [
            (r'\b(ghp_[A-Za-z0-9]{36})\b', 0.95),
            (r'\b(gho_[A-Za-z0-9]{36})\b', 0.95),
            (r'\b(ghu_[A-Za-z0-9]{36})\b', 0.95),
            (r'\b(ghs_[A-Za-z0-9]{36})\b', 0.95),
            (r'\b(ghr_[A-Za-z0-9]{36})\b', 0.95),
        ],
        SecretType.GITHUB_PAT: [
            (r'(?i)(?:github|gh)[_-]?(?:token|pat|api[_-]?key)["\']?\s*[:=]\s*["\']?([a-f0-9]{40})["\']?', 0.85),
        ],
        
        # Slack
        SecretType.SLACK_TOKEN: [
            (r'\b(xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*)\b', 0.95),
        ],
        SecretType.SLACK_WEBHOOK: [
            (r'(https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+)', 0.95),
        ],
        
        # Google
        SecretType.GOOGLE_API_KEY: [
            (r'\b(AIza[A-Za-z0-9_-]{35})\b', 0.95),
        ],
        
        # Private Keys
        SecretType.PRIVATE_KEY: [
            (r'(-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----)', 0.99),
        ],
        SecretType.SSH_KEY: [
            (r'(ssh-(?:rsa|dss|ed25519|ecdsa)\s+[A-Za-z0-9+/=]{50,})', 0.9),
        ],
        
        # JWT
        SecretType.JWT_TOKEN: [
            (r'\b(eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b', 0.9),
        ],
        
        # Bearer/Basic Auth
        SecretType.BEARER_TOKEN: [
            (r'(?i)bearer\s+([A-Za-z0-9_-]{20,})', 0.8),
        ],
        SecretType.BASIC_AUTH: [
            (r'(?i)basic\s+([A-Za-z0-9+/=]{20,})', 0.8),
        ],
        
        # Database URLs
        SecretType.DATABASE_URL: [
            (r'(?i)((?:postgres|mysql|mongodb|redis|mssql)(?:ql)?://[^\s<>"\']+:[^\s<>"\']+@[^\s<>"\']+)', 0.9),
        ],
        
        # Webhooks
        SecretType.WEBHOOK_URL: [
            (r'(https://(?:discord\.com|discordapp\.com)/api/webhooks/[0-9]+/[A-Za-z0-9_-]+)', 0.95),
            (r'(https://outlook\.office\.com/webhook/[A-Za-z0-9-]+)', 0.9),
        ],
        
        # Discord
        SecretType.DISCORD_TOKEN: [
            (r'\b([MN][A-Za-z0-9]{23,28}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27})\b', 0.9),
        ],
        
        # Stripe
        SecretType.STRIPE_KEY: [
            (r'\b(sk_live_[A-Za-z0-9]{24,})\b', 0.95),
            (r'\b(sk_test_[A-Za-z0-9]{24,})\b', 0.9),
            (r'\b(rk_live_[A-Za-z0-9]{24,})\b', 0.95),
        ],
        
        # SendGrid
        SecretType.SENDGRID_KEY: [
            (r'\b(SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43})\b', 0.95),
        ],
        
        # Twilio
        SecretType.TWILIO_KEY: [
            (r'\b(SK[a-f0-9]{32})\b', 0.9),
        ],
        
        # OpenAI
        SecretType.OPENAI_KEY: [
            (r'\b(sk-[A-Za-z0-9]{48})\b', 0.95),
        ],
        
        # Generic API Key
        SecretType.GENERIC_API_KEY: [
            (r'(?i)(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]{16,64})["\']?', 0.7),
        ],
        
        # Connection String
        SecretType.CONNECTION_STRING: [
            (r'(?i)(?:connection[_-]?string|conn[_-]?str)["\']?\s*[:=]\s*["\']?([^\s"\']{20,})["\']?', 0.75),
        ],
    }
    
    # Conversational patterns (password sharing in chat)
    CONVERSATION_PATTERNS: Dict[SecretType, List[Tuple[str, float]]] = {
        SecretType.PASSWORD_PATTERN: [
            # English patterns
            (r'(?i)(?:the\s+)?password\s+is\s*:?\s*["\']?([^\s"\'<>]{4,64})["\']?', 0.85),
            (r'(?i)(?:here\s+is|here\'s)\s+(?:the\s+)?(?:password|pwd|pass)\s*[:=]?\s*["\']?([^\s"\'<>]{4,64})["\']?', 0.85),
            (r'(?i)(?:my|your|the)\s+password\s*(?:is\s*:?|:)\s*["\']?([^\s"\'<>]{4,64})["\']?', 0.85),
            (r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\'<>]{4,64})["\']?', 0.75),
        ],
        SecretType.CREDENTIAL_EXCHANGE: [
            (r'(?i)(?:user(?:name)?|login)\s*[:=]\s*["\']?([^\s"\'<>]+)["\']?\s*[/\-,;]\s*(?:password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\'<>]+)["\']?', 0.9),
            (r'(?i)(?:login|user)\s*[:=]\s*([^\s,;]+)\s*[,;]\s*(?:pass|pwd)\s*[:=]\s*([^\s,;]+)', 0.85),
            (r'(?i)([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+)\s*[/\-:]\s*([^\s<>"\']{4,})', 0.75),
        ],
    }
    
    # False positive patterns (exclude these)
    EXCLUDE_PATTERNS = [
        r'^[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}$',  # UUIDs
        r'^#[a-fA-F0-9]{6}$',  # Hex colors
        r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',  # IPs
        r'^v?\d+\.\d+\.\d+$',  # Versions
        r'^\d{4}[-/]\d{2}[-/]\d{2}$',  # Dates
        r'^(true|false|null|none|undefined)$',
        r'^[a-zA-Z]+$',  # Pure letters
        r'^\d+$',  # Pure numbers
        r'^(example|test|demo|sample|placeholder|xxx+|yyy+|zzz+)$',
    ]
    
    # Common false positives
    COMMON_FALSE_POSITIVES = [
        'password', 'secret', 'token', 'apikey', 'api_key', 'changeme',
        'your_password', 'your_secret', 'your_token', 'your_api_key',
        'password123', 'admin', 'root', 'test', 'demo', 'example',
        'placeholder', 'redacted', 'hidden', 'masked', '********',
        'xxxxxxxx', 'yyyyyyyy', 'zzzzzzzz', 'undefined', 'null', 'none',
    ]
    
    # Teams system message patterns (skip these)
    TEAMS_SYSTEM_PATTERNS = [
        r'https?://[^\s]*\.teams\.microsoft\.com',
        r'https?://[^\s]*\.skype\.com',
        r'https?://[^\s]*msg\.teams',
        r'8:orgid:[a-f0-9-]+',
        r'8:teamsvisitor:[a-f0-9]+',
        r'19:meeting_[A-Za-z0-9-]+@thread',
        r'19:[a-f0-9]+@thread\.v2',
        r'AAMkA[A-Za-z0-9+/=]+',
        r'"eventtime":\d+',
        r'"initiator":"8:',
        r'"members":\[',
        r'callEnded',
        r'Scheduled\d{2}/\d{2}/\d{4}',
    ]
    
    def __init__(self):
        """Initialize detector with compiled patterns"""
        # Compile regex patterns for performance
        self.compiled_patterns: Dict[SecretType, List[Tuple[re.Pattern, float]]] = {}
        for secret_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[secret_type] = [
                (re.compile(pattern, re.IGNORECASE | re.MULTILINE), confidence)
                for pattern, confidence in patterns
            ]
        
        self.compiled_conversation_patterns: Dict[SecretType, List[Tuple[re.Pattern, float]]] = {}
        for secret_type, patterns in self.CONVERSATION_PATTERNS.items():
            self.compiled_conversation_patterns[secret_type] = [
                (re.compile(pattern, re.IGNORECASE | re.MULTILINE), confidence)
                for pattern, confidence in patterns
            ]
        
        self.exclude_patterns = [re.compile(p, re.IGNORECASE) for p in self.EXCLUDE_PATTERNS]
        self.system_patterns = [re.compile(p, re.IGNORECASE) for p in self.TEAMS_SYSTEM_PATTERNS]
    
    @staticmethod
    def calculate_shannon_entropy(data: str) -> float:
        """
        Calculate Shannon entropy of a string
        Higher entropy = more random = more likely to be a secret
        """
        if not data:
            return 0.0
        
        entropy = 0.0
        length = len(data)
        char_count: Dict[str, int] = {}
        
        for char in data:
            char_count[char] = char_count.get(char, 0) + 1
        
        for count in char_count.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    @staticmethod
    def redact_secret(secret: str, show_chars: int = 4) -> str:
        """Redact secret showing only first/last characters"""
        if len(secret) <= show_chars * 2:
            return '*' * len(secret)
        return secret[:show_chars] + '*' * (len(secret) - show_chars * 2) + secret[-show_chars:]
    
    def is_false_positive(self, value: str) -> bool:
        """Check if value is a known false positive"""
        value_lower = value.lower().strip()
        
        if value_lower in self.COMMON_FALSE_POSITIVES:
            return True
        
        for pattern in self.exclude_patterns:
            if pattern.fullmatch(value):
                return True
        
        # Too repetitive (low character diversity)
        if len(set(value_lower)) <= 2:
            return True
        
        return False
    
    def is_teams_system_message(self, text: str) -> bool:
        """Check if text is a Teams system message (should be ignored)"""
        if not text:
            return True
        
        for pattern in self.system_patterns:
            if pattern.search(text):
                return True
        
        # Check if it looks like JSON metadata
        if text.strip().startswith('{') and ('eventtime' in text or 'initiator' in text):
            return True
        
        return False
    
    def clean_html(self, text: str) -> str:
        """Clean HTML from Teams message"""
        if not text:
            return ""
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_user_content(self, text: str) -> str:
        """Extract only user content from Teams message (remove system metadata)"""
        if not text:
            return ""
        
        clean = self.clean_html(text)
        
        # Remove Teams system URLs
        clean = re.sub(r'https?://[^\s]*(?:teams\.microsoft\.com|skype\.com|msg\.teams)[^\s]*', '', clean)
        
        # Remove Teams IDs
        clean = re.sub(r'8:(?:orgid|teamsvisitor):[a-f0-9-]+', '', clean)
        clean = re.sub(r'19:(?:meeting_)?[A-Za-z0-9_-]+@thread(?:\.v2)?', '', clean)
        
        # Remove calendar/meeting IDs
        clean = re.sub(r'AAMkA[A-Za-z0-9+/=]+', '', clean)
        
        # Remove JSON-like metadata
        clean = re.sub(r'\{[^}]*"(?:eventtime|initiator|members)"[^}]*\}', '', clean)
        
        # Clean up whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
    def get_context(self, text: str, match_start: int, match_end: int, 
                   context_chars: int = 100) -> Tuple[str, str]:
        """Extract context before and after a match"""
        before_start = max(0, match_start - context_chars)
        after_end = min(len(text), match_end + context_chars)
        
        context_before = text[before_start:match_start]
        context_after = text[match_end:after_end]
        
        return context_before.strip(), context_after.strip()
    
    def scan_text(self, text: str, message_id: str = "", conversation_id: str = "",
                  conversation_name: str = "", sender: str = "", timestamp: str = "") -> List[SecretMatch]:
        """
        Scan text for secrets
        
        Args:
            text: Text content to scan
            message_id: Message ID
            conversation_id: Conversation ID
            conversation_name: Conversation name
            sender: Sender name
            timestamp: Message timestamp
            
        Returns:
            List of detected secrets
        """
        results: List[SecretMatch] = []
        
        # Skip system messages
        if self.is_teams_system_message(text):
            return results
        
        # Extract user content
        clean_text = self.extract_user_content(text)
        
        if not clean_text or len(clean_text) < 5:
            return results
        
        seen_secrets = set()
        
        # Scan with standard patterns
        for secret_type, patterns in self.compiled_patterns.items():
            for pattern, base_confidence in patterns:
                for match in pattern.finditer(clean_text):
                    secret_value = match.group(1) if match.lastindex else match.group(0)
                    
                    if secret_value in seen_secrets:
                        continue
                    
                    if self.is_false_positive(secret_value):
                        continue
                    
                    entropy = self.calculate_shannon_entropy(secret_value)
                    
                    # Adjust confidence based on entropy
                    confidence = base_confidence
                    if entropy < self.MIN_ENTROPY_GENERIC:
                        confidence *= 0.6
                    elif entropy > self.MIN_ENTROPY_HIGH:
                        confidence = min(1.0, confidence * 1.15)
                    
                    # Skip if confidence too low
                    if confidence < 0.5:
                        continue
                    
                    context_before, context_after = self.get_context(clean_text, match.start(), match.end())
                    
                    seen_secrets.add(secret_value)
                    results.append(SecretMatch(
                        secret_type=secret_type,
                        raw_value=secret_value,
                        redacted_value=self.redact_secret(secret_value),
                        confidence=round(confidence, 2),
                        entropy=round(entropy, 2),
                        severity=self.SEVERITY_MAP.get(secret_type, 'low'),
                        context_before=context_before,
                        context_after=context_after,
                        message_id=message_id,
                        conversation_id=conversation_id,
                        conversation_name=conversation_name,
                        sender=sender,
                        timestamp=timestamp,
                        message_content=clean_text[:500]  # Limit message content
                    ))
        
        # Scan with conversational patterns
        for secret_type, patterns in self.compiled_conversation_patterns.items():
            for pattern, base_confidence in patterns:
                for match in pattern.finditer(clean_text):
                    if secret_type == SecretType.CREDENTIAL_EXCHANGE and match.lastindex and match.lastindex >= 2:
                        username = match.group(1)
                        password = match.group(2)
                        combined = f"{username}:{password}"
                        
                        if combined in seen_secrets:
                            continue
                        
                        if self.is_false_positive(password):
                            continue
                        
                        entropy = self.calculate_shannon_entropy(password)
                        confidence = base_confidence
                        
                        if entropy < 2.5:
                            confidence *= 0.5
                        
                        if confidence < 0.5:
                            continue
                        
                        context_before, context_after = self.get_context(clean_text, match.start(), match.end())
                        
                        seen_secrets.add(combined)
                        results.append(SecretMatch(
                            secret_type=secret_type,
                            raw_value=combined,
                            redacted_value=f"{username}:{self.redact_secret(password)}",
                            confidence=round(confidence, 2),
                            entropy=round(entropy, 2),
                            severity=self.SEVERITY_MAP.get(secret_type, 'medium'),
                            context_before=context_before,
                            context_after=context_after,
                            message_id=message_id,
                            conversation_id=conversation_id,
                            conversation_name=conversation_name,
                            sender=sender,
                            timestamp=timestamp,
                            message_content=clean_text[:500],
                            extra_data={"username": username, "password_redacted": self.redact_secret(password)}
                        ))
                    else:
                        secret_value = match.group(1) if match.lastindex else match.group(0)
                        
                        if secret_value in seen_secrets:
                            continue
                        
                        if self.is_false_positive(secret_value):
                            continue
                        
                        entropy = self.calculate_shannon_entropy(secret_value)
                        confidence = base_confidence
                        
                        if entropy < 2.5:
                            confidence *= 0.5
                        
                        if confidence < 0.5:
                            continue
                        
                        context_before, context_after = self.get_context(clean_text, match.start(), match.end())
                        
                        seen_secrets.add(secret_value)
                        results.append(SecretMatch(
                            secret_type=secret_type,
                            raw_value=secret_value,
                            redacted_value=self.redact_secret(secret_value),
                            confidence=round(confidence, 2),
                            entropy=round(entropy, 2),
                            severity=self.SEVERITY_MAP.get(secret_type, 'medium'),
                            context_before=context_before,
                            context_after=context_after,
                            message_id=message_id,
                            conversation_id=conversation_id,
                            conversation_name=conversation_name,
                            sender=sender,
                            timestamp=timestamp,
                            message_content=clean_text[:500]
                        ))
        
        return results
    
    def scan_messages(self, messages: List[Dict], conversation_id: str = "",
                     conversation_name: str = "") -> List[SecretMatch]:
        """
        Scan a list of Teams messages
        
        Args:
            messages: List of message dicts from Skype API
            conversation_id: Conversation ID
            conversation_name: Conversation name
            
        Returns:
            List of detected secrets
        """
        all_results: List[SecretMatch] = []
        
        for msg in messages:
            content = msg.get('content', '')
            message_id = msg.get('id', msg.get('clientmessageid', ''))
            sender = msg.get('imdisplayname', msg.get('from', 'Unknown'))
            timestamp = msg.get('composetime', msg.get('originalarrivaltime', ''))
            
            results = self.scan_text(
                text=content,
                message_id=message_id,
                conversation_id=conversation_id,
                conversation_name=conversation_name,
                sender=sender,
                timestamp=timestamp
            )
            all_results.extend(results)
        
        return all_results
