"""
Security Manager

This module provides advanced security features including input validation,
output sanitization, rate limiting, and security monitoring.
"""

import logging
import re
import time
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)

@dataclass
class SecurityViolation:
    """Security violation record."""
    violation_type: str
    severity: str
    details: str
    timestamp: datetime
    source_ip: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class RateLimit:
    """Rate limit configuration."""
    max_requests: int
    time_window: timedelta
    block_duration: timedelta = timedelta(minutes=5)

class InputValidator:
    """Input validator for security checks."""
    
    def __init__(self):
        """Initialize input validator."""
        # Malicious patterns
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'javascript:',  # JavaScript injection
            r'data:text/html',  # Data URI XSS
            r'vbscript:',  # VBScript injection
            r'onload\s*=',  # Event handler injection
            r'onerror\s*=',  # Event handler injection
            r'onclick\s*=',  # Event handler injection
            r'<iframe[^>]*>',  # Iframe injection
            r'<object[^>]*>',  # Object injection
            r'<embed[^>]*>',  # Embed injection
            r'<link[^>]*>',  # Link injection
            r'<meta[^>]*>',  # Meta injection
            r'<style[^>]*>',  # Style injection
            r'expression\s*\(',  # CSS expression
            r'url\s*\(',  # CSS URL
            r'@import',  # CSS import
            r'\.\./',  # Path traversal
            r'\.\.\\',  # Path traversal
            r'%2e%2e%2f',  # URL encoded path traversal
            r'%2e%2e%5c',  # URL encoded path traversal
            r'0x[0-9a-fA-F]+',  # Hex encoding
            r'\\x[0-9a-fA-F]+',  # Hex encoding
            r'\\u[0-9a-fA-F]+',  # Unicode encoding
            r'%[0-9a-fA-F]{2}',  # URL encoding
            r'\\[0-7]{1,3}',  # Octal encoding
            r'\\[0-9a-fA-F]{1,2}',  # Hex encoding
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            r'union\s+select',  # Union select
            r'drop\s+table',  # Drop table
            r'delete\s+from',  # Delete from
            r'insert\s+into',  # Insert into
            r'update\s+set',  # Update set
            r'alter\s+table',  # Alter table
            r'create\s+table',  # Create table
            r'exec\s*\(',  # Execute
            r'execute\s*\(',  # Execute
            r'sp_',  # Stored procedures
            r'xp_',  # Extended procedures
            r'--',  # SQL comment
            r'/\*.*?\*/',  # SQL comment block
            r';\s*drop',  # Command chaining
            r';\s*delete',  # Command chaining
            r';\s*insert',  # Command chaining
            r';\s*update',  # Command chaining
            r';\s*alter',  # Command chaining
            r';\s*create',  # Command chaining
            r';\s*exec',  # Command chaining
            r';\s*execute',  # Command chaining
        ]
        
        # Command injection patterns
        self.command_patterns = [
            r';\s*ls',  # List directory
            r';\s*cat',  # Read file
            r';\s*rm',  # Remove file
            r';\s*mv',  # Move file
            r';\s*cp',  # Copy file
            r';\s*chmod',  # Change permissions
            r';\s*chown',  # Change ownership
            r';\s*ps',  # Process list
            r';\s*kill',  # Kill process
            r';\s*nc',  # Netcat
            r';\s*wget',  # Download
            r';\s*curl',  # Download
            r';\s*ping',  # Ping
            r';\s*nslookup',  # DNS lookup
            r';\s*whoami',  # User info
            r';\s*id',  # User info
            r';\s*uname',  # System info
            r';\s*env',  # Environment
            r';\s*history',  # Command history
            r';\s*passwd',  # Password change
            r';\s*su',  # Switch user
            r';\s*sudo',  # Sudo
            r';\s*sh',  # Shell
            r';\s*bash',  # Bash
            r';\s*zsh',  # Zsh
            r';\s*fish',  # Fish
            r';\s*powershell',  # PowerShell
            r';\s*cmd',  # CMD
            r';\s*python',  # Python
            r';\s*perl',  # Perl
            r';\s*ruby',  # Ruby
            r';\s*php',  # PHP
            r';\s*node',  # Node.js
            r';\s*npm',  # NPM
            r';\s*pip',  # Pip
            r';\s*gem',  # Gem
            r';\s*composer',  # Composer
            r';\s*yarn',  # Yarn
            r';\s*docker',  # Docker
            r';\s*kubectl',  # Kubernetes
            r';\s*terraform',  # Terraform
            r';\s*ansible',  # Ansible
            r';\s*git',  # Git
            r';\s*svn',  # SVN
            r';\s*hg',  # Mercurial
            r';\s*ssh',  # SSH
            r';\s*scp',  # SCP
            r';\s*rsync',  # Rsync
            r';\s*ftp',  # FTP
            r';\s*sftp',  # SFTP
            r';\s*telnet',  # Telnet
            r';\s*nmap',  # Nmap
            r';\s*nc',  # Netcat
            r';\s*socat',  # Socat
            r';\s*netcat',  # Netcat
            r';\s*nc',  # Netcat
            r';\s*ncat',  # Ncat
            r';\s*openssl',  # OpenSSL
            r';\s*base64',  # Base64
            r';\s*hexdump',  # Hexdump
            r';\s*xxd',  # Hexdump
            r';\s*od',  # Octal dump
            r';\s*strings',  # Strings
            r';\s*file',  # File type
            r';\s*stat',  # File stats
            r';\s*find',  # Find files
            r';\s*grep',  # Grep
            r';\s*sed',  # Sed
            r';\s*awk',  # Awk
            r';\s*sort',  # Sort
            r';\s*uniq',  # Unique
            r';\s*wc',  # Word count
            r';\s*head',  # Head
            r';\s*tail',  # Tail
            r';\s*less',  # Less
            r';\s*more',  # More
            r';\s*vi',  # Vi
            r';\s*vim',  # Vim
            r';\s*nano',  # Nano
            r';\s*emacs',  # Emacs
            r';\s*pico',  # Pico
            r';\s*joe',  # Joe
            r';\s*ed',  # Ed
            r';\s*ex',  # Ex
            r';\s*view',  # View
            r';\s*gview',  # Gview
            r';\s*gvim',  # Gvim
            r';\s*rvim',  # Rvim
            r';\s*rview',  # Rview
            r';\s*evim',  # Evim
            r';\s*eview',  # Eview
            r';\s*vimdiff',  # Vimdiff
            r';\s*gvimdiff',  # Gvimdiff
            r';\s*rvimdiff',  # Rvimdiff
            r';\s*evimdiff',  # Evimdiff
            r';\s*eviewdiff',  # Eviewdiff
        ]
        
        # Compile patterns for efficiency
        self.malicious_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.malicious_patterns]
        self.sql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.command_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.command_patterns]
        
        logger.info("Input validator initialized")
    
    def validate_input(
        self,
        input_text: str,
        input_type: str = "text",
        max_length: int = 10000
    ) -> Tuple[bool, List[str]]:
        """Validate input for security threats.
        
        Args:
            input_text: Input text to validate
            input_type: Type of input (text, html, sql, command)
            max_length: Maximum allowed length
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Check length
        if len(input_text) > max_length:
            violations.append(f"Input too long: {len(input_text)} > {max_length}")
        
        # Check for malicious patterns
        for regex in self.malicious_regex:
            if regex.search(input_text):
                violations.append(f"Malicious pattern detected: {regex.pattern}")
        
        # Check for SQL injection if applicable
        if input_type in ["sql", "database", "query"]:
            for regex in self.sql_regex:
                if regex.search(input_text):
                    violations.append(f"SQL injection pattern detected: {regex.pattern}")
        
        # Check for command injection if applicable
        if input_type in ["command", "shell", "system"]:
            for regex in self.command_regex:
                if regex.search(input_text):
                    violations.append(f"Command injection pattern detected: {regex.pattern}")
        
        # Check for suspicious characters
        suspicious_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}', '[', ']']
        for char in suspicious_chars:
            if char in input_text:
                violations.append(f"Suspicious character detected: {char}")
        
        # Check for encoding attempts
        if any(encoded in input_text.lower() for encoded in ['%20', '%3c', '%3e', '%22', '%27', '%26']):
            violations.append("URL encoding detected")
        
        if any(encoded in input_text.lower() for encoded in ['\\x', '\\u', '\\0']):
            violations.append("Hex/Unicode encoding detected")
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def sanitize_input(
        self,
        input_text: str,
        input_type: str = "text"
    ) -> str:
        """Sanitize input by removing or escaping dangerous content.
        
        Args:
            input_text: Input text to sanitize
            input_type: Type of input
            
        Returns:
            Sanitized input text
        """
        sanitized = input_text
        
        # Remove HTML tags
        if input_type in ["text", "html"]:
            sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        # Escape HTML entities
        html_entities = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;'
        }
        
        for char, entity in html_entities.items():
            sanitized = sanitized.replace(char, entity)
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized

class OutputSanitizer:
    """Output sanitizer for secure response generation."""
    
    def __init__(self):
        """Initialize output sanitizer."""
        # Dangerous output patterns
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'javascript:',  # JavaScript injection
            r'data:text/html',  # Data URI XSS
            r'vbscript:',  # VBScript injection
            r'onload\s*=',  # Event handler injection
            r'onerror\s*=',  # Event handler injection
            r'onclick\s*=',  # Event handler injection
            r'<iframe[^>]*>',  # Iframe injection
            r'<object[^>]*>',  # Object injection
            r'<embed[^>]*>',  # Embed injection
            r'<link[^>]*>',  # Link injection
            r'<meta[^>]*>',  # Meta injection
            r'<style[^>]*>',  # Style injection
            r'expression\s*\(',  # CSS expression
            r'url\s*\(',  # CSS URL
            r'@import',  # CSS import
        ]
        
        # Compile patterns
        self.dangerous_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]
        
        logger.info("Output sanitizer initialized")
    
    def sanitize_output(
        self,
        output_text: str,
        output_type: str = "text"
    ) -> str:
        """Sanitize output for security.
        
        Args:
            output_text: Output text to sanitize
            output_type: Type of output
            
        Returns:
            Sanitized output text
        """
        sanitized = output_text
        
        # Remove dangerous patterns
        for regex in self.dangerous_regex:
            sanitized = regex.sub('', sanitized)
        
        # Escape HTML entities
        html_entities = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;'
        }
        
        for char, entity in html_entities.items():
            sanitized = sanitized.replace(char, entity)
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def validate_output(
        self,
        output_text: str,
        output_type: str = "text"
    ) -> Tuple[bool, List[str]]:
        """Validate output for security threats.
        
        Args:
            output_text: Output text to validate
            output_type: Type of output
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Check for dangerous patterns
        for regex in self.dangerous_regex:
            if regex.search(output_text):
                violations.append(f"Dangerous pattern detected: {regex.pattern}")
        
        # Check for suspicious characters
        suspicious_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}', '[', ']']
        for char in suspicious_chars:
            if char in output_text:
                violations.append(f"Suspicious character detected: {char}")
        
        is_valid = len(violations) == 0
        return is_valid, violations

