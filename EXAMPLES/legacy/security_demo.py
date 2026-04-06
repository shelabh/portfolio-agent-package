"""
Security & Privacy Demo

This demo showcases the comprehensive security and privacy features
including PII detection, data encryption, privacy-preserving techniques,
compliance management, audit logging, and consent management.
"""

import os
import sys
import json
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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

def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_subsection(title: str):
    """Print a subsection header."""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def demo_pii_detection():
    """Demo PII detection and redaction."""
    print_section("PII Detection & Redaction Demo")
    
    # Initialize PII detector
    detector = AdvancedPIIDetector(use_spacy=False, use_presidio=False)
    
    # Sample text with various PII
    sample_text = """
    Hello, my name is John Doe and I work at Acme Corp.
    You can reach me at john.doe@example.com or call me at 555-123-4567.
    My SSN is 123-45-6789 and my credit card number is 4532-1234-5678-9012.
    I live at 123 Main Street, New York, NY 10001.
    My API key is sk_abcdefghijklmnopqrstuvwxyz123456789.
    """
    
    print("Original text:")
    print(sample_text)
    
    # Detect PII with different redaction methods
    redaction_methods = ["replace", "hash", "mask"]
    
    for method in redaction_methods:
        print_subsection(f"Redaction Method: {method}")
        result = detector.detect_pii(sample_text, redaction_method=method)
        
        print(f"Redacted text: {result.redacted_text}")
        print(f"Detected PII types: {[pii['type'] for pii in result.detected_pii]}")
        print(f"Confidence scores: {result.confidence_scores}")
        print(f"Redaction stats: {result.redaction_stats}")
        print(f"Processing time: {result.processing_time:.3f}s")
        print(f"Method used: {result.method_used}")
    
    # Test with custom patterns
    print_subsection("Custom PII Patterns")
    custom_patterns = {
        PIIType.API_KEY: r"sk_[A-Za-z0-9]{20,}"
    }
    
    custom_detector = AdvancedPIIDetector(
        use_spacy=False,
        use_presidio=False,
        custom_patterns=custom_patterns
    )
    
    result = custom_detector.detect_pii(sample_text)
    print(f"Custom pattern detection: {[pii['type'] for pii in result.detected_pii]}")
    
    # Get detection statistics
    stats = detector.get_detection_stats()
    print_subsection("Detection Statistics")
    print(f"Available patterns: {stats['patterns_count']}")
    print(f"Supported PII types: {len(stats['supported_pii_types'])}")
    print(f"Confidence threshold: {stats['confidence_threshold']}")

def demo_data_encryption():
    """Demo data encryption and decryption."""
    print_section("Data Encryption & Decryption Demo")
    
    # Initialize encryption manager
    config = EncryptionConfig(algorithm=EncryptionAlgorithm.FERNET)
    encryption = DataEncryption(config)
    
    # Generate encryption key
    key_id = encryption.generate_key()
    print(f"Generated encryption key: {key_id}")
    
    # Test data
    test_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "sensitive_info": "This is confidential data"
    }
    
    print_subsection("Encrypting Data")
    print(f"Original data: {json.dumps(test_data, indent=2)}")
    
    # Encrypt data
    encrypted_data = encryption.encrypt_data(test_data, key_id)
    print(f"Encrypted data size: {len(encrypted_data.encrypted_data)} bytes")
    print(f"Algorithm: {encrypted_data.algorithm}")
    print(f"Key ID: {encrypted_data.key_id}")
    print(f"Created at: {encrypted_data.created_at}")
    
    # Decrypt data
    print_subsection("Decrypting Data")
    decrypted_data = encryption.decrypt_data(encrypted_data, key_id)
    print(f"Decrypted data: {json.dumps(decrypted_data, indent=2)}")
    print(f"Data integrity: {test_data == decrypted_data}")
    
    # Test file encryption
    print_subsection("File Encryption")
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("This is a test file with sensitive information.")
        temp_file = f.name
    
    try:
        # Encrypt file
        encrypted_file_data = encryption.encrypt_file(temp_file, key_id=key_id)
        print(f"File encrypted successfully")
        
        # Decrypt file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            decrypted_file = f.name
        
        try:
            decrypted_file_data = encryption.decrypt_file(encrypted_file_data, decrypted_file, key_id)
            
            # Read decrypted file
            with open(decrypted_file, 'r') as f:
                decrypted_content = f.read()
            
            print(f"File decrypted successfully")
            print(f"Decrypted content: {decrypted_content}")
        finally:
            os.unlink(decrypted_file)
    finally:
        os.unlink(temp_file)
    
    # Test key rotation
    print_subsection("Key Rotation")
    new_key_id = encryption.rotate_key(key_id)
    print(f"New key ID: {new_key_id}")
    print(f"Old key still available: {key_id in encryption.active_keys}")
    print(f"New key available: {new_key_id in encryption.active_keys}")
    
    # Get encryption statistics
    stats = encryption.get_encryption_stats()
    print_subsection("Encryption Statistics")
    print(f"Algorithm: {stats['algorithm']}")
    print(f"Key size: {stats['key_size']} bytes")
    print(f"Active keys: {stats['active_keys']}")
    print(f"Total keys: {stats['total_keys']}")
    print(f"Compression enabled: {stats['compression_enabled']}")

