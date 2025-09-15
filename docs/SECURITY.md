# Security Guide

## Overview

The Portfolio Agent is designed with security-first principles, implementing multiple layers of protection to ensure data privacy, system integrity, and safe operation.

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Input     │  │  Processing │  │   Output    │        │
│  │ Validation  │  │  Sandboxing │  │ Sanitization│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Encryption  │  │ Access      │  │ Audit       │        │
│  │ at Rest     │  │ Control     │  │ Logging     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Network Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ TLS/SSL     │  │ Firewall    │  │ Rate        │        │
│  │ Encryption  │  │ Rules       │  │ Limiting    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Safe-by-Default Configuration

### Core Security Settings

```yaml
# Security & Privacy (Safe-by-default)
LOCAL_ONLY: true              # No external API calls
REDACT_PII: true              # Automatic PII redaction
AUTO_EMAIL: false             # Manual email approval
RETENTION_DAYS: 30            # Data retention limit
CONSENT_REQUIRED: true        # Explicit consent required
ENABLE_AUDIT_LOG: true        # Comprehensive logging
```

### Why These Defaults?

- **LOCAL_ONLY=true**: Prevents accidental data exposure to external services
- **REDACT_PII=true**: Protects sensitive information automatically
- **AUTO_EMAIL=false**: Prevents unauthorized communication
- **RETENTION_DAYS=30**: Limits data exposure window
- **CONSENT_REQUIRED=true**: Ensures legal compliance

## Data Protection

### PII Redaction Pipeline

The system automatically detects and redacts personally identifiable information:

```python
# Supported PII types
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
    'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
    'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    'address': r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr)',
}
```

### Data Encryption

- **At Rest**: All stored data encrypted using AES-256
- **In Transit**: TLS 1.3 for all network communications
- **In Memory**: Sensitive data cleared after use

### Access Control

```python
# ACL Metadata Example
document_metadata = {
    'id': 'doc_123',
    'content': '...',
    'acl': {
        'owner': 'user_123',
        'permissions': ['read'],
        'groups': ['team_alpha'],
        'expires': '2024-12-31T23:59:59Z'
    }
}
```

## Secret Management

### Environment Variables

```bash
# Required secrets (set in production)
export OPENAI_API_KEY="sk-..."
export PINECONE_API_KEY="..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Optional secrets
export SMTP_PASS="..."
export CALENDLY_API_KEY="..."
```

### Secret Rotation

1. **Automated Rotation**: Use cloud secret managers (AWS Secrets Manager, Azure Key Vault)
2. **Manual Rotation**: Update environment variables and restart services
3. **Audit Trail**: Log all secret access and rotation events

### Secret Scanning

The CI pipeline includes automated secret detection:

```yaml
# .github/workflows/ci.yaml
- name: Secret Scan
  run: |
    # Check for common secret patterns
    if grep -r -i -E "(api[_-]?key|secret[_-]?key|token)" . | grep -v -E "(example|test|demo)"; then
      echo "❌ Potential secrets found!"
      exit 1
    fi
```

## Network Security

### TLS Configuration

```python
# Secure TLS settings
TLS_CONFIG = {
    'min_version': 'TLSv1.3',
    'ciphers': 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS',
    'verify_mode': 'CERT_REQUIRED',
    'check_hostname': True
}
```

### Rate Limiting

```python
# Rate limiting configuration
RATE_LIMITS = {
    'api_calls': '100/minute',
    'file_uploads': '10/minute',
    'email_sends': '5/hour'
}
```

### Firewall Rules

```bash
# Recommended firewall configuration
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 6379/tcp  # Redis (internal only)
ufw deny 5432/tcp   # PostgreSQL (internal only)
```

## Input Validation

### Content Validation

```python
def validate_input(content: str) -> bool:
    """Validate input content for security."""
    # Check for malicious patterns
    malicious_patterns = [
        r'<script.*?>.*?</script>',  # XSS
        r'javascript:',              # JavaScript injection
        r'data:text/html',           # Data URI attacks
        r'vbscript:',                # VBScript injection
    ]
    
    for pattern in malicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False
    
    return True
```

### File Upload Security

```python
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.html', '.json'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file_path: str) -> bool:
    """Validate uploaded file."""
    # Check extension
    if not any(file_path.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return False
    
    # Check size
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        return False
    
    # Scan for malware (integrate with antivirus)
    return scan_file(file_path)
```

## Audit Logging

### Comprehensive Logging

```python
import logging
import json
from datetime import datetime

def audit_log(event_type: str, user_id: str, details: dict):
    """Log security-relevant events."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'details': details,
        'ip_address': get_client_ip(),
        'user_agent': get_user_agent()
    }
    
    logger.info(json.dumps(log_entry))
```

### Logged Events

- Authentication attempts
- Data access and modifications
- Configuration changes
- Error conditions
- Security violations

## Vulnerability Management

### Dependency Scanning

```bash
# Regular dependency updates
poetry update
pip-audit

# Check for known vulnerabilities
safety check
```

### Security Testing

```python
# Security test examples
def test_sql_injection():
    """Test for SQL injection vulnerabilities."""
    malicious_input = "'; DROP TABLE users; --"
    result = query_database(malicious_input)
    assert "error" not in result.lower()

def test_xss_protection():
    """Test for XSS protection."""
    malicious_input = "<script>alert('xss')</script>"
    result = process_content(malicious_input)
    assert "<script>" not in result
```

## Incident Response

### Security Incident Checklist

1. **Immediate Response**
   - Isolate affected systems
   - Preserve evidence
   - Notify security team

2. **Investigation**
   - Analyze logs and metrics
   - Identify attack vector
   - Assess data exposure

3. **Containment**
   - Patch vulnerabilities
   - Update security controls
   - Monitor for recurrence

4. **Recovery**
   - Restore from clean backups
   - Verify system integrity
   - Update incident documentation

### Contact Information

- **Security Team**: security@company.com
- **Emergency Hotline**: +1-XXX-XXX-XXXX
- **Bug Bounty**: security@company.com

## Compliance

### GDPR Compliance

- **Data Minimization**: Only collect necessary data
- **Consent Management**: Explicit consent for processing
- **Right to Erasure**: Data deletion capabilities
- **Data Portability**: Export user data
- **Privacy by Design**: Built-in privacy protections

### SOC 2 Compliance

- **Security**: Access controls and encryption
- **Availability**: System uptime and monitoring
- **Processing Integrity**: Data accuracy and completeness
- **Confidentiality**: Data protection measures
- **Privacy**: Personal information handling

## Security Best Practices

### For Developers

1. **Code Security**
   - Input validation and sanitization
   - Secure coding practices
   - Regular security reviews

2. **Dependency Management**
   - Keep dependencies updated
   - Use trusted sources
   - Monitor for vulnerabilities

3. **Testing**
   - Security-focused testing
   - Penetration testing
   - Code analysis tools

### For Administrators

1. **System Hardening**
   - Regular security updates
   - Minimal privilege access
   - Network segmentation

2. **Monitoring**
   - Security event monitoring
   - Performance monitoring
   - Log analysis

3. **Backup and Recovery**
   - Regular backups
   - Test recovery procedures
   - Offsite storage

## Security Resources

### Documentation
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls/)

### Tools
- [OWASP ZAP](https://www.zaproxy.org/) - Web application security testing
- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [Safety](https://pyup.io/safety/) - Dependency vulnerability scanner

### Training
- Security awareness training
- Secure coding workshops
- Incident response drills
