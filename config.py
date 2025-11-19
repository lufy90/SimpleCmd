"""
Configuration file: Define sensitive commands and system settings
"""
import os
from typing import List, Set

# Sensitive command keywords list (commands that require user approval)
SENSITIVE_COMMAND_KEYWORDS: Set[str] = {
    'rm', 'delete', 'remove',  # Delete operations
    'mv', 'move',  # Move operations (may overwrite files)
    'cp', 'copy',  # Copy operations (may overwrite files)
    'chmod', 'chown',  # Permission modifications
    'sudo', 'su',  # Privilege escalation
    'dd',  # Disk operations
    'format', 'mkfs',  # Format operations
    'shutdown', 'reboot', 'halt',  # System control
    'kill', 'killall',  # Process termination
    'curl', 'wget',  # Network downloads (may download malicious files)
    'git push --force',  # Force push
    'drop', 'truncate',  # Database dangerous operations
    '>', '>>',  # Redirection (may overwrite files)
    'uninstall', 'purge',  # Uninstall operations
}

# Dangerous operation patterns that require confirmation
DANGEROUS_PATTERNS: List[str] = [
    r'rm\s+-rf',  # Recursive delete
    r'rm\s+.*\*',  # Wildcard delete
    r'>\s+/',  # Redirect to root directory
    r'sudo\s+rm',  # Sudo delete
]

# AI API Configuration
# API provider type: 'openai', 'custom'
AI_API_PROVIDER = os.getenv('AI_API_PROVIDER', 'openai')

# API endpoint URL (set this value if using custom API)
# Example: 'https://api.openai.com/v1/chat/completions' or 'http://localhost:8000/v1/chat/completions'
AI_API_URL = os.getenv('AI_API_URL', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions')

# API key
AI_API_KEY = os.getenv('AI_API_KEY', '')

# AI model name (adjust according to API provider)
AI_MODEL = os.getenv('AI_MODEL', 'doubao-seed-1-6-251015')

# API request timeout (seconds)
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))

# Command execution timeout (seconds)
COMMAND_TIMEOUT = 30

# Whether to run in debug mode (show more debug information)
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