def demo_privacy_preserving():
    """Demo privacy-preserving techniques."""
    print_section("Privacy-Preserving Techniques Demo")
    
    # Test differential privacy
    print_subsection("Differential Privacy")
    dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
    
    # Test data
    original_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    print(f"Original data: {original_data}")
    
    # Add noise to data
    private_data = [dp.add_laplace_noise(value, sensitivity=1.0) for value in original_data]
    print(f"Private data: {[round(x, 2) for x in private_data]}")
    
    # Test private statistics
    original_sum = sum(original_data)
    private_sum = dp.private_sum(original_data, sensitivity=1.0)
    print(f"Original sum: {original_sum}")
    print(f"Private sum: {round(private_sum, 2)}")
    
    original_mean = sum(original_data) / len(original_data)
    private_mean = dp.private_mean(original_data, sensitivity=1.0)
    print(f"Original mean: {original_mean}")
    print(f"Private mean: {round(private_mean, 2)}")
    
    # Test private count
    count_query = lambda x: x > 5
    original_count = sum(1 for x in original_data if count_query(x))
    private_count = dp.private_count(original_data, count_query)
    print(f"Original count (>5): {original_count}")
    print(f"Private count (>5): {round(private_count, 2)}")
    
    # Test private histogram
    print_subsection("Private Histogram")
    categorical_data = ["A", "B", "A", "C", "B", "A", "C", "A", "B", "C"]
    bins = ["A", "B", "C"]
    
    original_hist = {bin_val: sum(1 for x in categorical_data if x == bin_val) for bin_val in bins}
    private_hist = dp.private_histogram(categorical_data, bins)
    
    print(f"Original histogram: {original_hist}")
    print(f"Private histogram: {[(k, round(v, 2)) for k, v in private_hist.items()]}")
    
    # Test data anonymization
    print_subsection("Data Anonymization")
    config = PrivacyConfig(technique=PrivacyTechnique.K_ANONYMITY, k=2)
    anonymizer = DataAnonymizer(config)
    
    # Sample dataset
    dataset = [
        {"age": "20-30", "city": "NYC", "salary": 50000, "name": "John"},
        {"age": "20-30", "city": "NYC", "salary": 55000, "name": "Jane"},
        {"age": "30-40", "city": "LA", "salary": 60000, "name": "Bob"},
        {"age": "30-40", "city": "LA", "salary": 65000, "name": "Alice"},
        {"age": "40-50", "city": "Chicago", "salary": 70000, "name": "Charlie"}
    ]
    
    print(f"Original dataset size: {len(dataset)}")
    
    # Apply k-anonymity
    quasi_identifiers = ["age", "city"]
    k_anonymous_data = anonymizer.k_anonymize(dataset, quasi_identifiers)
    print(f"K-anonymous dataset size: {len(k_anonymous_data)}")
    
    # Apply data masking
    print_subsection("Data Masking")
    masking_rules = {"name": "*", "salary": "*"}
    masked_data = anonymizer.mask_data(dataset, masking_rules)
    print(f"Masked data sample: {masked_data[0]}")
    
    # Apply pseudonymization
    print_subsection("Pseudonymization")
    pseudonymization_rules = {"name": "USER", "email": "EMAIL"}
    pseudonymized_data = anonymizer.pseudonymize_data(dataset, pseudonymization_rules)
    print(f"Pseudonymized data sample: {pseudonymized_data[0]}")
    
    # Test privacy preserver
    print_subsection("Privacy Preserver")
    config = PrivacyConfig(technique=PrivacyTechnique.DIFFERENTIAL_PRIVACY)
    preserver = PrivacyPreserver(config)
    
    numeric_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    private_data = preserver.preserve_privacy(numeric_data, sensitivity=1.0)
    print(f"Original: {numeric_data}")
    print(f"Private: {[round(x, 2) for x in private_data]}")
    
    # Get privacy statistics
    stats = preserver.get_privacy_stats()
    print_subsection("Privacy Statistics")
    print(f"Technique: {stats['technique']}")
    print(f"Epsilon: {stats['epsilon']}")
    print(f"Delta: {stats['delta']}")

