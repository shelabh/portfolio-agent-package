"""
Security Endpoints

This module provides endpoints for security operations and PII detection.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from ..models import SecurityRequest, SecurityResponse
from ...security.pii_detector import AdvancedPIIDetector
from ...security.data_encryption import DataEncryption

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/security/analyze", response_model=SecurityResponse)
async def analyze_security(
    request: SecurityRequest
):
    """
    Analyze text for security issues including PII, secrets, and malicious content.
    
    This endpoint performs comprehensive security analysis on input text.
    """
    try:
        logger.info(f"Analyzing text for security issues: {len(request.text)} characters")
        
        # Initialize security components
        pii_detector = AdvancedPIIDetector()
        
        # Analyze the text
        pii_detected = []
        secrets_detected = []
        malicious_content = []
        risk_score = 0.0
        recommendations = []
        
        # Check for PII
        if request.check_pii:
            pii_result = pii_detector.detect_pii(request.text)
            pii_detected = [
                {
                    "type": pii.type,
                    "value": pii.value,
                    "start": pii.start,
                    "end": pii.end,
                    "confidence": pii.confidence
                }
                for pii in pii_result.detected_pii
            ]
            risk_score += len(pii_detected) * 0.3
        
        # Check for secrets (basic pattern matching)
        if request.check_secrets:
            secrets = _detect_secrets(request.text)
            secrets_detected = secrets
            risk_score += len(secrets) * 0.5
        
        # Check for malicious content (basic patterns)
        if request.check_malicious:
            malicious = _detect_malicious_content(request.text)
            malicious_content = malicious
            risk_score += len(malicious) * 0.4
        
        # Generate recommendations
        if pii_detected:
            recommendations.append("Remove or redact PII before processing")
        if secrets_detected:
            recommendations.append("Remove secrets and use environment variables")
        if malicious_content:
            recommendations.append("Review content for potential security threats")
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        
        # Determine if text is safe
        is_safe = risk_score < 0.5 and not malicious_content
        
        return SecurityResponse(
            is_safe=is_safe,
            pii_detected=pii_detected,
            secrets_detected=secrets_detected,
            malicious_content=malicious_content,
            risk_score=risk_score,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Security analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Security analysis failed: {str(e)}"
        )

@router.post("/security/redact")
async def redact_pii(
    text: str,
    replacement: str = "[REDACTED]"
):
    """
    Redact PII from text.
    
    This endpoint removes or replaces PII in the input text.
    """
    try:
        logger.info(f"Redacting PII from text: {len(text)} characters")
        
        # Initialize PII detector
        pii_detector = AdvancedPIIDetector()
        
        # Detect and redact PII
        result = pii_detector.redact_pii(text, replacement=replacement)
        
        return {
            "original_text": text,
            "redacted_text": result.redacted_text,
            "pii_detected": len(result.detected_pii),
            "redacted_count": result.redacted_count,
            "detected_pii": [
                {
                    "type": pii.type,
                    "value": pii.value,
                    "start": pii.start,
                    "end": pii.end
                }
                for pii in result.detected_pii
            ]
        }
        
    except Exception as e:
        logger.error(f"PII redaction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PII redaction failed: {str(e)}"
        )

@router.post("/security/encrypt")
async def encrypt_data(
    data: Dict[str, Any],
    algorithm: str = "fernet"
):
    """
    Encrypt sensitive data.
    
    This endpoint encrypts the provided data using the specified algorithm.
    """
    try:
        logger.info(f"Encrypting data with algorithm: {algorithm}")
        
        # Initialize encryption
        encryption = DataEncryption()
        
        # Generate key
        key_id = encryption.generate_key()
        
        # Encrypt data
        encrypted_data = encryption.encrypt_data(data, key_id)
        
        return {
            "key_id": key_id,
            "encrypted_data": encrypted_data.encrypted_data.hex(),
            "algorithm": encrypted_data.algorithm,
            "created_at": encrypted_data.created_at
        }
        
    except Exception as e:
        logger.error(f"Data encryption failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Data encryption failed: {str(e)}"
        )

@router.post("/security/decrypt")
async def decrypt_data(
    encrypted_data: str,
    key_id: str,
    algorithm: str = "fernet"
):
    """
    Decrypt data.
    
    This endpoint decrypts the provided encrypted data.
    """
    try:
        logger.info(f"Decrypting data with key: {key_id}")
        
        # Initialize encryption
        encryption = DataEncryption()
        
        # Create encrypted data object
        from ...security.data_encryption import EncryptedData
        encrypted_obj = EncryptedData(
            encrypted_data=bytes.fromhex(encrypted_data),
            algorithm=algorithm,
            key_id=key_id,
            created_at=None,
            iv=None
        )
        
        # Decrypt data
        decrypted_data = encryption.decrypt_data(encrypted_obj, key_id)
        
        return {
            "decrypted_data": decrypted_data,
            "key_id": key_id,
            "algorithm": algorithm
        }
        
    except Exception as e:
        logger.error(f"Data decryption failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Data decryption failed: {str(e)}"
        )

def _detect_secrets(text: str) -> list:
    """Detect potential secrets in text using pattern matching."""
    import re
    
    secrets = []
    
    # Common secret patterns
    patterns = {
        "api_key": r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
        "secret_key": r"(?i)(secret[_-]?key|secretkey)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
        "password": r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"\n]{8,})['\"]?",
        "token": r"(?i)(token|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_.-]{20,})['\"]?",
        "aws_key": r"AKIA[0-9A-Z]{16}",
        "openai_key": r"sk-[a-zA-Z0-9]{48}",
        "github_token": r"ghp_[a-zA-Z0-9]{36}",
        "private_key": r"-----BEGIN (RSA )?PRIVATE KEY-----"
    }
    
    for secret_type, pattern in patterns.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            secrets.append({
                "type": secret_type,
                "value": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.8
            })
    
    return secrets

def _detect_malicious_content(text: str) -> list:
    """Detect potentially malicious content in text."""
    import re
    
    malicious = []
    
    # Malicious patterns
    patterns = {
        "sql_injection": r"(?i)(union\s+select|drop\s+table|delete\s+from|insert\s+into)",
        "xss": r"(?i)(<script|javascript:|onload=|onerror=)",
        "command_injection": r"(?i)(;|\||&|\$\(|\`.*\`)",
        "path_traversal": r"(?i)(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)"
    }
    
    for threat_type, pattern in patterns.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            malicious.append({
                "type": threat_type,
                "value": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.7
            })
    
    return malicious
