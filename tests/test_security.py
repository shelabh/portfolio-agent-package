"""
Tests for Security & Privacy Module

This module contains comprehensive tests for all security and privacy features
including PII detection, data encryption, privacy-preserving techniques,
compliance management, audit logging, and consent management.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import security modules
from portfolio_agent.security.pii_detector import (
    AdvancedPIIDetector, PIIType, PIIDetectionResult
)
from portfolio_agent.security.data_encryption import (
    DataEncryption, EncryptionConfig, EncryptedData, EncryptionAlgorithm
)
from portfolio_agent.security.privacy_preserving import (
    PrivacyPreserver, PrivacyConfig, PrivacyTechnique, DifferentialPrivacy,
    DataAnonymizer
)
from portfolio_agent.security.compliance_manager import (
    ComplianceManager, ComplianceFramework, DataCategory, ProcessingPurpose,
    DataSubject, ComplianceViolation, ComplianceReport
)
from portfolio_agent.security.audit_logger import (
    AuditLogger, AuditEvent, AuditEventType, AuditSeverity, ComplianceAuditor
)
from portfolio_agent.security.consent_manager import (
    ConsentManager, ConsentRecord, ConsentType, DataRetentionPolicy,
    DataRetentionManager
)

class TestAdvancedPIIDetector:
    """Test advanced PII detector."""
    
    def test_pii_detector_initialization(self):
        """Test PII detector initialization."""
        detector = AdvancedPIIDetector()
        assert detector.confidence_threshold == 0.5
        assert len(detector.patterns) > 0
        assert len(detector.compiled_patterns) > 0
    
    def test_detect_pii_with_regex(self):
        """Test PII detection with regex patterns."""
        detector = AdvancedPIIDetector(use_spacy=False, use_presidio=False)
        
        test_text = "Contact me at john.doe@example.com or call 555-123-4567"
        result = detector.detect_pii(test_text)
        
        assert isinstance(result, PIIDetectionResult)
        assert result.text == test_text
        assert "[REDACTED]" in result.redacted_text
        assert len(result.detected_pii) > 0
        assert result.method_used == "regex"
    
    def test_detect_pii_with_different_redaction_methods(self):
        """Test PII detection with different redaction methods."""
        detector = AdvancedPIIDetector(use_spacy=False, use_presidio=False)
        
        test_text = "Email: test@example.com, Phone: 555-123-4567"
        
        # Test replace method
        result_replace = detector.detect_pii(test_text, redaction_method="replace")
        assert "[REDACTED]" in result_replace.redacted_text
        
        # Test hash method
        result_hash = detector.detect_pii(test_text, redaction_method="hash")
        assert "[REDACTED]" not in result_hash.redacted_text
        assert len(result_hash.redacted_text) > 0
        
        # Test mask method
        result_mask = detector.detect_pii(test_text, redaction_method="mask")
        assert "*" in result_mask.redacted_text
    
    def test_detect_pii_with_custom_patterns(self):
        """Test PII detection with custom patterns."""
        custom_patterns = {
            PIIType.API_KEY: r"api_key_[A-Za-z0-9]{20,}"
        }
        
        detector = AdvancedPIIDetector(
            use_spacy=False, 
            use_presidio=False,
            custom_patterns=custom_patterns
        )
        
        test_text = "API key: api_key_abcdefghijklmnopqrstuvwxyz123456"
        result = detector.detect_pii(test_text)
        
        assert len(result.detected_pii) > 0
        assert any(pii["type"] == "api_key" for pii in result.detected_pii)
    
    def test_pii_detection_result_validation(self):
        """Test PII detection result validation."""
        detector = AdvancedPIIDetector(use_spacy=False, use_presidio=False)
        
        test_text = "Test text with email@example.com"
        result = detector.detect_pii(test_text)
        
        assert detector.validate_pii_detection(result)
        
        # Test invalid result
        invalid_result = PIIDetectionResult(
            text="",
            redacted_text="",
            detected_pii=[],
            confidence_scores={},
            redaction_stats={},
            processing_time=-1,
            method_used="test"
        )
        assert not detector.validate_pii_detection(invalid_result)
    
    def test_get_detection_stats(self):
        """Test getting detection statistics."""
        detector = AdvancedPIIDetector()
        stats = detector.get_detection_stats()
        
        assert "spacy_available" in stats
        assert "presidio_available" in stats
        assert "patterns_count" in stats
        assert "confidence_threshold" in stats
        assert "supported_pii_types" in stats

class TestDataEncryption:
    """Test data encryption functionality."""
    
    def test_encryption_initialization(self):
        """Test encryption manager initialization."""
        config = EncryptionConfig(algorithm=EncryptionAlgorithm.FERNET)
        encryption = DataEncryption(config)
        
        assert encryption.config.algorithm == EncryptionAlgorithm.FERNET
        assert len(encryption.active_keys) == 0
    
    def test_generate_key(self):
        """Test key generation."""
        encryption = DataEncryption()
        key_id = encryption.generate_key()
        
        assert key_id is not None
        assert key_id in encryption.active_keys
        assert len(encryption.active_keys) == 1
    
    def test_derive_key_from_password(self):
        """Test key derivation from password."""
        encryption = DataEncryption()
        password = "test_password"
        key_id = encryption.derive_key_from_password(password)
        
        assert key_id is not None
        assert key_id in encryption.active_keys
    
    def test_encrypt_and_decrypt_text(self):
        """Test text encryption and decryption."""
        encryption = DataEncryption()
        key_id = encryption.generate_key()
        
        original_text = "This is a test message"
        encrypted_data = encryption.encrypt_data(original_text, key_id)
        
        assert isinstance(encrypted_data, EncryptedData)
        assert encrypted_data.encrypted_data != original_text
        assert encrypted_data.key_id == key_id
        
        decrypted_text = encryption.decrypt_data(encrypted_data, key_id)
        assert decrypted_text == original_text
    
    def test_encrypt_and_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        encryption = DataEncryption()
        key_id = encryption.generate_key()
        
        original_dict = {"name": "John", "age": 30, "email": "john@example.com"}
        encrypted_data = encryption.encrypt_data(original_dict, key_id)
        
        decrypted_dict = encryption.decrypt_data(encrypted_data, key_id)
        assert decrypted_dict == original_dict
    
    def test_encrypt_and_decrypt_file(self):
        """Test file encryption and decryption."""
        encryption = DataEncryption()
        key_id = encryption.generate_key()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test file content")
            temp_file = f.name
        
        try:
            # Encrypt file
            encrypted_data = encryption.encrypt_file(temp_file, key_id=key_id)
            
            # Decrypt file
            with tempfile.NamedTemporaryFile(delete=False) as f:
                decrypted_file = f.name
            
            try:
                decrypted_data = encryption.decrypt_file(encrypted_data, decrypted_file, key_id)
                
                # Read decrypted file
                with open(decrypted_file, 'r') as f:
                    decrypted_content = f.read()
                
                assert decrypted_content == "Test file content"
            finally:
                os.unlink(decrypted_file)
        finally:
            os.unlink(temp_file)
    
    def test_key_rotation(self):
        """Test key rotation."""
        encryption = DataEncryption()
        old_key_id = encryption.generate_key()
        new_key_id = encryption.rotate_key(old_key_id)
        
        assert new_key_id != old_key_id
        assert new_key_id in encryption.active_keys
        assert old_key_id in encryption.active_keys  # Old key should still be available for decryption
    
    def test_get_encryption_stats(self):
        """Test getting encryption statistics."""
        encryption = DataEncryption()
        encryption.generate_key()
        
        stats = encryption.get_encryption_stats()
        assert "algorithm" in stats
        assert "key_size" in stats
        assert "active_keys" in stats
        assert "total_keys" in stats

class TestPrivacyPreserving:
    """Test privacy-preserving techniques."""
    
    def test_differential_privacy_initialization(self):
        """Test differential privacy initialization."""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
        assert dp.epsilon == 1.0
        assert dp.delta == 1e-5
    
    def test_add_laplace_noise(self):
        """Test adding Laplace noise."""
        dp = DifferentialPrivacy(epsilon=1.0)
        original_value = 100.0
        noisy_value = dp.add_laplace_noise(original_value, sensitivity=1.0)
        
        assert noisy_value != original_value
        assert isinstance(noisy_value, float)
    
    def test_add_gaussian_noise(self):
        """Test adding Gaussian noise."""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
        original_value = 100.0
        noisy_value = dp.add_gaussian_noise(original_value, sensitivity=1.0)
        
        assert noisy_value != original_value
        assert isinstance(noisy_value, float)
    
    def test_private_count(self):
        """Test private count computation."""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = [1, 2, 3, 4, 5]
        query = lambda x: x > 3
        
        private_count = dp.private_count(data, query)
        assert isinstance(private_count, float)
        assert private_count >= 0
    
    def test_private_sum(self):
        """Test private sum computation."""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        private_sum = dp.private_sum(data, sensitivity=1.0)
        assert isinstance(private_sum, float)
    
    def test_private_mean(self):
        """Test private mean computation."""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        private_mean = dp.private_mean(data, sensitivity=1.0)
        assert isinstance(private_mean, float)
    
    def test_private_histogram(self):
        """Test private histogram computation."""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = ["A", "B", "A", "C", "B", "A"]
        bins = ["A", "B", "C"]
        
        private_hist = dp.private_histogram(data, bins)
        assert isinstance(private_hist, dict)
        assert all(bin_val in private_hist for bin_val in bins)
        assert all(isinstance(count, float) for count in private_hist.values())
    
    def test_data_anonymizer_initialization(self):
        """Test data anonymizer initialization."""
        config = PrivacyConfig(technique=PrivacyTechnique.K_ANONYMITY, k=3)
        anonymizer = DataAnonymizer(config)
        assert anonymizer.config.technique == PrivacyTechnique.K_ANONYMITY
    
    def test_k_anonymity(self):
        """Test k-anonymity implementation."""
        config = PrivacyConfig(technique=PrivacyTechnique.K_ANONYMITY, k=2)
        anonymizer = DataAnonymizer(config)
        
        data = [
            {"age": "20-30", "city": "NYC", "salary": 50000},
            {"age": "20-30", "city": "NYC", "salary": 55000},
            {"age": "30-40", "city": "LA", "salary": 60000},
            {"age": "30-40", "city": "LA", "salary": 65000}
        ]
        
        quasi_identifiers = ["age", "city"]
        k_anonymous_data = anonymizer.k_anonymize(data, quasi_identifiers)
        
        assert len(k_anonymous_data) <= len(data)
    
    def test_data_masking(self):
        """Test data masking."""
        config = PrivacyConfig(technique=PrivacyTechnique.DATA_MASKING)
        anonymizer = DataAnonymizer(config)
        
        data = [
            {"name": "John Doe", "email": "john@example.com", "phone": "555-123-4567"}
        ]
        
        masking_rules = {"name": "*", "email": "*", "phone": "*"}
        masked_data = anonymizer.mask_data(data, masking_rules)
        
        assert len(masked_data) == 1
        assert "*" in masked_data[0]["name"]
        assert "*" in masked_data[0]["email"]
        assert "*" in masked_data[0]["phone"]
    
    def test_pseudonymization(self):
        """Test data pseudonymization."""
        config = PrivacyConfig(technique=PrivacyTechnique.PSEUDONYMIZATION)
        anonymizer = DataAnonymizer(config)
        
        data = [
            {"name": "John Doe", "email": "john@example.com"}
        ]
        
        pseudonymization_rules = {"name": "USER", "email": "EMAIL"}
        pseudonymized_data = anonymizer.pseudonymize_data(data, pseudonymization_rules)
        
        assert len(pseudonymized_data) == 1
        assert pseudonymized_data[0]["name"].startswith("USER_")
        assert pseudonymized_data[0]["email"].startswith("EMAIL_")
    
    def test_privacy_preserver_initialization(self):
        """Test privacy preserver initialization."""
        config = PrivacyConfig(technique=PrivacyTechnique.DIFFERENTIAL_PRIVACY)
        preserver = PrivacyPreserver(config)
        assert preserver.config.technique == PrivacyTechnique.DIFFERENTIAL_PRIVACY
    
    def test_privacy_preserver_with_differential_privacy(self):
        """Test privacy preserver with differential privacy."""
        config = PrivacyConfig(technique=PrivacyTechnique.DIFFERENTIAL_PRIVACY)
        preserver = PrivacyPreserver(config)
        
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        private_data = preserver.preserve_privacy(data, sensitivity=1.0)
        
        assert len(private_data) == len(data)
        assert all(isinstance(value, float) for value in private_data)
    
    def test_get_privacy_stats(self):
        """Test getting privacy statistics."""
        config = PrivacyConfig(technique=PrivacyTechnique.DIFFERENTIAL_PRIVACY)
        preserver = PrivacyPreserver(config)
        
        stats = preserver.get_privacy_stats()
        assert "technique" in stats
        assert "epsilon" in stats
        assert "delta" in stats

class TestComplianceManager:
    """Test compliance management functionality."""
    
    def test_compliance_manager_initialization(self):
        """Test compliance manager initialization."""
        manager = ComplianceManager()
        assert manager.gdpr is not None
        assert manager.ccpa is not None
    
    def test_register_data_subject_gdpr(self):
        """Test registering data subject for GDPR."""
        manager = ComplianceManager()
        subject_id = manager.register_data_subject(
            "test_subject",
            ComplianceFramework.GDPR,
            email="test@example.com"
        )
        
        assert subject_id == "test_subject"
        assert "test_subject" in manager.gdpr.data_subjects
    
    def test_register_data_subject_ccpa(self):
        """Test registering data subject for CCPA."""
        manager = ComplianceManager()
        subject_id = manager.register_data_subject(
            "test_consumer",
            ComplianceFramework.CCPA,
            email="consumer@example.com"
        )
        
        assert subject_id == "test_consumer"
        assert "test_consumer" in manager.ccpa.consumers
    
    def test_gdpr_consent_management(self):
        """Test GDPR consent management."""
        manager = ComplianceManager()
        subject_id = manager.register_data_subject(
            "test_subject",
            ComplianceFramework.GDPR
        )
        
        # Update consent
        success = manager.gdpr.update_consent(
            subject_id,
            consent_given=True,
            purpose=ProcessingPurpose.CONSENT
        )
        
        assert success
        assert manager.gdpr.data_subjects[subject_id].consent_given
    
    def test_gdpr_processing_activity_recording(self):
        """Test GDPR processing activity recording."""
        manager = ComplianceManager()
        subject_id = manager.register_data_subject(
            "test_subject",
            ComplianceFramework.GDPR
        )
        
        record_id = manager.gdpr.record_processing_activity(
            subject_id,
            [DataCategory.PERSONAL_DATA],
            ProcessingPurpose.CONSENT,
            "consent",
            "Data processing for consent management"
        )
        
        assert record_id is not None
        assert len(manager.gdpr.processing_records) == 1
    
    def test_gdpr_compliance_checking(self):
        """Test GDPR compliance checking."""
        manager = ComplianceManager()
        subject_id = manager.register_data_subject(
            "test_subject",
            ComplianceFramework.GDPR
        )
        
        # Check consent compliance
        violations = manager.gdpr.check_consent_compliance()
        assert isinstance(violations, list)
        
        # Check data retention compliance
        violations = manager.gdpr.check_data_retention_compliance()
        assert isinstance(violations, list)
    
    def test_gdpr_compliance_report_generation(self):
        """Test GDPR compliance report generation."""
        manager = ComplianceManager()
        subject_id = manager.register_data_subject(
            "test_subject",
            ComplianceFramework.GDPR
        )
        
        report = manager.gdpr.generate_compliance_report()
        assert isinstance(report, ComplianceReport)
        assert report.framework == ComplianceFramework.GDPR
        assert "compliance_score" in report.__dict__
    
    def test_ccpa_data_sale_recording(self):
        """Test CCPA data sale recording."""
        manager = ComplianceManager()
        consumer_id = manager.register_data_subject(
            "test_consumer",
            ComplianceFramework.CCPA
        )
        
        sale_id = manager.ccpa.record_data_sale(
            consumer_id,
            [DataCategory.PERSONAL_DATA],
            "third_party_1",
            "marketing"
        )
        
        assert sale_id is not None
        assert len(manager.ccpa.data_sales) == 1
    
    def test_ccpa_compliance_checking(self):
        """Test CCPA compliance checking."""
        manager = ComplianceManager()
        consumer_id = manager.register_data_subject(
            "test_consumer",
            ComplianceFramework.CCPA
        )
        
        # Check opt-out compliance
        violations = manager.ccpa.check_opt_out_compliance()
        assert isinstance(violations, list)
        
        # Check disclosure compliance
        violations = manager.ccpa.check_disclosure_compliance()
        assert isinstance(violations, list)
    
    def test_ccpa_compliance_report_generation(self):
        """Test CCPA compliance report generation."""
        manager = ComplianceManager()
        consumer_id = manager.register_data_subject(
            "test_consumer",
            ComplianceFramework.CCPA
        )
        
        report = manager.ccpa.generate_compliance_report()
        assert isinstance(report, ComplianceReport)
        assert report.framework == ComplianceFramework.CCPA
    
    def test_compliance_manager_check_compliance(self):
        """Test compliance manager compliance checking."""
        manager = ComplianceManager()
        subject_id = manager.register_data_subject(
            "test_subject",
            ComplianceFramework.GDPR
        )
        
        violations = manager.check_compliance(ComplianceFramework.GDPR)
        assert isinstance(violations, list)
    
    def test_compliance_manager_generate_report(self):
        """Test compliance manager report generation."""
        manager = ComplianceManager()
        subject_id = manager.register_data_subject(
            "test_subject",
            ComplianceFramework.GDPR
        )
        
        report = manager.generate_compliance_report(ComplianceFramework.GDPR)
        assert isinstance(report, ComplianceReport)
    
    def test_get_compliance_stats(self):
        """Test getting compliance statistics."""
        manager = ComplianceManager()
        manager.register_data_subject("test_subject", ComplianceFramework.GDPR)
        manager.register_data_subject("test_consumer", ComplianceFramework.CCPA)
        
        stats = manager.get_compliance_stats()
        assert "supported_frameworks" in stats
        assert "gdpr_subjects" in stats
        assert "ccpa_consumers" in stats
        assert "total_violations" in stats

class TestAuditLogger:
    """Test audit logging functionality."""
    
    def test_audit_logger_initialization(self):
        """Test audit logger initialization."""
        logger = AuditLogger(max_events=1000, retention_days=30)
        assert logger.max_events == 1000
        assert logger.retention_days == 30
        assert len(logger.events) == 0
    
    def test_log_event(self):
        """Test logging audit event."""
        logger = AuditLogger()
        event_id = logger.log_event(
            AuditEventType.AUTHENTICATION,
            AuditSeverity.HIGH,
            user_id="test_user",
            action="login",
            outcome="success"
        )
        
        assert event_id is not None
        assert len(logger.events) == 1
        assert event_id in logger.event_index
    
    def test_log_authentication(self):
        """Test logging authentication event."""
        logger = AuditLogger()
        event_id = logger.log_authentication(
            "test_user",
            success=True,
            ip_address="192.168.1.1"
        )
        
        assert event_id is not None
        event = logger.get_event_by_id(event_id)
        assert event.event_type == AuditEventType.AUTHENTICATION
        assert event.user_id == "test_user"
        assert event.outcome == "success"
    
    def test_log_data_access(self):
        """Test logging data access event."""
        logger = AuditLogger()
        event_id = logger.log_data_access(
            "test_user",
            "user_data",
            "read",
            success=True
        )
        
        assert event_id is not None
        event = logger.get_event_by_id(event_id)
        assert event.event_type == AuditEventType.DATA_ACCESS
        assert event.resource == "user_data"
        assert event.action == "read"
    
    def test_log_data_modification(self):
        """Test logging data modification event."""
        logger = AuditLogger()
        event_id = logger.log_data_modification(
            "test_user",
            "user_data",
            "update",
            success=True
        )
        
        assert event_id is not None
        event = logger.get_event_by_id(event_id)
        assert event.event_type == AuditEventType.DATA_MODIFICATION
        assert event.resource == "user_data"
        assert event.action == "update"
    
    def test_log_security_event(self):
        """Test logging security event."""
        logger = AuditLogger()
        event_id = logger.log_security_event(
            "suspicious_activity",
            AuditSeverity.HIGH,
            user_id="test_user"
        )
        
        assert event_id is not None
        event = logger.get_event_by_id(event_id)
        assert event.event_type == AuditEventType.SECURITY_EVENT
        assert event.severity == AuditSeverity.HIGH
        assert event.action == "suspicious_activity"
    
    def test_log_compliance_event(self):
        """Test logging compliance event."""
        logger = AuditLogger()
        event_id = logger.log_compliance_event(
            "gdpr_violation",
            AuditSeverity.CRITICAL
        )
        
        assert event_id is not None
        event = logger.get_event_by_id(event_id)
        assert event.event_type == AuditEventType.COMPLIANCE_EVENT
        assert event.severity == AuditSeverity.CRITICAL
        assert event.action == "gdpr_violation"
    
    def test_get_events_with_filters(self):
        """Test getting events with filters."""
        logger = AuditLogger()
        
        # Log multiple events
        logger.log_authentication("user1", success=True)
        logger.log_authentication("user2", success=False)
        logger.log_data_access("user1", "data1", "read")
        
        # Filter by user
        user_events = logger.get_events(user_id="user1")
        assert len(user_events) == 2
        
        # Filter by event type
        auth_events = logger.get_events(event_type=AuditEventType.AUTHENTICATION)
        assert len(auth_events) == 2
        
        # Filter by severity
        high_severity_events = logger.get_events(severity=AuditSeverity.HIGH)
        assert len(high_severity_events) >= 0
    
    def test_get_user_activity(self):
        """Test getting user activity."""
        logger = AuditLogger()
        logger.log_authentication("test_user", success=True)
        logger.log_data_access("test_user", "data1", "read")
        
        activity = logger.get_user_activity("test_user", hours=24)
        assert len(activity) == 2
    
    def test_get_security_events(self):
        """Test getting security events."""
        logger = AuditLogger()
        logger.log_security_event("threat_detected", AuditSeverity.HIGH)
        logger.log_authentication("user1", success=True)
        
        security_events = logger.get_security_events(hours=24)
        assert len(security_events) == 1
        assert security_events[0].action == "threat_detected"
    
    def test_get_failed_authentications(self):
        """Test getting failed authentication events."""
        logger = AuditLogger()
        logger.log_authentication("user1", success=True)
        logger.log_authentication("user2", success=False)
        
        failed_auths = logger.get_failed_authentications(hours=24)
        assert len(failed_auths) == 1
        assert failed_auths[0].user_id == "user2"
        assert failed_auths[0].outcome == "failure"
    
    def test_export_events(self):
        """Test exporting events."""
        logger = AuditLogger()
        logger.log_authentication("test_user", success=True)
        
        # Export as JSON
        json_export = logger.export_events(format="json")
        assert isinstance(json_export, str)
        assert "test_user" in json_export
        
        # Export as dict
        dict_export = logger.export_events(format="dict")
        assert isinstance(dict_export, list)
        assert len(dict_export) == 1
    
    def test_get_audit_stats(self):
        """Test getting audit statistics."""
        logger = AuditLogger()
        logger.log_authentication("user1", success=True)
        logger.log_authentication("user2", success=False)
        
        stats = logger.get_audit_stats()
        assert "total_events" in stats
        assert "events_by_type" in stats
        assert "events_by_severity" in stats
        assert "events_by_user" in stats
        assert "events_by_outcome" in stats
        assert stats["total_events"] == 2

class TestComplianceAuditor:
    """Test compliance auditor functionality."""
    
    def test_compliance_auditor_initialization(self):
        """Test compliance auditor initialization."""
        audit_logger = AuditLogger()
        auditor = ComplianceAuditor(audit_logger)
        assert auditor.audit_logger == audit_logger
    
    def test_audit_data_access_compliance(self):
        """Test data access compliance auditing."""
        audit_logger = AuditLogger()
        auditor = ComplianceAuditor(audit_logger)
        
        # Log some data access events
        audit_logger.log_data_access("user1", "data1", "read", success=True)
        audit_logger.log_data_access("user2", "data2", "read", success=False)
        
        compliance = auditor.audit_data_access_compliance(hours=24)
        assert "total_data_access" in compliance
        assert "unauthorized_access" in compliance
        assert "compliance_rate" in compliance
        assert "violations" in compliance
    
    def test_audit_authentication_compliance(self):
        """Test authentication compliance auditing."""
        audit_logger = AuditLogger()
        auditor = ComplianceAuditor(audit_logger)
        
        # Log some authentication events
        audit_logger.log_authentication("user1", success=True)
        audit_logger.log_authentication("user2", success=False)
        
        compliance = auditor.audit_authentication_compliance(hours=24)
        assert "total_authentications" in compliance
        assert "failed_authentications" in compliance
        assert "success_rate" in compliance
        assert "security_concerns" in compliance
    
    def test_audit_security_compliance(self):
        """Test security compliance auditing."""
        audit_logger = AuditLogger()
        auditor = ComplianceAuditor(audit_logger)
        
        # Log some security events
        audit_logger.log_security_event("threat_detected", AuditSeverity.HIGH)
        audit_logger.log_security_event("vulnerability_found", AuditSeverity.CRITICAL)
        
        compliance = auditor.audit_security_compliance(hours=24)
        assert "total_security_events" in compliance
        assert "critical_events" in compliance
        assert "high_severity_events" in compliance
        assert "security_incidents" in compliance
    
    def test_generate_compliance_report(self):
        """Test generating compliance report."""
        audit_logger = AuditLogger()
        auditor = ComplianceAuditor(audit_logger)
        
        # Log some events
        audit_logger.log_authentication("user1", success=True)
        audit_logger.log_data_access("user1", "data1", "read", success=True)
        audit_logger.log_security_event("threat_detected", AuditSeverity.HIGH)
        
        report = auditor.generate_compliance_report(hours=24)
        assert "overall_compliance_score" in report
        assert "data_access_compliance" in report
        assert "authentication_compliance" in report
        assert "security_compliance" in report
        assert "report_generated_at" in report
        assert "audit_period_hours" in report

class TestConsentManager:
    """Test consent management functionality."""
    
    def test_consent_manager_initialization(self):
        """Test consent manager initialization."""
        manager = ConsentManager(default_retention_days=365)
        assert manager.default_retention_days == 365
        assert len(manager.consent_records) == 0
    
    def test_grant_consent(self):
        """Test granting consent."""
        manager = ConsentManager()
        consent_id = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT],
            consent_type=ConsentType.EXPLICIT
        )
        
        assert consent_id is not None
        assert consent_id in manager.consent_records
        assert manager.consent_records[consent_id].granted
    
    def test_withdraw_consent(self):
        """Test withdrawing consent."""
        manager = ConsentManager()
        consent_id = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        
        success = manager.withdraw_consent(consent_id, reason="User requested")
        assert success
        assert not manager.consent_records[consent_id].granted
        assert manager.consent_records[consent_id].withdrawn_at is not None
    
    def test_check_consent(self):
        """Test checking consent."""
        manager = ConsentManager()
        consent_id = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        
        # Check valid consent
        has_consent = manager.check_consent(
            "test_subject",
            DataCategory.PERSONAL_DATA,
            ProcessingPurpose.CONSENT
        )
        assert has_consent
        
        # Check invalid consent
        has_consent = manager.check_consent(
            "test_subject",
            DataCategory.SENSITIVE_DATA,
            ProcessingPurpose.MARKETING
        )
        assert not has_consent
    
    def test_get_consent_records(self):
        """Test getting consent records."""
        manager = ConsentManager()
        consent_id1 = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        consent_id2 = manager.grant_consent(
            "test_subject",
            [DataCategory.SENSITIVE_DATA],
            [ProcessingPurpose.MARKETING]
        )
        
        # Get all consents for subject
        records = manager.get_consent_records(subject_id="test_subject")
        assert len(records) == 2
        
        # Get consents for specific category
        records = manager.get_consent_records(data_category=DataCategory.PERSONAL_DATA)
        assert len(records) == 1
        
        # Get only valid consents
        records = manager.get_consent_records(valid_only=True)
        assert len(records) == 2
    
    def test_get_subject_consent_summary(self):
        """Test getting subject consent summary."""
        manager = ConsentManager()
        consent_id1 = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        consent_id2 = manager.grant_consent(
            "test_subject",
            [DataCategory.SENSITIVE_DATA],
            [ProcessingPurpose.MARKETING]
        )
        
        summary = manager.get_subject_consent_summary("test_subject")
        assert summary["subject_id"] == "test_subject"
        assert summary["total_consents"] == 2
        assert summary["active_consents"] == 2
        assert len(summary["data_categories"]) == 2
        assert len(summary["processing_purposes"]) == 2
    
    def test_create_retention_policy(self):
        """Test creating retention policy."""
        manager = ConsentManager()
        policy_id = manager.create_retention_policy(
            DataCategory.PERSONAL_DATA,
            ProcessingPurpose.CONSENT,
            timedelta(days=365),
            auto_delete=True
        )
        
        assert policy_id is not None
        assert policy_id in manager.retention_policies
    
    def test_get_retention_policy(self):
        """Test getting retention policy."""
        manager = ConsentManager()
        policy_id = manager.create_retention_policy(
            DataCategory.PERSONAL_DATA,
            ProcessingPurpose.CONSENT,
            timedelta(days=365)
        )
        
        policy = manager.get_retention_policy(
            DataCategory.PERSONAL_DATA,
            ProcessingPurpose.CONSENT
        )
        
        assert policy is not None
        assert policy.policy_id == policy_id
        assert policy.retention_period.days == 365
    
    def test_get_expired_consents(self):
        """Test getting expired consents."""
        manager = ConsentManager()
        consent_id = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT],
            expires_at=datetime.now() - timedelta(days=1)  # Expired yesterday
        )
        
        expired_consents = manager.get_expired_consents()
        assert len(expired_consents) == 1
        assert expired_consents[0].consent_id == consent_id
    
    def test_cleanup_expired_consents(self):
        """Test cleaning up expired consents."""
        manager = ConsentManager()
        consent_id = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT],
            expires_at=datetime.now() - timedelta(days=1)  # Expired yesterday
        )
        
        cleaned_count = manager.cleanup_expired_consents()
        assert cleaned_count == 1
        assert consent_id not in manager.consent_records
    
    def test_export_consent_data(self):
        """Test exporting consent data."""
        manager = ConsentManager()
        consent_id = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        
        export_data = manager.export_consent_data("test_subject")
        assert "export_timestamp" in export_data
        assert "subject_id" in export_data
        assert "consent_records" in export_data
        assert "retention_policies" in export_data
        assert len(export_data["consent_records"]) == 1
    
    def test_get_consent_stats(self):
        """Test getting consent statistics."""
        manager = ConsentManager()
        consent_id1 = manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        consent_id2 = manager.grant_consent(
            "test_subject",
            [DataCategory.SENSITIVE_DATA],
            [ProcessingPurpose.MARKETING]
        )
        
        stats = manager.get_consent_stats()
        assert "total_consents" in stats
        assert "active_consents" in stats
        assert "withdrawn_consents" in stats
        assert "expired_consents" in stats
        assert "retention_policies" in stats
        assert "unique_subjects" in stats
        assert "consent_types" in stats

class TestDataRetentionManager:
    """Test data retention management functionality."""
    
    def test_data_retention_manager_initialization(self):
        """Test data retention manager initialization."""
        consent_manager = ConsentManager()
        retention_manager = DataRetentionManager(consent_manager)
        assert retention_manager.consent_manager == consent_manager
    
    def test_get_retention_deadline(self):
        """Test getting retention deadline."""
        consent_manager = ConsentManager()
        retention_manager = DataRetentionManager(consent_manager)
        
        # Create retention policy
        policy_id = consent_manager.create_retention_policy(
            DataCategory.PERSONAL_DATA,
            ProcessingPurpose.CONSENT,
            timedelta(days=365)
        )
        
        # Grant consent
        consent_id = consent_manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        
        deadline = retention_manager.get_retention_deadline(
            "test_subject",
            DataCategory.PERSONAL_DATA,
            ProcessingPurpose.CONSENT
        )
        
        assert deadline is not None
        assert isinstance(deadline, datetime)
    
    def test_get_data_for_deletion(self):
        """Test getting data for deletion."""
        consent_manager = ConsentManager()
        retention_manager = DataRetentionManager(consent_manager)
        
        # Create retention policy with short period
        policy_id = consent_manager.create_retention_policy(
            DataCategory.PERSONAL_DATA,
            ProcessingPurpose.CONSENT,
            timedelta(days=1)  # 1 day retention
        )
        
        # Grant consent with old timestamp
        consent_id = consent_manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        
        # Manually set old timestamp
        consent_record = consent_manager.consent_records[consent_id]
        consent_record.created_at = datetime.now() - timedelta(days=2)
        
        deletion_records = retention_manager.get_data_for_deletion()
        assert len(deletion_records) == 1
        assert deletion_records[0]["subject_id"] == "test_subject"
    
    def test_cleanup_expired_data(self):
        """Test cleaning up expired data."""
        consent_manager = ConsentManager()
        retention_manager = DataRetentionManager(consent_manager)
        
        # Create retention policy with short period
        policy_id = consent_manager.create_retention_policy(
            DataCategory.PERSONAL_DATA,
            ProcessingPurpose.CONSENT,
            timedelta(days=1)  # 1 day retention
        )
        
        # Grant consent with old timestamp
        consent_id = consent_manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        
        # Manually set old timestamp
        consent_record = consent_manager.consent_records[consent_id]
        consent_record.created_at = datetime.now() - timedelta(days=2)
        
        cleanup_count = retention_manager.cleanup_expired_data()
        assert cleanup_count == 1

# Integration tests
class TestSecurityIntegration:
    """Test security module integration."""
    
    def test_pii_detection_with_encryption(self):
        """Test PII detection followed by encryption."""
        # Detect PII
        detector = AdvancedPIIDetector(use_spacy=False, use_presidio=False)
        test_text = "Contact me at john.doe@example.com"
        pii_result = detector.detect_pii(test_text)
        
        # Encrypt the redacted text
        encryption = DataEncryption()
        key_id = encryption.generate_key()
        encrypted_data = encryption.encrypt_data(pii_result.redacted_text, key_id)
        
        # Decrypt and verify
        decrypted_text = encryption.decrypt_data(encrypted_data, key_id)
        assert decrypted_text == pii_result.redacted_text
    
    def test_privacy_preserving_with_audit_logging(self):
        """Test privacy-preserving techniques with audit logging."""
        # Apply differential privacy
        config = PrivacyConfig(technique=PrivacyTechnique.DIFFERENTIAL_PRIVACY)
        preserver = PrivacyPreserver(config)
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        private_data = preserver.preserve_privacy(data, sensitivity=1.0)
        
        # Log the privacy-preserving operation
        audit_logger = AuditLogger()
        event_id = audit_logger.log_privacy_event(
            "differential_privacy_applied",
            AuditSeverity.MEDIUM,
            details={"original_data_length": len(data), "private_data_length": len(private_data)}
        )
        
        assert event_id is not None
        event = audit_logger.get_event_by_id(event_id)
        assert event.event_type == AuditEventType.PRIVACY_EVENT
    
    def test_compliance_with_consent_management(self):
        """Test compliance checking with consent management."""
        # Set up consent manager
        consent_manager = ConsentManager()
        consent_id = consent_manager.grant_consent(
            "test_subject",
            [DataCategory.PERSONAL_DATA],
            [ProcessingPurpose.CONSENT]
        )
        
        # Set up compliance manager
        compliance_manager = ComplianceManager()
        subject_id = compliance_manager.register_data_subject(
            "test_subject",
            ComplianceFramework.GDPR
        )
        
        # Update consent in compliance manager
        compliance_manager.gdpr.update_consent(
            subject_id,
            consent_given=True,
            purpose=ProcessingPurpose.CONSENT
        )
        
        # Check compliance
        violations = compliance_manager.check_compliance(ComplianceFramework.GDPR)
        assert isinstance(violations, list)
    
    def test_audit_logging_with_compliance_auditing(self):
        """Test audit logging with compliance auditing."""
        # Set up audit logger
        audit_logger = AuditLogger()
        audit_logger.log_authentication("user1", success=True)
        audit_logger.log_data_access("user1", "data1", "read", success=True)
        audit_logger.log_security_event("threat_detected", AuditSeverity.HIGH)
        
        # Set up compliance auditor
        auditor = ComplianceAuditor(audit_logger)
        
        # Generate compliance report
        report = auditor.generate_compliance_report(hours=24)
        assert "overall_compliance_score" in report
        assert "data_access_compliance" in report
        assert "authentication_compliance" in report
        assert "security_compliance" in report

if __name__ == "__main__":
    pytest.main([__file__])