def demo_compliance_management():
    """Demo compliance management."""
    print_section("Compliance Management Demo")
    
    # Initialize compliance manager
    compliance_manager = ComplianceManager()
    
    # Register data subjects
    print_subsection("GDPR Compliance")
    gdpr_subject = compliance_manager.register_data_subject(
        "user_001",
        ComplianceFramework.GDPR,
        email="user001@example.com",
        name="John Doe"
    )
    print(f"Registered GDPR subject: {gdpr_subject}")
    
    # Update consent
    compliance_manager.gdpr.update_consent(
        gdpr_subject,
        consent_given=True,
        purpose=ProcessingPurpose.CONSENT
    )
    print("Updated consent for GDPR subject")
    
    # Record processing activity
    record_id = compliance_manager.gdpr.record_processing_activity(
        gdpr_subject,
        [DataCategory.PERSONAL_DATA],
        ProcessingPurpose.CONSENT,
        "consent",
        "Data processing for consent management"
    )
    print(f"Recorded processing activity: {record_id}")
    
    # Check compliance
    violations = compliance_manager.check_compliance(ComplianceFramework.GDPR)
    print(f"GDPR compliance violations: {len(violations)}")
    
    # Generate compliance report
    gdpr_report = compliance_manager.generate_compliance_report(ComplianceFramework.GDPR)
    print(f"GDPR compliance score: {gdpr_report.compliance_score:.2f}%")
    print(f"GDPR violations: {len(gdpr_report.violations)}")
    print(f"GDPR recommendations: {gdpr_report.recommendations}")
    
    print_subsection("CCPA Compliance")
    ccpa_consumer = compliance_manager.register_data_subject(
        "consumer_001",
        ComplianceFramework.CCPA,
        email="consumer001@example.com",
        name="Jane Smith"
    )
    print(f"Registered CCPA consumer: {ccpa_consumer}")
    
    # Record data sale
    sale_id = compliance_manager.ccpa.record_data_sale(
        ccpa_consumer,
        [DataCategory.PERSONAL_DATA],
        "third_party_1",
        "marketing"
    )
    print(f"Recorded data sale: {sale_id}")
    
    # Check compliance
    violations = compliance_manager.check_compliance(ComplianceFramework.CCPA)
    print(f"CCPA compliance violations: {len(violations)}")
    
    # Generate compliance report
    ccpa_report = compliance_manager.generate_compliance_report(ComplianceFramework.CCPA)
    print(f"CCPA compliance score: {ccpa_report.compliance_score:.2f}%")
    print(f"CCPA violations: {len(ccpa_report.violations)}")
    print(f"CCPA recommendations: {ccpa_report.recommendations}")
    
    # Get compliance statistics
    stats = compliance_manager.get_compliance_stats()
    print_subsection("Compliance Statistics")
    print(f"Supported frameworks: {stats['supported_frameworks']}")
    print(f"GDPR subjects: {stats['gdpr_subjects']}")
    print(f"CCPA consumers: {stats['ccpa_consumers']}")
    print(f"Total violations: {stats['total_violations']}")

