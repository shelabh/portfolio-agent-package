"""
Security & Privacy Module

This module provides advanced security and privacy features including
PII detection, data encryption, privacy-preserving techniques, compliance
frameworks, and audit logging.
"""

from .pii_detector import AdvancedPIIDetector, PIIType, PIIDetectionResult
from .data_encryption import DataEncryption, EncryptionConfig, EncryptedData
from .privacy_preserving import PrivacyPreserver, DifferentialPrivacy, DataAnonymizer
from .compliance_manager import ComplianceManager, GDPRCompliance, CCPACompliance
from .audit_logger import AuditLogger, AuditEvent, ComplianceAuditor
from .consent_manager import ConsentManager, ConsentRecord, DataRetentionManager

__all__ = [
    'AdvancedPIIDetector',
    'PIIType',
    'PIIDetectionResult',
    'DataEncryption',
    'EncryptionConfig',
    'EncryptedData',
    'PrivacyPreserver',
    'DifferentialPrivacy',
    'DataAnonymizer',
    'ComplianceManager',
    'GDPRCompliance',
    'CCPACompliance',
    'AuditLogger',
    'AuditEvent',
    'ComplianceAuditor',
    'ConsentManager',
    'ConsentRecord',
    'DataRetentionManager'
]