class RateLimiter:
    """Rate limiter for request throttling."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.rate_limits: Dict[str, RateLimit] = {}
        self.request_counts: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        
        logger.info("Rate limiter initialized")
    
    def add_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        time_window: timedelta,
        block_duration: timedelta = timedelta(minutes=5)
    ):
        """Add a rate limit configuration.
        
        Args:
            identifier: Rate limit identifier
            max_requests: Maximum requests allowed
            time_window: Time window for rate limiting
            block_duration: Duration to block after limit exceeded
        """
        self.rate_limits[identifier] = RateLimit(
            max_requests=max_requests,
            time_window=time_window,
            block_duration=block_duration
        )
        logger.info(f"Added rate limit for {identifier}: {max_requests} requests per {time_window}")
    
    def is_allowed(
        self,
        client_id: str,
        identifier: str = "default"
    ) -> Tuple[bool, str]:
        """Check if request is allowed.
        
        Args:
            client_id: Client identifier (IP, user ID, etc.)
            identifier: Rate limit identifier
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        with self._lock:
            # Check if client is blocked
            if client_id in self.blocked_ips:
                block_until = self.blocked_ips[client_id]
                if datetime.now() < block_until:
                    return False, f"Client blocked until {block_until}"
                else:
                    del self.blocked_ips[client_id]
            
            # Get rate limit configuration
            if identifier not in self.rate_limits:
                return True, "No rate limit configured"
            
            rate_limit = self.rate_limits[identifier]
            now = datetime.now()
            
            # Clean old requests
            client_requests = self.request_counts[client_id]
            cutoff_time = now - rate_limit.time_window
            
            while client_requests and client_requests[0] < cutoff_time:
                client_requests.popleft()
            
            # Check if limit exceeded
            if len(client_requests) >= rate_limit.max_requests:
                # Block client
                self.blocked_ips[client_id] = now + rate_limit.block_duration
                return False, f"Rate limit exceeded: {len(client_requests)}/{rate_limit.max_requests}"
            
            # Add current request
            client_requests.append(now)
            return True, "Request allowed"
    
    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get client statistics.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with client statistics
        """
        with self._lock:
            client_requests = self.request_counts[client_id]
            now = datetime.now()
            
            # Clean old requests
            for identifier, rate_limit in self.rate_limits.items():
                cutoff_time = now - rate_limit.time_window
                while client_requests and client_requests[0] < cutoff_time:
                    client_requests.popleft()
            
            return {
                'client_id': client_id,
                'request_count': len(client_requests),
                'is_blocked': client_id in self.blocked_ips,
                'blocked_until': self.blocked_ips.get(client_id),
                'rate_limits': {
                    identifier: {
                        'max_requests': rate_limit.max_requests,
                        'time_window': str(rate_limit.time_window),
                        'block_duration': str(rate_limit.block_duration)
                    }
                    for identifier, rate_limit in self.rate_limits.items()
                }
            }

class SecurityManager:
    """Main security manager combining all security features."""
    
    def __init__(self):
        """Initialize security manager."""
        self.input_validator = InputValidator()
        self.output_sanitizer = OutputSanitizer()
        self.rate_limiter = RateLimiter()
        
        # Security monitoring
        self.violations: List[SecurityViolation] = []
        self.security_metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'input_violations': 0,
            'output_violations': 0,
            'rate_limit_violations': 0
        }
        
        # Setup default rate limits
        self.rate_limiter.add_rate_limit(
            "default",
            max_requests=100,
            time_window=timedelta(minutes=1),
            block_duration=timedelta(minutes=5)
        )
        
        self.rate_limiter.add_rate_limit(
            "api",
            max_requests=1000,
            time_window=timedelta(hours=1),
            block_duration=timedelta(hours=1)
        )
        
        logger.info("Security manager initialized")
    
    def validate_and_sanitize_input(
        self,
        input_text: str,
        input_type: str = "text",
        max_length: int = 10000,
        client_id: str = "anonymous"
    ) -> Tuple[bool, str, List[str]]:
        """Validate and sanitize input.
        
        Args:
            input_text: Input text
            input_type: Type of input
            max_length: Maximum length
            client_id: Client identifier
            
        Returns:
            Tuple of (is_valid, sanitized_text, violations)
        """
        self.security_metrics['total_requests'] += 1
        
        # Check rate limit
        is_allowed, reason = self.rate_limiter.is_allowed(client_id, "default")
        if not is_allowed:
            self.security_metrics['blocked_requests'] += 1
            self.security_metrics['rate_limit_violations'] += 1
            self._record_violation(
                "rate_limit",
                "high",
                f"Rate limit exceeded: {reason}",
                user_id=client_id
            )
            return False, "", [f"Rate limit exceeded: {reason}"]
        
        # Validate input
        is_valid, violations = self.input_validator.validate_input(
            input_text, input_type, max_length
        )
        
        if not is_valid:
            self.security_metrics['input_violations'] += 1
            for violation in violations:
                self._record_violation(
                    "input_validation",
                    "high",
                    violation,
                    user_id=client_id
                )
            return False, "", violations
        
        # Sanitize input
        sanitized_text = self.input_validator.sanitize_input(input_text, input_type)
        
        return True, sanitized_text, []
    
    def validate_and_sanitize_output(
        self,
        output_text: str,
        output_type: str = "text",
        client_id: str = "anonymous"
    ) -> Tuple[bool, str, List[str]]:
        """Validate and sanitize output.
        
        Args:
            output_text: Output text
            output_type: Type of output
            client_id: Client identifier
            
        Returns:
            Tuple of (is_valid, sanitized_text, violations)
        """
        # Validate output
        is_valid, violations = self.output_sanitizer.validate_output(
            output_text, output_type
        )
        
        if not is_valid:
            self.security_metrics['output_violations'] += 1
            for violation in violations:
                self._record_violation(
                    "output_validation",
                    "high",
                    violation,
                    user_id=client_id
                )
            return False, "", violations
        
        # Sanitize output
        sanitized_text = self.output_sanitizer.sanitize_output(output_text, output_type)
        
        return True, sanitized_text, []
    
    def _record_violation(
        self,
        violation_type: str,
        severity: str,
        details: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Record a security violation."""
        violation = SecurityViolation(
            violation_type=violation_type,
            severity=severity,
            details=details,
            timestamp=datetime.now(),
            source_ip=source_ip,
            user_id=user_id
        )
        
        self.violations.append(violation)
        
        # Keep only recent violations (last 1000)
        if len(self.violations) > 1000:
            self.violations = self.violations[-1000:]
        
        logger.warning(f"Security violation: {violation_type} - {details}")
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        return {
            'metrics': self.security_metrics.copy(),
            'total_violations': len(self.violations),
            'recent_violations': len([
                v for v in self.violations
                if v.timestamp > datetime.now() - timedelta(hours=1)
            ]),
            'violation_types': {
                violation_type: len([
                    v for v in self.violations
                    if v.violation_type == violation_type
                ])
                for violation_type in set(v.violation_type for v in self.violations)
            }
        }
    
    def get_violations(
        self,
        hours: int = 24,
        violation_type: Optional[str] = None
    ) -> List[SecurityViolation]:
        """Get recent violations.
        
        Args:
            hours: Number of hours to look back
            violation_type: Filter by violation type
            
        Returns:
            List of violations
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_violations = [
            v for v in self.violations
            if v.timestamp > cutoff_time
        ]
        
        if violation_type:
            recent_violations = [
                v for v in recent_violations
                if v.violation_type == violation_type
            ]
        
        return recent_violations
    
    def clear_violations(self):
        """Clear all violations."""
        self.violations.clear()
        logger.info("Security violations cleared")
    
    def reset_metrics(self):
        """Reset security metrics."""
        self.security_metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'input_violations': 0,
            'output_violations': 0,
            'rate_limit_violations': 0
        }
        logger.info("Security metrics reset")

# Convenience functions
def create_security_manager() -> SecurityManager:
    """Create a security manager instance."""
    return SecurityManager()

def create_input_validator() -> InputValidator:
    """Create an input validator instance."""
    return InputValidator()

def create_output_sanitizer() -> OutputSanitizer:
    """Create an output sanitizer instance."""
    return OutputSanitizer()

def create_rate_limiter() -> RateLimiter:
    """Create a rate limiter instance."""
    return RateLimiter()