def demo_audit_logging():
    """Demo audit logging and monitoring."""
    print_section("Audit Logging & Monitoring Demo")
    
    # Initialize audit logger
    audit_logger = AuditLogger(max_events=1000, retention_days=30)
    
    # Log various events
    print_subsection("Logging Events")
    
    # Authentication events
    auth_event1 = audit_logger.log_authentication(
        "user_001",
        success=True,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0..."
    )
    print(f"Logged successful authentication: {auth_event1}")
    
    auth_event2 = audit_logger.log_authentication(
        "user_002",
        success=False,
        ip_address="192.168.1.101",
        user_agent="Mozilla/5.0..."
    )
    print(f"Logged failed authentication: {auth_event2}")
    
    # Data access events
    data_access_event = audit_logger.log_data_access(
        "user_001",
        "user_data",
        "read",
        success=True
    )
    print(f"Logged data access: {data_access_event}")
    
    # Data modification events
    data_mod_event = audit_logger.log_data_modification(
        "user_001",
        "user_data",
        "update",
        success=True
    )
    print(f"Logged data modification: {data_mod_event}")
    
    # Security events
    security_event = audit_logger.log_security_event(
        "suspicious_activity",
        AuditSeverity.HIGH,
        user_id="user_001"
    )
    print(f"Logged security event: {security_event}")
    
    # Compliance events
    compliance_event = audit_logger.log_compliance_event(
        "gdpr_violation",
        AuditSeverity.CRITICAL
    )
    print(f"Logged compliance event: {compliance_event}")
    
    # Query events
    print_subsection("Querying Events")
    
    # Get all events
    all_events = audit_logger.get_events()
    print(f"Total events logged: {len(all_events)}")
    
    # Get events by type
    auth_events = audit_logger.get_events(event_type=AuditEventType.AUTHENTICATION)
    print(f"Authentication events: {len(auth_events)}")
    
    # Get events by severity
    high_severity_events = audit_logger.get_events(severity=AuditSeverity.HIGH)
    print(f"High severity events: {len(high_severity_events)}")
    
    # Get user activity
    user_activity = audit_logger.get_user_activity("user_001", hours=24)
    print(f"User 001 activity (24h): {len(user_activity)} events")
    
    # Get security events
    security_events = audit_logger.get_security_events(hours=24)
    print(f"Security events (24h): {len(security_events)}")
    
    # Get failed authentications
    failed_auths = audit_logger.get_failed_authentications(hours=24)
    print(f"Failed authentications (24h): {len(failed_auths)}")
    
    # Export events
    print_subsection("Exporting Events")
    exported_events = audit_logger.export_events(format="dict")
    print(f"Exported {len(exported_events)} events")
    
    # Get audit statistics
    stats = audit_logger.get_audit_stats()
    print_subsection("Audit Statistics")
    print(f"Total events: {stats['total_events']}")
    print(f"Events by type: {stats['events_by_type']}")
    print(f"Events by severity: {stats['events_by_severity']}")
    print(f"Events by user: {stats['events_by_user']}")
    print(f"Events by outcome: {stats['events_by_outcome']}")
    
    # Test compliance auditor
    print_subsection("Compliance Auditing")
    auditor = ComplianceAuditor(audit_logger)
    
    # Audit data access compliance
    data_access_compliance = auditor.audit_data_access_compliance(hours=24)
    print(f"Data access compliance: {data_access_compliance}")
    
    # Audit authentication compliance
    auth_compliance = auditor.audit_authentication_compliance(hours=24)
    print(f"Authentication compliance: {auth_compliance}")
    
    # Audit security compliance
    security_compliance = auditor.audit_security_compliance(hours=24)
    print(f"Security compliance: {security_compliance}")
    
    # Generate comprehensive compliance report
    compliance_report = auditor.generate_compliance_report(hours=24)
    print(f"Overall compliance score: {compliance_report['overall_compliance_score']:.2f}%")
    print(f"Report generated at: {compliance_report['report_generated_at']}")

