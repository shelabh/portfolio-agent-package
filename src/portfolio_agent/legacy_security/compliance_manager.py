"""
Compliance Management

This module provides compliance frameworks for GDPR, CCPA, and other regulations
with automated compliance checking and reporting.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"

class DataCategory(Enum):
    """Data categories for compliance."""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    FINANCIAL_DATA = "financial_data"
    HEALTH_DATA = "health_data"
    BIOMETRIC_DATA = "biometric_data"
    LOCATION_DATA = "location_data"
    BEHAVIORAL_DATA = "behavioral_data"
    COMMUNICATION_DATA = "communication_data"

class ProcessingPurpose(Enum):
    """Data processing purposes."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PERSONALIZATION = "personalization"
    SECURITY = "security"

@dataclass
class DataSubject:
    """Data subject information."""
    subject_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    data_categories: Set[DataCategory] = field(default_factory=set)
    processing_purposes: Set[ProcessingPurpose] = field(default_factory=set)
    consent_given: bool = False
    consent_date: Optional[datetime] = None
    data_retention_period: Optional[timedelta] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ComplianceViolation:
    """Compliance violation record."""
    violation_id: str
    framework: ComplianceFramework
    violation_type: str
    severity: str  # low, medium, high, critical
    description: str
    affected_data: List[str]
    detected_at: datetime
    resolved: bool = False
    resolution_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None

@dataclass
class ComplianceReport:
    """Compliance report."""
    report_id: str
    framework: ComplianceFramework
    generated_at: datetime
    compliance_score: float
    violations: List[ComplianceViolation]
    recommendations: List[str]
    data_subjects_count: int
    data_categories_count: int
    processing_purposes_count: int

