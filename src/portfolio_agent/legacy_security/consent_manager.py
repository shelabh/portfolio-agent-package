"""
Consent Management

This module provides consent management and data retention capabilities
for GDPR, CCPA, and other privacy regulations.
"""

import logging
import json
import hashlib
from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

class ConsentType(Enum):
    """Types of consent."""
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    OPT_IN = "opt_in"
    OPT_OUT = "opt_out"
    GRANULAR = "granular"
    WITHDRAWN = "withdrawn"

class DataCategory(Enum):
    """Data categories for consent."""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    FINANCIAL_DATA = "financial_data"
    HEALTH_DATA = "health_data"
    BIOMETRIC_DATA = "biometric_data"
    LOCATION_DATA = "location_data"
    BEHAVIORAL_DATA = "behavioral_data"
    COMMUNICATION_DATA = "communication_data"
    MARKETING_DATA = "marketing_data"
    ANALYTICS_DATA = "analytics_data"

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
class ConsentRecord:
    """Consent record."""
    consent_id: str
    subject_id: str
    consent_type: ConsentType
    data_categories: Set[DataCategory]
    processing_purposes: Set[ProcessingPurpose]
    granted: bool
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    legal_basis: Optional[str] = None
    consent_method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def is_valid(self) -> bool:
        """Check if consent is valid."""
        if not self.granted:
            return False
        
        if self.withdrawn_at:
            return False
        
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if consent is expired."""
        return self.expires_at and datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert consent record to dictionary."""
        return {
            "consent_id": self.consent_id,
            "subject_id": self.subject_id,
            "consent_type": self.consent_type.value,
            "data_categories": [cat.value for cat in self.data_categories],
            "processing_purposes": [purpose.value for purpose in self.processing_purposes],
            "granted": self.granted,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "withdrawn_at": self.withdrawn_at.isoformat() if self.withdrawn_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "legal_basis": self.legal_basis,
            "consent_method": self.consent_method,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConsentRecord':
        """Create consent record from dictionary."""
        return cls(
            consent_id=data["consent_id"],
            subject_id=data["subject_id"],
            consent_type=ConsentType(data["consent_type"]),
            data_categories=set(DataCategory(cat) for cat in data["data_categories"]),
            processing_purposes=set(ProcessingPurpose(purpose) for purpose in data["processing_purposes"]),
            granted=data["granted"],
            granted_at=datetime.fromisoformat(data["granted_at"]) if data.get("granted_at") else None,
            withdrawn_at=datetime.fromisoformat(data["withdrawn_at"]) if data.get("withdrawn_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            legal_basis=data.get("legal_basis"),
            consent_method=data.get("consent_method"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

@dataclass
class DataRetentionPolicy:
    """Data retention policy."""
    policy_id: str
    data_category: DataCategory
    processing_purpose: ProcessingPurpose
    retention_period: timedelta
    auto_delete: bool = True
    legal_hold: bool = False
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class ConsentManager:
    """Consent management system."""
    
    def __init__(self, default_retention_days: int = 365):
        """Initialize consent manager.
        
        Args:
            default_retention_days: Default data retention period in days
        """
        self.default_retention_days = default_retention_days
        
        # Storage
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.retention_policies: Dict[str, DataRetentionPolicy] = {}
        
        # Indexes for efficient querying
        self.consent_by_subject: Dict[str, Set[str]] = defaultdict(set)
        self.consent_by_category: Dict[DataCategory, Set[str]] = defaultdict(set)
        self.consent_by_purpose: Dict[ProcessingPurpose, Set[str]] = defaultdict(set)
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info("Consent manager initialized")
    
    def grant_consent(
        self,
        subject_id: str,
        data_categories: List[DataCategory],
        processing_purposes: List[ProcessingPurpose],
        consent_type: ConsentType = ConsentType.EXPLICIT,
        expires_at: Optional[datetime] = None,
        legal_basis: Optional[str] = None,
        consent_method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Grant consent for data processing.
        
        Args:
            subject_id: Data subject ID
            data_categories: Data categories to process
            processing_purposes: Processing purposes
            consent_type: Type of consent
            expires_at: Consent expiration date
            legal_basis: Legal basis for processing
            consent_method: Method of consent collection
            ip_address: IP address of consent
            user_agent: User agent string
            metadata: Additional metadata
            
        Returns:
            Consent ID
        """
        with self._lock:
            # Generate consent ID
            consent_id = self._generate_consent_id(subject_id, data_categories, processing_purposes)
            
            # Create consent record
            consent_record = ConsentRecord(
                consent_id=consent_id,
                subject_id=subject_id,
                consent_type=consent_type,
                data_categories=set(data_categories),
                processing_purposes=set(processing_purposes),
                granted=True,
                granted_at=datetime.now(),
                expires_at=expires_at,
                legal_basis=legal_basis,
                consent_method=consent_method,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            # Store consent record
            self.consent_records[consent_id] = consent_record
            
            # Update indexes
            self._update_indexes(consent_record)
            
            logger.info(f"Granted consent: {consent_id} for subject: {subject_id}")
            return consent_id
    
    def withdraw_consent(
        self,
        consent_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Withdraw consent.
        
        Args:
            consent_id: Consent ID to withdraw
            reason: Reason for withdrawal
            
        Returns:
            Success status
        """
        with self._lock:
            if consent_id not in self.consent_records:
                return False
            
            consent_record = self.consent_records[consent_id]
            consent_record.granted = False
            consent_record.withdrawn_at = datetime.now()
            consent_record.updated_at = datetime.now()
            
            if reason:
                consent_record.metadata["withdrawal_reason"] = reason
            
            logger.info(f"Withdrawn consent: {consent_id}")
            return True
    
    def check_consent(
        self,
        subject_id: str,
        data_category: DataCategory,
        processing_purpose: ProcessingPurpose
    ) -> bool:
        """Check if consent exists for data processing.
        
        Args:
            subject_id: Data subject ID
            data_category: Data category
            processing_purpose: Processing purpose
            
        Returns:
            Consent status
        """
        with self._lock:
            # Get consent records for subject
            subject_consents = self.consent_by_subject.get(subject_id, set())
            
            for consent_id in subject_consents:
                consent_record = self.consent_records[consent_id]
                
                # Check if consent is valid
                if not consent_record.is_valid():
                    continue
                
                # Check if consent covers the requested category and purpose
                if (data_category in consent_record.data_categories and 
                    processing_purpose in consent_record.processing_purposes):
                    return True
            
            return False
    
    def get_consent_records(
        self,
        subject_id: Optional[str] = None,
        data_category: Optional[DataCategory] = None,
        processing_purpose: Optional[ProcessingPurpose] = None,
        valid_only: bool = True
    ) -> List[ConsentRecord]:
        """Get consent records with filters.
        
        Args:
            subject_id: Filter by subject ID
            data_category: Filter by data category
            processing_purpose: Filter by processing purpose
            valid_only: Return only valid consents
            
        Returns:
            List of consent records
        """
        with self._lock:
            return self._get_consent_records_unlocked(
                subject_id, data_category, processing_purpose, valid_only
            )
    
    def _get_consent_records_unlocked(
        self,
        subject_id: Optional[str] = None,
        data_category: Optional[DataCategory] = None,
        processing_purpose: Optional[ProcessingPurpose] = None,
        valid_only: bool = True
    ) -> List[ConsentRecord]:
        """Get consent records with filters (without acquiring lock).
        
        Args:
            subject_id: Filter by subject ID
            data_category: Filter by data category
            processing_purpose: Filter by processing purpose
            valid_only: Return only valid consents
            
        Returns:
            List of consent records
        """
        filtered_records = []
        
        for consent_record in self.consent_records.values():
            # Apply filters
            if subject_id and consent_record.subject_id != subject_id:
                continue
            if data_category and data_category not in consent_record.data_categories:
                continue
            if processing_purpose and processing_purpose not in consent_record.processing_purposes:
                continue
            if valid_only and not consent_record.is_valid():
                continue
            
            filtered_records.append(consent_record)
        
        return filtered_records
    
    def get_subject_consent_summary(self, subject_id: str) -> Dict[str, Any]:
        """Get consent summary for a subject.
        
        Args:
            subject_id: Data subject ID
            
        Returns:
            Consent summary
        """
        with self._lock:
            consent_records = self._get_consent_records_unlocked(subject_id=subject_id, valid_only=False)
            
            summary = {
                "subject_id": subject_id,
                "total_consents": len(consent_records),
                "active_consents": len([r for r in consent_records if r.is_valid()]),
                "withdrawn_consents": len([r for r in consent_records if r.withdrawn_at]),
                "expired_consents": len([r for r in consent_records if r.is_expired()]),
                "data_categories": set(),
                "processing_purposes": set(),
                "consent_types": set(),
                "latest_consent": None,
                "latest_withdrawal": None
            }
            
            for record in consent_records:
                summary["data_categories"].update(record.data_categories)
                summary["processing_purposes"].update(record.processing_purposes)
                summary["consent_types"].add(record.consent_type)
                
                if record.granted_at and (not summary["latest_consent"] or record.granted_at > summary["latest_consent"]):
                    summary["latest_consent"] = record.granted_at
                
                if record.withdrawn_at and (not summary["latest_withdrawal"] or record.withdrawn_at > summary["latest_withdrawal"]):
                    summary["latest_withdrawal"] = record.withdrawn_at
            
            # Convert sets to lists for JSON serialization
            summary["data_categories"] = [cat.value for cat in summary["data_categories"]]
            summary["processing_purposes"] = [purpose.value for purpose in summary["processing_purposes"]]
            summary["consent_types"] = [consent_type.value for consent_type in summary["consent_types"]]
            
            # Convert datetime objects to ISO format
            if summary["latest_consent"]:
                summary["latest_consent"] = summary["latest_consent"].isoformat()
            if summary["latest_withdrawal"]:
                summary["latest_withdrawal"] = summary["latest_withdrawal"].isoformat()
            
            return summary
    
    def create_retention_policy(
        self,
        data_category: DataCategory,
        processing_purpose: ProcessingPurpose,
        retention_period: timedelta,
        auto_delete: bool = True,
        legal_hold: bool = False,
        description: Optional[str] = None
    ) -> str:
        """Create data retention policy.
        
        Args:
            data_category: Data category
            processing_purpose: Processing purpose
            retention_period: Retention period
            auto_delete: Whether to auto-delete after retention period
            legal_hold: Whether data is under legal hold
            description: Policy description
            
        Returns:
            Policy ID
        """
        with self._lock:
            policy_id = self._generate_policy_id(data_category, processing_purpose)
            
            policy = DataRetentionPolicy(
                policy_id=policy_id,
                data_category=data_category,
                processing_purpose=processing_purpose,
                retention_period=retention_period,
                auto_delete=auto_delete,
                legal_hold=legal_hold,
                description=description
            )
            
            self.retention_policies[policy_id] = policy
            
            logger.info(f"Created retention policy: {policy_id}")
            return policy_id
    
    def get_retention_policy(
        self,
        data_category: DataCategory,
        processing_purpose: ProcessingPurpose
    ) -> Optional[DataRetentionPolicy]:
        """Get retention policy for data category and purpose.
        
        Args:
            data_category: Data category
            processing_purpose: Processing purpose
            
        Returns:
            Retention policy or None
        """
        with self._lock:
            for policy in self.retention_policies.values():
                if (policy.data_category == data_category and 
                    policy.processing_purpose == processing_purpose):
                    return policy
            
            return None
    
    def get_expired_consents(self) -> List[ConsentRecord]:
        """Get expired consent records.
        
        Returns:
            List of expired consent records
        """
        with self._lock:
            expired_consents = []
            
            for consent_record in self.consent_records.values():
                if consent_record.is_expired():
                    expired_consents.append(consent_record)
            
            return expired_consents
    
    def cleanup_expired_consents(self) -> int:
        """Clean up expired consent records.
        
        Returns:
            Number of cleaned up records
        """
        with self._lock:
            expired_consents = self.get_expired_consents()
            
            for consent_record in expired_consents:
                # Remove from indexes
                self._remove_from_indexes(consent_record)
                
                # Remove from storage
                del self.consent_records[consent_record.consent_id]
            
            logger.info(f"Cleaned up {len(expired_consents)} expired consent records")
            return len(expired_consents)
    
    def export_consent_data(self, subject_id: Optional[str] = None) -> Dict[str, Any]:
        """Export consent data for a subject.
        
        Args:
            subject_id: Data subject ID (exports all if None)
            
        Returns:
            Exported consent data
        """
        with self._lock:
            if subject_id:
                consent_records = self.get_consent_records(subject_id=subject_id, valid_only=False)
            else:
                consent_records = list(self.consent_records.values())
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "subject_id": subject_id,
                "consent_records": [record.to_dict() for record in consent_records],
                "retention_policies": [
                    {
                        "policy_id": policy.policy_id,
                        "data_category": policy.data_category.value,
                        "processing_purpose": policy.processing_purpose.value,
                        "retention_period_days": policy.retention_period.days,
                        "auto_delete": policy.auto_delete,
                        "legal_hold": policy.legal_hold,
                        "description": policy.description
                    }
                    for policy in self.retention_policies.values()
                ]
            }
            
            return export_data
    
    def get_consent_stats(self) -> Dict[str, Any]:
        """Get consent management statistics."""
        with self._lock:
            total_consents = len(self.consent_records)
            active_consents = len([r for r in self.consent_records.values() if r.is_valid()])
            withdrawn_consents = len([r for r in self.consent_records.values() if r.withdrawn_at])
            expired_consents = len([r for r in self.consent_records.values() if r.is_expired()])
            
            return {
                "total_consents": total_consents,
                "active_consents": active_consents,
                "withdrawn_consents": withdrawn_consents,
                "expired_consents": expired_consents,
                "retention_policies": len(self.retention_policies),
                "unique_subjects": len(self.consent_by_subject),
                "consent_types": {
                    consent_type.value: len([r for r in self.consent_records.values() if r.consent_type == consent_type])
                    for consent_type in ConsentType
                }
            }
    
    def _generate_consent_id(self, subject_id: str, data_categories: List[DataCategory], processing_purposes: List[ProcessingPurpose]) -> str:
        """Generate unique consent ID."""
        timestamp = datetime.now().isoformat()
        content = f"{subject_id}_{data_categories}_{processing_purposes}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _generate_policy_id(self, data_category: DataCategory, processing_purpose: ProcessingPurpose) -> str:
        """Generate unique policy ID."""
        content = f"{data_category.value}_{processing_purpose.value}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _update_indexes(self, consent_record: ConsentRecord):
        """Update consent indexes."""
        self.consent_by_subject[consent_record.subject_id].add(consent_record.consent_id)
        
        for category in consent_record.data_categories:
            self.consent_by_category[category].add(consent_record.consent_id)
        
        for purpose in consent_record.processing_purposes:
            self.consent_by_purpose[purpose].add(consent_record.consent_id)
    
    def _remove_from_indexes(self, consent_record: ConsentRecord):
        """Remove consent from indexes."""
        self.consent_by_subject[consent_record.subject_id].discard(consent_record.consent_id)
        
        for category in consent_record.data_categories:
            self.consent_by_category[category].discard(consent_record.consent_id)
        
        for purpose in consent_record.processing_purposes:
            self.consent_by_purpose[purpose].discard(consent_record.consent_id)

class DataRetentionManager:
    """Data retention management system."""
    
    def __init__(self, consent_manager: ConsentManager):
        """Initialize data retention manager.
        
        Args:
            consent_manager: Consent manager instance
        """
        self.consent_manager = consent_manager
        logger.info("Data retention manager initialized")
    
    def get_retention_deadline(
        self,
        subject_id: str,
        data_category: DataCategory,
        processing_purpose: ProcessingPurpose
    ) -> Optional[datetime]:
        """Get retention deadline for data.
        
        Args:
            subject_id: Data subject ID
            data_category: Data category
            processing_purpose: Processing purpose
            
        Returns:
            Retention deadline or None
        """
        # Get retention policy
        policy = self.consent_manager.get_retention_policy(data_category, processing_purpose)
        
        if not policy:
            return None
        
        # Get consent record
        consent_records = self.consent_manager.get_consent_records(
            subject_id=subject_id,
            data_category=data_category,
            processing_purpose=processing_purpose,
            valid_only=False
        )
        
        if not consent_records:
            return None
        
        # Use the earliest consent date
        earliest_consent = min(consent_records, key=lambda r: r.created_at)
        return earliest_consent.created_at + policy.retention_period
    
    def get_data_for_deletion(self) -> List[Dict[str, Any]]:
        """Get data that should be deleted based on retention policies.
        
        Returns:
            List of data deletion records
        """
        deletion_records = []
        
        for consent_record in self.consent_manager.consent_records.values():
            if not consent_record.granted:
                continue
            
            for data_category in consent_record.data_categories:
                for processing_purpose in consent_record.processing_purposes:
                    deadline = self.get_retention_deadline(
                        consent_record.subject_id,
                        data_category,
                        processing_purpose
                    )
                    
                    if deadline and datetime.now() > deadline:
                        deletion_records.append({
                            "subject_id": consent_record.subject_id,
                            "data_category": data_category.value,
                            "processing_purpose": processing_purpose.value,
                            "retention_deadline": deadline.isoformat(),
                            "consent_id": consent_record.consent_id
                        })
        
        return deletion_records
    
    def cleanup_expired_data(self) -> int:
        """Clean up expired data based on retention policies.
        
        Returns:
            Number of cleanup operations performed
        """
        deletion_records = self.get_data_for_deletion()
        
        for record in deletion_records:
            # In a real implementation, this would trigger actual data deletion
            # For now, we'll just log the cleanup action
            logger.info(f"Data cleanup scheduled for subject {record['subject_id']}: {record['data_category']}")
        
        return len(deletion_records)

# Convenience functions
def create_consent_manager(**kwargs) -> ConsentManager:
    """Create a consent manager instance."""
    return ConsentManager(**kwargs)

def create_data_retention_manager(consent_manager: ConsentManager) -> DataRetentionManager:
    """Create a data retention manager instance."""
    return DataRetentionManager(consent_manager)