def demo_consent_management():
    """Demo consent management and data retention."""
    print_section("Consent Management & Data Retention Demo")
    
    # Initialize consent manager
    consent_manager = ConsentManager(default_retention_days=365)
    
    # Grant consents
    print_subsection("Granting Consents")
    
    consent1 = consent_manager.grant_consent(
        "user_001",
        [DataCategory.PERSONAL_DATA],
        [ProcessingPurpose.CONSENT],
        consent_type=ConsentType.EXPLICIT,
        expires_at=datetime.now() + timedelta(days=365),
        legal_basis="consent",
        consent_method="web_form",
        ip_address="192.168.1.100"
    )
    print(f"Granted consent 1: {consent1}")
    
    consent2 = consent_manager.grant_consent(
        "user_001",
        [DataCategory.SENSITIVE_DATA],
        [ProcessingPurpose.MARKETING],
        consent_type=ConsentType.OPT_IN,
        expires_at=datetime.now() + timedelta(days=180),
        legal_basis="consent",
        consent_method="email_opt_in"
    )
    print(f"Granted consent 2: {consent2}")
    
    consent3 = consent_manager.grant_consent(
        "user_002",
        [DataCategory.PERSONAL_DATA, DataCategory.LOCATION_DATA],
        [ProcessingPurpose.ANALYTICS],
        consent_type=ConsentType.GRANULAR,
        expires_at=datetime.now() + timedelta(days=90),
        legal_basis="legitimate_interests"
    )
    print(f"Granted consent 3: {consent3}")
    
    # Check consents
    print_subsection("Checking Consents")
    
    has_consent1 = consent_manager.check_consent(
        "user_001",
        DataCategory.PERSONAL_DATA,
        ProcessingPurpose.CONSENT
    )
    print(f"User 001 has consent for personal data: {has_consent1}")
    
    has_consent2 = consent_manager.check_consent(
        "user_001",
        DataCategory.SENSITIVE_DATA,
        ProcessingPurpose.MARKETING
    )
    print(f"User 001 has consent for sensitive data marketing: {has_consent2}")
    
    has_consent3 = consent_manager.check_consent(
        "user_002",
        DataCategory.LOCATION_DATA,
        ProcessingPurpose.ANALYTICS
    )
    print(f"User 002 has consent for location data analytics: {has_consent3}")
    
    # Get consent records
    print_subsection("Retrieving Consent Records")
    
    user1_consents = consent_manager.get_consent_records(subject_id="user_001")
    print(f"User 001 consents: {len(user1_consents)}")
    
    personal_data_consents = consent_manager.get_consent_records(
        data_category=DataCategory.PERSONAL_DATA
    )
    print(f"Personal data consents: {len(personal_data_consents)}")
    
    valid_consents = consent_manager.get_consent_records(valid_only=True)
    print(f"Valid consents: {len(valid_consents)}")
    
    # Get consent summary
    print_subsection("Consent Summary")
    summary = consent_manager.get_subject_consent_summary("user_001")
    print(f"User 001 summary: {json.dumps(summary, indent=2)}")
    
    # Withdraw consent
    print_subsection("Withdrawing Consent")
    withdrawal_success = consent_manager.withdraw_consent(
        consent2,
        reason="User requested opt-out"
    )
    print(f"Consent withdrawal successful: {withdrawal_success}")
    
    # Check consent after withdrawal
    has_consent_after_withdrawal = consent_manager.check_consent(
        "user_001",
        DataCategory.SENSITIVE_DATA,
        ProcessingPurpose.MARKETING
    )
    print(f"User 001 has consent for sensitive data marketing after withdrawal: {has_consent_after_withdrawal}")
    
    # Create retention policies
    print_subsection("Data Retention Policies")
    
    policy1 = consent_manager.create_retention_policy(
        DataCategory.PERSONAL_DATA,
        ProcessingPurpose.CONSENT,
        timedelta(days=365),
        auto_delete=True,
        description="Personal data retention for consent management"
    )
    print(f"Created retention policy 1: {policy1}")
    
    policy2 = consent_manager.create_retention_policy(
        DataCategory.SENSITIVE_DATA,
        ProcessingPurpose.MARKETING,
        timedelta(days=180),
        auto_delete=True,
        description="Sensitive data retention for marketing"
    )
    print(f"Created retention policy 2: {policy2}")
    
    # Get retention policy
    retention_policy = consent_manager.get_retention_policy(
        DataCategory.PERSONAL_DATA,
        ProcessingPurpose.CONSENT
    )
    if retention_policy:
        print(f"Retention policy for personal data: {retention_policy.retention_period.days} days")
    
    # Test data retention manager
    print_subsection("Data Retention Management")
    retention_manager = DataRetentionManager(consent_manager)
    
    # Get retention deadline
    deadline = retention_manager.get_retention_deadline(
        "user_001",
        DataCategory.PERSONAL_DATA,
        ProcessingPurpose.CONSENT
    )
    if deadline:
        print(f"Retention deadline for user_001 personal data: {deadline}")
    
    # Get data for deletion
    deletion_records = retention_manager.get_data_for_deletion()
    print(f"Data records for deletion: {len(deletion_records)}")
    
    # Cleanup expired data
    cleanup_count = retention_manager.cleanup_expired_data()
    print(f"Cleaned up {cleanup_count} expired data records")
    
    # Export consent data
    print_subsection("Exporting Consent Data")
    export_data = consent_manager.export_consent_data("user_001")
    print(f"Exported consent data for user_001: {len(export_data['consent_records'])} records")
    
    # Get consent statistics
    stats = consent_manager.get_consent_stats()
    print_subsection("Consent Statistics")
    print(f"Total consents: {stats['total_consents']}")
    print(f"Active consents: {stats['active_consents']}")
    print(f"Withdrawn consents: {stats['withdrawn_consents']}")
    print(f"Expired consents: {stats['expired_consents']}")
    print(f"Retention policies: {stats['retention_policies']}")
    print(f"Unique subjects: {stats['unique_subjects']}")
    print(f"Consent types: {stats['consent_types']}")