class GDPRCompliance:
    """GDPR compliance manager."""
    
    def __init__(self):
        """Initialize GDPR compliance manager."""
        self.data_subjects: Dict[str, DataSubject] = {}
        self.violations: List[ComplianceViolation] = []
        self.processing_records: List[Dict[str, Any]] = []
        
        logger.info("GDPR compliance manager initialized")
    
    def register_data_subject(self, subject: DataSubject) -> str:
        """Register a data subject.
        
        Args:
            subject: Data subject information
            
        Returns:
            Subject ID
        """
        self.data_subjects[subject.subject_id] = subject
        logger.info(f"Registered data subject: {subject.subject_id}")
        return subject.subject_id
    
    def update_consent(self, subject_id: str, consent_given: bool, purpose: ProcessingPurpose) -> bool:
        """Update consent for a data subject.
        
        Args:
            subject_id: Data subject ID
            consent_given: Whether consent is given
            purpose: Processing purpose
            
        Returns:
            Success status
        """
        if subject_id not in self.data_subjects:
            return False
        
        subject = self.data_subjects[subject_id]
        subject.consent_given = consent_given
        subject.consent_date = datetime.now()
        subject.processing_purposes.add(purpose)
        subject.updated_at = datetime.now()
        
        logger.info(f"Updated consent for subject {subject_id}: {consent_given}")
        return True
    
    def record_processing_activity(
        self,
        subject_id: str,
        data_categories: List[DataCategory],
        purpose: ProcessingPurpose,
        legal_basis: str,
        description: str
    ) -> str:
        """Record data processing activity.
        
        Args:
            subject_id: Data subject ID
            data_categories: Data categories processed
            purpose: Processing purpose
            legal_basis: Legal basis for processing
            description: Description of processing
            
        Returns:
            Processing record ID
        """
        record_id = hashlib.md5(f"{subject_id}_{datetime.now()}".encode()).hexdigest()
        
        record = {
            "record_id": record_id,
            "subject_id": subject_id,
            "data_categories": [cat.value for cat in data_categories],
            "purpose": purpose.value,
            "legal_basis": legal_basis,
            "description": description,
            "processed_at": datetime.now().isoformat()
        }
        
        self.processing_records.append(record)
        
        # Update subject's data categories
        if subject_id in self.data_subjects:
            subject = self.data_subjects[subject_id]
            subject.data_categories.update(data_categories)
            subject.updated_at = datetime.now()
        
        logger.info(f"Recorded processing activity: {record_id}")
        return record_id
    
    def check_consent_compliance(self) -> List[ComplianceViolation]:
        """Check consent compliance."""
        violations = []
        
        for subject_id, subject in self.data_subjects.items():
            # Check if consent is required but not given
            if subject.processing_purposes and not subject.consent_given:
                violation = ComplianceViolation(
                    violation_id=hashlib.md5(f"consent_{subject_id}".encode()).hexdigest(),
                    framework=ComplianceFramework.GDPR,
                    violation_type="missing_consent",
                    severity="high",
                    description=f"Data subject {subject_id} has no consent for processing",
                    affected_data=[subject_id],
                    detected_at=datetime.now()
                )
                violations.append(violation)
            
            # Check if consent is expired
            if (subject.consent_given and subject.consent_date and 
                datetime.now() - subject.consent_date > timedelta(days=365)):
                violation = ComplianceViolation(
                    violation_id=hashlib.md5(f"expired_consent_{subject_id}".encode()).hexdigest(),
                    framework=ComplianceFramework.GDPR,
                    violation_type="expired_consent",
                    severity="medium",
                    description=f"Data subject {subject_id} consent is expired",
                    affected_data=[subject_id],
                    detected_at=datetime.now()
                )
                violations.append(violation)
        
        self.violations.extend(violations)
        return violations
    
    def check_data_retention_compliance(self) -> List[ComplianceViolation]:
        """Check data retention compliance."""
        violations = []
        
        for subject_id, subject in self.data_subjects.items():
            if subject.data_retention_period:
                retention_deadline = subject.created_at + subject.data_retention_period
                if datetime.now() > retention_deadline:
                    violation = ComplianceViolation(
                        violation_id=hashlib.md5(f"retention_{subject_id}".encode()).hexdigest(),
                        framework=ComplianceFramework.GDPR,
                        violation_type="data_retention_violation",
                        severity="high",
                        description=f"Data for subject {subject_id} should be deleted",
                        affected_data=[subject_id],
                        detected_at=datetime.now()
                    )
                    violations.append(violation)
        
        self.violations.extend(violations)
        return violations
    
    def generate_compliance_report(self) -> ComplianceReport:
        """Generate GDPR compliance report."""
        # Check for violations
        consent_violations = self.check_consent_compliance()
        retention_violations = self.check_data_retention_compliance()
        
        all_violations = consent_violations + retention_violations
        
        # Calculate compliance score
        total_checks = len(self.data_subjects) * 2  # consent + retention
        violations_count = len(all_violations)
        compliance_score = max(0, (total_checks - violations_count) / total_checks * 100) if total_checks > 0 else 100
        
        # Generate recommendations
        recommendations = []
        if consent_violations:
            recommendations.append("Review and update consent mechanisms")
        if retention_violations:
            recommendations.append("Implement automated data deletion processes")
        if compliance_score < 80:
            recommendations.append("Conduct comprehensive compliance audit")
        
        report = ComplianceReport(
            report_id=hashlib.md5(f"gdpr_report_{datetime.now()}".encode()).hexdigest(),
            framework=ComplianceFramework.GDPR,
            generated_at=datetime.now(),
            compliance_score=compliance_score,
            violations=all_violations,
            recommendations=recommendations,
            data_subjects_count=len(self.data_subjects),
            data_categories_count=len(set(cat for subject in self.data_subjects.values() for cat in subject.data_categories)),
            processing_purposes_count=len(set(purpose for subject in self.data_subjects.values() for purpose in subject.processing_purposes))
        )
        
        logger.info(f"Generated GDPR compliance report: {report.report_id}")
        return report

