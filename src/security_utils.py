from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
from collections import defaultdict
import re

#Simple in-memory account lockout protection
class AccountLockoutProtection:    
    def __init__(self, max_attempts: int = 5, lockout_duration: int = 30):
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.failed_attempts: Dict[str, list] = defaultdict(list)
        self.locked_accounts: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def is_locked(self, identifier: str) -> bool:
        with self._lock:
            if identifier in self.locked_accounts:
                # Check if lockout has expired
                if datetime.now() > self.locked_accounts[identifier]:
                    del self.locked_accounts[identifier]
                    self.failed_attempts[identifier] = []
                    return False
                return True
            return False
    
    def record_failed_attempt(self, identifier: str) -> bool:
        with self._lock:
            now = datetime.now()
            
            # Remove attempts older than 1 hour
            self.failed_attempts[identifier] = [
                attempt for attempt in self.failed_attempts[identifier]
                if now - attempt < timedelta(hours=1)
            ]
            self.failed_attempts[identifier].append(now)
            
            # Check if should lock
            if len(self.failed_attempts[identifier]) >= self.max_attempts:
                self.locked_accounts[identifier] = now + timedelta(minutes=self.lockout_duration)
                return True
            
            return False
    
    # Clear failed attempts on successful login
    def record_successful_login(self, identifier: str):
        with self._lock:
            if identifier in self.failed_attempts:
                del self.failed_attempts[identifier]
            if identifier in self.locked_accounts:
                del self.locked_accounts[identifier]
                
    # Get remaining login attempts before lockout
    def get_remaining_attempts(self, identifier: str) -> int:
        with self._lock:
            current_attempts = len(self.failed_attempts.get(identifier, []))
            return max(0, self.max_attempts - current_attempts)

account_protection = AccountLockoutProtection()

# Content sanitization for XSS prevention
class ContentSanitizer:
    
    #Remove potentially dangerous HTML tags and attributes
    @staticmethod    
    def sanitize_html(text: str) -> str:        
        # Remove script tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove ALL on* event handlers (onclick, onerror, onload, etc.)
        text = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*on\w+\s*=\s*[^"\'\s][^\s>]*', '', text, flags=re.IGNORECASE)
        
        # Remove javascript: links
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Remove potentially dangerous tags completely
        dangerous_tags = ['iframe', 'embed', 'object', 'form', 'input', 'style', 'script']
        for tag in dangerous_tags:
            text = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(f'<{tag}[^>]*/?>', '', text, flags=re.IGNORECASE)
        
        # Special handling for img tags - remove those with event handlers
        text = re.sub(r'<img[^>]*\son\w+[^>]*>', '', text, flags=re.IGNORECASE)
        
        return text.strip()

sanitizer = ContentSanitizer()
