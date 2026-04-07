"""
Audit Logging

This module provides comprehensive audit logging and monitoring capabilities
for security events, compliance tracking, and system monitoring.
"""

import logging
import json
import hashlib
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of audit events."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    SYSTEM_ACCESS = "system_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    PRIVACY_EVENT = "privacy_event"
    ERROR_EVENT = "error_event"
    PERFORMANCE_EVENT = "performance_event"

class AuditSeverity(Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Audit event record."""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    outcome: str = "success"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource": self.resource,
            "action": self.action,
            "details": self.details,
            "outcome": self.outcome,
            "error_message": self.error_message,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create audit event from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            severity=AuditSeverity(data["severity"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            resource=data.get("resource"),
            action=data.get("action"),
            details=data.get("details", {}),
            outcome=data.get("outcome", "success"),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {})
        )

class AuditLogger:
    """Comprehensive audit logger."""
    
    def __init__(
        self,
        max_events: int = 10000,
        retention_days: int = 90,
        enable_compression: bool = True
    ):
        """Initialize audit logger.
        
        Args:
            max_events: Maximum number of events to keep in memory
            retention_days: Number of days to retain events
            enable_compression: Whether to compress stored events
        """
        self.max_events = max_events
        self.retention_days = retention_days
        self.enable_compression = enable_compression
        
        # Event storage
        self.events: deque = deque(maxlen=max_events)
        self.event_index: Dict[str, AuditEvent] = {}
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_severity": defaultdict(int),
            "events_by_user": defaultdict(int),
            "events_by_outcome": defaultdict(int),
            "last_cleanup": datetime.now()
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info("Audit logger initialized")
    
    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        outcome: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an audit event.
        
        Args:
            event_type: Type of event
            severity: Severity level
            user_id: User identifier
            session_id: Session identifier
            ip_address: IP address
            user_agent: User agent string
            resource: Resource accessed
            action: Action performed
            details: Event details
            outcome: Event outcome
            error_message: Error message if applicable
            metadata: Additional metadata
            
        Returns:
            Event ID
        """
        with self._lock:
            # Generate event ID
            event_id = self._generate_event_id(event_type, user_id, action)
            
            # Create audit event
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                severity=severity,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource=resource,
                action=action,
                details=details or {},
                outcome=outcome,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            # Store event
            self.events.append(event)
            self.event_index[event_id] = event
            
            # Update statistics
            self._update_stats(event)
            
            # Cleanup old events
            self._cleanup_old_events()
            
            logger.info(f"Logged audit event: {event_id}")
            return event_id
    
    def log_authentication(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log authentication event."""
        return self.log_event(
            event_type=AuditEventType.AUTHENTICATION,
            severity=AuditSeverity.HIGH if not success else AuditSeverity.MEDIUM,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action="login" if success else "login_failed",
            outcome="success" if success else "failure",
            details=details or {}
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log data access event."""
        return self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.MEDIUM,
            user_id=user_id,
            resource=resource,
            action=action,
            outcome="success" if success else "failure",
            details=details or {}
        )
    
    def log_data_modification(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log data modification event."""
        return self.log_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            severity=AuditSeverity.HIGH,
            user_id=user_id,
            resource=resource,
            action=action,
            outcome="success" if success else "failure",
            details=details or {}
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: AuditSeverity,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log security event."""
        return self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            severity=severity,
            user_id=user_id,
            action=event_type,
            details=details or {}
        )
    
    def log_compliance_event(
        self,
        compliance_type: str,
        severity: AuditSeverity,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log compliance event."""
        return self.log_event(
            event_type=AuditEventType.COMPLIANCE_EVENT,
            severity=severity,
            action=compliance_type,
            details=details or {}
        )
    
    def get_events(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[AuditEvent]:
        """Get audit events with filters.
        
        Args:
            event_type: Filter by event type
            severity: Filter by severity
            user_id: Filter by user ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of events to return
            
        Returns:
            List of audit events
        """
        with self._lock:
            filtered_events = []
            
            for event in self.events:
                # Apply filters
                if event_type and event.event_type != event_type:
                    continue
                if severity and event.severity != severity:
                    continue
                if user_id and event.user_id != user_id:
                    continue
                if start_time and event.timestamp < start_time:
                    continue
                if end_time and event.timestamp > end_time:
                    continue
                
                filtered_events.append(event)
                
                # Apply limit
                if limit and len(filtered_events) >= limit:
                    break
            
            return filtered_events
    
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Get audit event by ID."""
        with self._lock:
            return self.event_index.get(event_id)
    
    def get_user_activity(self, user_id: str, hours: int = 24) -> List[AuditEvent]:
        """Get user activity for specified hours."""
        start_time = datetime.now() - timedelta(hours=hours)
        return self.get_events(user_id=user_id, start_time=start_time)
    
    def get_security_events(self, hours: int = 24) -> List[AuditEvent]:
        """Get security events for specified hours."""
        start_time = datetime.now() - timedelta(hours=hours)
        return self.get_events(
            event_type=AuditEventType.SECURITY_EVENT,
            start_time=start_time
        )
    
    def get_failed_authentications(self, hours: int = 24) -> List[AuditEvent]:
        """Get failed authentication events."""
        start_time = datetime.now() - timedelta(hours=hours)
        auth_events = self.get_events(
            event_type=AuditEventType.AUTHENTICATION,
            start_time=start_time
        )
        # Filter for failed authentications
        return [event for event in auth_events if event.outcome == "failure"]
    
    def export_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json"
    ) -> Union[str, List[Dict[str, Any]]]:
        """Export audit events.
        
        Args:
            start_time: Start time for export
            end_time: End time for export
            format: Export format (json, dict)
            
        Returns:
            Exported events
        """
        events = self.get_events(start_time=start_time, end_time=end_time)
        
        if format == "json":
            return json.dumps([event.to_dict() for event in events], indent=2)
        else:
            return [event.to_dict() for event in events]
    
    def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit statistics."""
        with self._lock:
            return {
                "total_events": self.stats["total_events"],
                "events_by_type": dict(self.stats["events_by_type"]),
                "events_by_severity": dict(self.stats["events_by_severity"]),
                "events_by_user": dict(self.stats["events_by_user"]),
                "events_by_outcome": dict(self.stats["events_by_outcome"]),
                "last_cleanup": self.stats["last_cleanup"].isoformat(),
                "current_events_count": len(self.events)
            }
    
    def _generate_event_id(self, event_type: AuditEventType, user_id: Optional[str], action: Optional[str]) -> str:
        """Generate unique event ID."""
        timestamp = datetime.now().isoformat()
        content = f"{event_type.value}_{user_id}_{action}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _update_stats(self, event: AuditEvent):
        """Update audit statistics."""
        self.stats["total_events"] += 1
        self.stats["events_by_type"][event.event_type.value] += 1
        self.stats["events_by_severity"][event.severity.value] += 1
        self.stats["events_by_outcome"][event.outcome] += 1
        
        if event.user_id:
            self.stats["events_by_user"][event.user_id] += 1
    
    def _cleanup_old_events(self):
        """Clean up old events based on retention policy."""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        
        # Remove old events from deque
        while self.events and self.events[0].timestamp < cutoff_time:
            old_event = self.events.popleft()
            if old_event.event_id in self.event_index:
                del self.event_index[old_event.event_id]
        
        self.stats["last_cleanup"] = datetime.now()

class ComplianceAuditor:
    """Compliance auditor for audit logs."""
    
    def __init__(self, audit_logger: AuditLogger):
        """Initialize compliance auditor.
        
        Args:
            audit_logger: Audit logger instance
        """
        self.audit_logger = audit_logger
        logger.info("Compliance auditor initialized")
    
    def audit_data_access_compliance(self, hours: int = 24) -> Dict[str, Any]:
        """Audit data access compliance."""
        start_time = datetime.now() - timedelta(hours=hours)
        data_access_events = self.audit_logger.get_events(
            event_type=AuditEventType.DATA_ACCESS,
            start_time=start_time
        )
        
        # Analyze compliance
        total_access = len(data_access_events)
        unauthorized_access = len([e for e in data_access_events if e.outcome == "failure"])
        compliance_rate = (total_access - unauthorized_access) / total_access * 100 if total_access > 0 else 100
        
        return {
            "total_data_access": total_access,
            "unauthorized_access": unauthorized_access,
            "compliance_rate": compliance_rate,
            "violations": unauthorized_access > 0
        }
    
    def audit_authentication_compliance(self, hours: int = 24) -> Dict[str, Any]:
        """Audit authentication compliance."""
        start_time = datetime.now() - timedelta(hours=hours)
        auth_events = self.audit_logger.get_events(
            event_type=AuditEventType.AUTHENTICATION,
            start_time=start_time
        )
        
        # Analyze compliance
        total_auth = len(auth_events)
        failed_auth = len([e for e in auth_events if e.outcome == "failure"])
        success_rate = (total_auth - failed_auth) / total_auth * 100 if total_auth > 0 else 100
        
        return {
            "total_authentications": total_auth,
            "failed_authentications": failed_auth,
            "success_rate": success_rate,
            "security_concerns": failed_auth > total_auth * 0.1  # More than 10% failure rate
        }
    
    def audit_security_compliance(self, hours: int = 24) -> Dict[str, Any]:
        """Audit security compliance."""
        start_time = datetime.now() - timedelta(hours=hours)
        security_events = self.audit_logger.get_events(
            event_type=AuditEventType.SECURITY_EVENT,
            start_time=start_time
        )
        
        # Analyze compliance
        critical_events = len([e for e in security_events if e.severity == AuditSeverity.CRITICAL])
        high_events = len([e for e in security_events if e.severity == AuditSeverity.HIGH])
        
        return {
            "total_security_events": len(security_events),
            "critical_events": critical_events,
            "high_severity_events": high_events,
            "security_incidents": critical_events > 0 or high_events > 5
        }
    
    def generate_compliance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        data_access_audit = self.audit_data_access_compliance(hours)
        auth_audit = self.audit_authentication_compliance(hours)
        security_audit = self.audit_security_compliance(hours)
        
        # Calculate overall compliance score
        compliance_scores = [
            data_access_audit["compliance_rate"],
            auth_audit["success_rate"],
            100 - (security_audit["security_incidents"] * 20)  # Penalize security incidents
        ]
        overall_score = sum(compliance_scores) / len(compliance_scores)
        
        return {
            "overall_compliance_score": overall_score,
            "data_access_compliance": data_access_audit,
            "authentication_compliance": auth_audit,
            "security_compliance": security_audit,
            "report_generated_at": datetime.now().isoformat(),
            "audit_period_hours": hours
        }

# Convenience functions
def create_audit_logger(**kwargs) -> AuditLogger:
    """Create an audit logger instance."""
    return AuditLogger(**kwargs)

def create_compliance_auditor(audit_logger: AuditLogger) -> ComplianceAuditor:
    """Create a compliance auditor instance."""
    return ComplianceAuditor(audit_logger)