class CCPACompliance:
    """CCPA compliance manager."""
    
    def __init__(self):
        """Initialize CCPA compliance manager."""
        self.consumers: Dict[str, DataSubject] = {}
        self.violations: List[ComplianceViolation] = []
        self.data_sales: List[Dict[str, Any]] = []
        
        logger.info("CCPA compliance manager initialized")
    
    def register_consumer(self, consumer: DataSubject) -> str:
        """Register a consumer.
        
        Args:
            consumer: Consumer information
            
        Returns:
            Consumer ID
        """
        self.consumers[consumer.subject_id] = consumer
        logger.info(f"Registered consumer: {consumer.subject_id}")
        return consumer.subject_id
    
    def record_data_sale(
        self,
        consumer_id: str,
        data_categories: List[DataCategory],
        third_party: str,
        purpose: str
    ) -> str:
        """Record data sale to third party.
        
        Args:
            consumer_id: Consumer ID
            data_categories: Data categories sold
            third_party: Third party identifier
            purpose: Purpose of sale
            
        Returns:
            Sale record ID
        """
        sale_id = hashlib.md5(f"{consumer_id}_{third_party}_{datetime.now()}".encode()).hexdigest()
        
        sale_record = {
            "sale_id": sale_id,
            "consumer_id": consumer_id,
            "data_categories": [cat.value for cat in data_categories],
            "third_party": third_party,
            "purpose": purpose,
            "sold_at": datetime.now().isoformat()
        }
        
        self.data_sales.append(sale_record)
        
        # Update consumer's data categories
        if consumer_id in self.consumers:
            consumer = self.consumers[consumer_id]
            consumer.data_categories.update(data_categories)
            consumer.updated_at = datetime.now()
        
        logger.info(f"Recorded data sale: {sale_id}")
        return sale_id
    
    def check_opt_out_compliance(self) -> List[ComplianceViolation]:
        """Check opt-out compliance."""
        violations = []
        
        for consumer_id, consumer in self.consumers.items():
            # Check if consumer has opted out but data is still being sold
            if not consumer.consent_given and consumer_id in [sale["consumer_id"] for sale in self.data_sales]:
                violation = ComplianceViolation(
                    violation_id=hashlib.md5(f"opt_out_{consumer_id}".encode()).hexdigest(),
                    framework=ComplianceFramework.CCPA,
                    violation_type="opt_out_violation",
                    severity="high",
                    description=f"Consumer {consumer_id} has opted out but data is still being sold",
                    affected_data=[consumer_id],
                    detected_at=datetime.now()
                )
                violations.append(violation)
        
        self.violations.extend(violations)
        return violations
    
    def check_disclosure_compliance(self) -> List[ComplianceViolation]:
        """Check disclosure compliance."""
        violations = []
        
        for consumer_id, consumer in self.consumers.items():
            # Check if consumer has requested disclosure but not provided
            if consumer.data_categories and not consumer.consent_given:
                violation = ComplianceViolation(
                    violation_id=hashlib.md5(f"disclosure_{consumer_id}".encode()).hexdigest(),
                    framework=ComplianceFramework.CCPA,
                    violation_type="disclosure_violation",
                    severity="medium",
                    description=f"Consumer {consumer_id} has not been provided with data disclosure",
                    affected_data=[consumer_id],
                    detected_at=datetime.now()
                )
                violations.append(violation)
        
        self.violations.extend(violations)
        return violations
    
    def generate_compliance_report(self) -> ComplianceReport:
        """Generate CCPA compliance report."""
        # Check for violations
        opt_out_violations = self.check_opt_out_compliance()
        disclosure_violations = self.check_disclosure_compliance()
        
        all_violations = opt_out_violations + disclosure_violations
        
        # Calculate compliance score
        total_checks = len(self.consumers) * 2  # opt-out + disclosure
        violations_count = len(all_violations)
        compliance_score = max(0, (total_checks - violations_count) / total_checks * 100) if total_checks > 0 else 100
        
        # Generate recommendations
        recommendations = []
        if opt_out_violations:
            recommendations.append("Implement automated opt-out mechanisms")
        if disclosure_violations:
            recommendations.append("Provide data disclosure to consumers")
        if compliance_score < 80:
            recommendations.append("Conduct comprehensive CCPA audit")
        
        report = ComplianceReport(
            report_id=hashlib.md5(f"ccpa_report_{datetime.now()}".encode()).hexdigest(),
            framework=ComplianceFramework.CCPA,
            generated_at=datetime.now(),
            compliance_score=compliance_score,
            violations=all_violations,
            recommendations=recommendations,
            data_subjects_count=len(self.consumers),
            data_categories_count=len(set(cat for consumer in self.consumers.values() for cat in consumer.data_categories)),
            processing_purposes_count=len(set(purpose for consumer in self.consumers.values() for purpose in consumer.processing_purposes))
        )
        
        logger.info(f"Generated CCPA compliance report: {report.report_id}")
        return report

