"""
Advanced PII Detection

This module provides sophisticated PII detection and redaction capabilities
using NER models, regex patterns, and machine learning techniques.
"""

import logging
import re
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json

try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available. Install with: pip install spacy")

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logging.warning("Presidio not available. Install with: pip install presidio-analyzer presidio-anonymizer")

logger = logging.getLogger(__name__)

class PIIType(Enum):
    """Types of PII that can be detected."""
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    ADDRESS = "address"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"
    URL = "url"
    BANK_ACCOUNT = "bank_account"
    ROUTING_NUMBER = "routing_number"
    API_KEY = "api_key"
    PASSWORD = "password"
    USERNAME = "username"
    LOCATION = "location"
    ORGANIZATION = "organization"
    PERSON = "person"

@dataclass
class PIIDetectionResult:
    """Result of PII detection."""
    text: str
    redacted_text: str
    detected_pii: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    redaction_stats: Dict[str, int]
    processing_time: float
    method_used: str

class AdvancedPIIDetector:
    """Advanced PII detector with multiple detection methods."""
    
    def __init__(
        self,
        use_spacy: bool = True,
        use_presidio: bool = True,
        custom_patterns: Optional[Dict[str, str]] = None,
        confidence_threshold: float = 0.5
    ):
        """Initialize advanced PII detector.
        
        Args:
            use_spacy: Whether to use spaCy NER models
            use_presidio: Whether to use Presidio for PII detection
            custom_patterns: Custom regex patterns for PII detection
            confidence_threshold: Minimum confidence threshold for detection
        """
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self.use_presidio = use_presidio and PRESIDIO_AVAILABLE
        self.confidence_threshold = confidence_threshold
        
        # Initialize spaCy
        if self.use_spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded successfully")
            except OSError:
                logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
                self.use_spacy = False
                self.nlp = None
        
        # Initialize Presidio
        if self.use_presidio:
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                logger.info("Presidio engines initialized successfully")
            except Exception as e:
                logger.warning(f"Presidio initialization failed: {e}")
                self.use_presidio = False
                self.analyzer = None
                self.anonymizer = None
        
        # Define comprehensive regex patterns
        self.patterns = {
            PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            PIIType.PHONE: r'(\+\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}',
            PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
            PIIType.CREDIT_CARD: r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            PIIType.IP_ADDRESS: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            PIIType.MAC_ADDRESS: r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b',
            PIIType.URL: r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
            PIIType.DATE_OF_BIRTH: r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b',
            PIIType.API_KEY: r'\b(?:sk|pk|ak)_[A-Za-z0-9]{20,}\b',
            PIIType.PASSWORD: r'\b(?:password|pwd|pass)\s*[:=]\s*[^\s]+\b',
            PIIType.USERNAME: r'\b(?:username|user|login)\s*[:=]\s*[^\s]+\b',
            PIIType.BANK_ACCOUNT: r'\b\d{8,17}\b',
            PIIType.ROUTING_NUMBER: r'\b\d{9}\b'
        }
        
        # Add custom patterns
        if custom_patterns:
            self.patterns.update(custom_patterns)
        
        # Compile patterns
        self.compiled_patterns = {
            pii_type: re.compile(pattern, re.IGNORECASE)
            for pii_type, pattern in self.patterns.items()
        }
        
        logger.info("Advanced PII detector initialized")
    
    def detect_pii(
        self,
        text: str,
        redaction_method: str = "replace",
        custom_redaction: Optional[str] = None
    ) -> PIIDetectionResult:
        """Detect and redact PII from text.
        
        Args:
            text: Input text to analyze
            redaction_method: Method for redaction ('replace', 'hash', 'mask', 'custom')
            custom_redaction: Custom redaction string (used with 'custom' method)
            
        Returns:
            PIIDetectionResult with detection and redaction information
        """
        import time
        start_time = time.time()
        
        logger.info(f"Detecting PII in text of length {len(text)}")
        
        detected_pii = []
        redacted_text = text
        confidence_scores = {}
        redaction_stats = {pii_type.value: 0 for pii_type in PIIType}
        
        # Method 1: Regex-based detection
        regex_results = self._detect_with_regex(text)
        detected_pii.extend(regex_results)
        
        # Method 2: spaCy NER detection
        if self.use_spacy:
            spacy_results = self._detect_with_spacy(text)
            detected_pii.extend(spacy_results)
        
        # Method 3: Presidio detection
        if self.use_presidio:
            presidio_results = self._detect_with_presidio(text)
            detected_pii.extend(presidio_results)
        
        # Remove duplicates and merge results
        detected_pii = self._merge_detection_results(detected_pii)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(detected_pii)
        
        # Apply redaction
        redacted_text, redaction_stats = self._apply_redaction(
            text, detected_pii, redaction_method, custom_redaction
        )
        
        processing_time = time.time() - start_time
        
        # Determine method used
        methods_used = []
        if regex_results:
            methods_used.append("regex")
        if self.use_spacy and spacy_results:
            methods_used.append("spacy")
        if self.use_presidio and presidio_results:
            methods_used.append("presidio")
        
        method_used = "+".join(methods_used) if methods_used else "regex"
        
        result = PIIDetectionResult(
            text=text,
            redacted_text=redacted_text,
            detected_pii=detected_pii,
            confidence_scores=confidence_scores,
            redaction_stats=redaction_stats,
            processing_time=processing_time,
            method_used=method_used
        )
        
        logger.info(f"PII detection completed in {processing_time:.3f}s")
        logger.info(f"Detected {len(detected_pii)} PII entities")
        
        return result
    
    def _detect_with_regex(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII using regex patterns."""
        results = []
        
        for pii_type, pattern in self.compiled_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                results.append({
                    "type": pii_type.value,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.8,  # High confidence for regex matches
                    "method": "regex"
                })
        
        return results
    
    def _detect_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII using spaCy NER."""
        if not self.nlp:
            return []
        
        results = []
        doc = self.nlp(text)
        
        # Map spaCy entities to PII types
        entity_mapping = {
            "PERSON": PIIType.NAME,
            "ORG": PIIType.ORGANIZATION,
            "GPE": PIIType.LOCATION,
            "DATE": PIIType.DATE_OF_BIRTH
        }
        
        for ent in doc.ents:
            if ent.label_ in entity_mapping:
                pii_type = entity_mapping[ent.label_]
                results.append({
                    "type": pii_type.value,
                    "value": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": ent._.prob if hasattr(ent._, 'prob') else 0.7,
                    "method": "spacy"
                })
        
        return results
    
    def _detect_with_presidio(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII using Presidio."""
        if not self.analyzer:
            return []
        
        results = []
        
        try:
            # Analyze text
            analyzer_results = self.analyzer.analyze(
                text=text,
                language='en',
                entities=[
                    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
                    "SSN", "IBAN_CODE", "IP_ADDRESS", "LOCATION", "DATE_TIME"
                ]
            )
            
            # Map Presidio entities to PII types
            entity_mapping = {
                "PERSON": PIIType.NAME,
                "EMAIL_ADDRESS": PIIType.EMAIL,
                "PHONE_NUMBER": PIIType.PHONE,
                "CREDIT_CARD": PIIType.CREDIT_CARD,
                "SSN": PIIType.SSN,
                "IBAN_CODE": PIIType.BANK_ACCOUNT,
                "IP_ADDRESS": PIIType.IP_ADDRESS,
                "LOCATION": PIIType.LOCATION,
                "DATE_TIME": PIIType.DATE_OF_BIRTH
            }
            
            for result in analyzer_results:
                if result.entity_type in entity_mapping:
                    pii_type = entity_mapping[result.entity_type]
                    results.append({
                        "type": pii_type.value,
                        "value": text[result.start:result.end],
                        "start": result.start,
                        "end": result.end,
                        "confidence": result.score,
                        "method": "presidio"
                    })
        
        except Exception as e:
            logger.warning(f"Presidio detection failed: {e}")
        
        return results
    
    def _merge_detection_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate detection results."""
        if not results:
            return []
        
        # Sort by start position
        results.sort(key=lambda x: x["start"])
        
        merged = []
        current = results[0]
        
        for next_result in results[1:]:
            # Check for overlap
            if (next_result["start"] < current["end"] and 
                next_result["type"] == current["type"]):
                # Merge overlapping results
                current["end"] = max(current["end"], next_result["end"])
                current["value"] = current["value"] + next_result["value"][current["end"] - next_result["start"]:]
                current["confidence"] = max(current["confidence"], next_result["confidence"])
            else:
                merged.append(current)
                current = next_result
        
        merged.append(current)
        return merged
    
    def _calculate_confidence_scores(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate confidence scores for each PII type."""
        confidence_scores = {}
        
        for result in results:
            pii_type = result["type"]
            if pii_type not in confidence_scores:
                confidence_scores[pii_type] = []
            confidence_scores[pii_type].append(result["confidence"])
        
        # Calculate average confidence for each type
        for pii_type in confidence_scores:
            scores = confidence_scores[pii_type]
            confidence_scores[pii_type] = sum(scores) / len(scores)
        
        return confidence_scores
    
    def _apply_redaction(
        self,
        text: str,
        detected_pii: List[Dict[str, Any]],
        method: str,
        custom_redaction: Optional[str] = None
    ) -> Tuple[str, Dict[str, int]]:
        """Apply redaction to detected PII."""
        redacted_text = text
        redaction_stats = {pii_type.value: 0 for pii_type in PIIType}
        
        # Sort by start position in reverse order to avoid index issues
        sorted_pii = sorted(detected_pii, key=lambda x: x["start"], reverse=True)
        
        for pii in sorted_pii:
            pii_type = pii["type"]
            start = pii["start"]
            end = pii["end"]
            
            # Determine redaction string
            if method == "replace":
                redaction_str = "[REDACTED]"
            elif method == "hash":
                redaction_str = hashlib.md5(pii["value"].encode()).hexdigest()[:8]
            elif method == "mask":
                redaction_str = "*" * len(pii["value"])
            elif method == "custom" and custom_redaction:
                redaction_str = custom_redaction
            else:
                redaction_str = "[REDACTED]"
            
            # Apply redaction
            redacted_text = redacted_text[:start] + redaction_str + redacted_text[end:]
            redaction_stats[pii_type] += 1
        
        return redacted_text, redaction_stats
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            "spacy_available": self.use_spacy,
            "presidio_available": self.use_presidio,
            "patterns_count": len(self.patterns),
            "confidence_threshold": self.confidence_threshold,
            "supported_pii_types": [pii_type.value for pii_type in PIIType]
        }
    
    def validate_pii_detection(self, result: PIIDetectionResult) -> bool:
        """Validate PII detection result."""
        if not result.text or not result.redacted_text:
            return False
        
        if len(result.detected_pii) != sum(result.redaction_stats.values()):
            return False
        
        if result.processing_time < 0:
            return False
        
        return True

# Convenience functions
def create_pii_detector(**kwargs) -> AdvancedPIIDetector:
    """Create an advanced PII detector instance."""
    return AdvancedPIIDetector(**kwargs)

def detect_pii_in_text(
    text: str,
    redaction_method: str = "replace",
    **kwargs
) -> PIIDetectionResult:
    """Convenience function to detect PII in text."""
    detector = create_pii_detector(**kwargs)
    return detector.detect_pii(text, redaction_method)