def demo_integration():
    """Demo integration of all security features."""
    print_section("Security Features Integration Demo")
    
    # Initialize all components
    pii_detector = AdvancedPIIDetector(use_spacy=False, use_presidio=False)
    encryption = DataEncryption()
    privacy_preserver = PrivacyPreserver(PrivacyConfig(technique=PrivacyTechnique.DIFFERENTIAL_PRIVACY))
    compliance_manager = ComplianceManager()
    audit_logger = AuditLogger()
    consent_manager = ConsentManager()
    
    print_subsection("End-to-End Security Pipeline")
    
    # 1. Detect and redact PII
    sensitive_text = "User John Doe (john.doe@example.com) has SSN 123-45-6789"
    pii_result = pii_detector.detect_pii(sensitive_text)
    print(f"1. PII Detection: {len(pii_result.detected_pii)} entities detected")
    
    # 2. Encrypt the redacted text
    key_id = encryption.generate_key()
    encrypted_data = encryption.encrypt_data(pii_result.redacted_text, key_id)
    print(f"2. Data Encryption: Text encrypted with key {key_id}")
    
    # 3. Apply privacy-preserving techniques
    numeric_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    private_data = privacy_preserver.preserve_privacy(numeric_data, sensitivity=1.0)
    print(f"3. Privacy Preservation: Applied differential privacy to {len(numeric_data)} values")
    
    # 4. Register data subject and grant consent
    subject_id = compliance_manager.register_data_subject(
        "user_001",
        ComplianceFramework.GDPR,
        email="user001@example.com"
    )
    consent_id = consent_manager.grant_consent(
        "user_001",
        [DataCategory.PERSONAL_DATA],
        [ProcessingPurpose.CONSENT]
    )
    print(f"4. Compliance & Consent: Registered subject {subject_id} with consent {consent_id}")
    
    # 5. Log all activities
    audit_logger.log_authentication("user_001", success=True)
    audit_logger.log_data_access("user_001", "sensitive_data", "read", success=True)
    audit_logger.log_security_event("pii_processing", AuditSeverity.MEDIUM)
    audit_logger.log_compliance_event("consent_granted", AuditSeverity.LOW)
    print(f"5. Audit Logging: Logged 4 security events")
    
    # 6. Check compliance
    violations = compliance_manager.check_compliance(ComplianceFramework.GDPR)
    print(f"6. Compliance Check: {len(violations)} violations found")
    
    # 7. Generate comprehensive report
    compliance_report = compliance_manager.generate_compliance_report(ComplianceFramework.GDPR)
    audit_stats = audit_logger.get_audit_stats()
    consent_stats = consent_manager.get_consent_stats()
    
    print_subsection("Comprehensive Security Report")
    print(f"GDPR Compliance Score: {compliance_report.compliance_score:.2f}%")
    print(f"Total Audit Events: {audit_stats['total_events']}")
    print(f"Active Consents: {consent_stats['active_consents']}")
    print(f"Security Status: {'SECURE' if len(violations) == 0 else 'ATTENTION REQUIRED'}")

def main():
    """Run the security demo."""
    print("Security & Privacy Features Demo")
    print("This demo showcases comprehensive security and privacy capabilities")
    
    try:
        # Run all demos
        demo_pii_detection()
        demo_data_encryption()
        demo_privacy_preserving()
        demo_compliance_management()
        demo_audit_logging()
        demo_consent_management()
        demo_integration()
        
        print_section("Demo Complete")
        print("All security and privacy features have been demonstrated successfully!")
        print("Key features showcased:")
        print("- Advanced PII detection and redaction")
        print("- Data encryption and secure storage")
        print("- Privacy-preserving techniques (differential privacy, anonymization)")
        print("- Compliance management (GDPR, CCPA)")
        print("- Comprehensive audit logging and monitoring")
        print("- Consent management and data retention")
        print("- End-to-end security pipeline integration")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