class ComplianceManager:
    """Main compliance manager."""
    
    def __init__(self):
        """Initialize compliance manager."""
        self.gdpr = GDPRCompliance()
        self.ccpa = CCPACompliance()
        self.frameworks: Dict[ComplianceFramework, Any] = {
            ComplianceFramework.GDPR: self.gdpr,
            ComplianceFramework.CCPA: self.ccpa
        }
        
        logger.info("Compliance manager initialized")
    
    def register_data_subject(
        self,
        subject_id: str,
        framework: ComplianceFramework,
        **kwargs
    ) -> str:
        """Register a data subject for compliance.
        
        Args:
            subject_id: Data subject ID
            framework: Compliance framework
            **kwargs: Additional subject information
            
        Returns:
            Subject ID
        """
        subject = DataSubject(subject_id=subject_id, **kwargs)
        
        if framework == ComplianceFramework.GDPR:
            return self.gdpr.register_data_subject(subject)
        elif framework == ComplianceFramework.CCPA:
            return self.ccpa.register_consumer(subject)
        else:
            raise ValueError(f"Unsupported framework: {framework}")
    
    def check_compliance(self, framework: ComplianceFramework) -> List[ComplianceViolation]:
        """Check compliance for a framework.
        
        Args:
            framework: Compliance framework
            
        Returns:
            List of violations
        """
        if framework not in self.frameworks:
            raise ValueError(f"Unsupported framework: {framework}")
        
        compliance_manager = self.frameworks[framework]
        
        if framework == ComplianceFramework.GDPR:
            return compliance_manager.check_consent_compliance() + compliance_manager.check_data_retention_compliance()
        elif framework == ComplianceFramework.CCPA:
            return compliance_manager.check_opt_out_compliance() + compliance_manager.check_disclosure_compliance()
        else:
            return []
    
    def generate_compliance_report(self, framework: ComplianceFramework) -> ComplianceReport:
        """Generate compliance report for a framework.
        
        Args:
            framework: Compliance framework
            
        Returns:
            Compliance report
        """
        if framework not in self.frameworks:
            raise ValueError(f"Unsupported framework: {framework}")
        
        compliance_manager = self.frameworks[framework]
        return compliance_manager.generate_compliance_report()
    
    def get_compliance_stats(self) -> Dict[str, Any]:
        """Get compliance statistics."""
        return {
            "supported_frameworks": [f.value for f in self.frameworks.keys()],
            "gdpr_subjects": len(self.gdpr.data_subjects),
            "ccpa_consumers": len(self.ccpa.consumers),
            "total_violations": len(self.gdpr.violations) + len(self.ccpa.violations)
        }

# Convenience functions
def create_compliance_manager() -> ComplianceManager:
    """Create a compliance manager instance."""
    return ComplianceManager()

def check_gdpr_compliance(compliance_manager: ComplianceManager) -> ComplianceReport:
    """Convenience function to check GDPR compliance."""
    return compliance_manager.generate_compliance_report(ComplianceFramework.GDPR)

def check_ccpa_compliance(compliance_manager: ComplianceManager) -> ComplianceReport:
    """Convenience function to check CCPA compliance."""
    return compliance_manager.generate_compliance_report(ComplianceFramework.CCPA)
