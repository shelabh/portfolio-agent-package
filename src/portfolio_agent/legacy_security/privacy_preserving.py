"""
Privacy-Preserving Techniques

This module provides privacy-preserving techniques including differential privacy,
data anonymization, and k-anonymity for protecting sensitive information.
"""

import logging
import random
import hashlib
import math
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas not available. Install with: pip install pandas")

logger = logging.getLogger(__name__)

class PrivacyTechnique(Enum):
    """Privacy-preserving techniques."""
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    K_ANONYMITY = "k_anonymity"
    L_DIVERSITY = "l_diversity"
    T_CLOSENESS = "t_closeness"
    DATA_MASKING = "data_masking"
    PSEUDONYMIZATION = "pseudonymization"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"

@dataclass
class PrivacyConfig:
    """Configuration for privacy-preserving techniques."""
    technique: PrivacyTechnique
    epsilon: float = 1.0  # For differential privacy
    delta: float = 1e-5   # For differential privacy
    k: int = 3           # For k-anonymity
    l: int = 2           # For l-diversity
    t: float = 0.1       # For t-closeness
    noise_scale: float = 1.0
    seed: Optional[int] = None

class DifferentialPrivacy:
    """Differential privacy implementation."""
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5, seed: Optional[int] = None):
        """Initialize differential privacy.
        
        Args:
            epsilon: Privacy parameter (smaller = more private)
            delta: Failure probability
            seed: Random seed for reproducibility
        """
        self.epsilon = epsilon
        self.delta = delta
        self.seed = seed
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        logger.info(f"Differential privacy initialized with epsilon={epsilon}, delta={delta}")
    
    def add_laplace_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """Add Laplace noise for differential privacy.
        
        Args:
            value: Original value
            sensitivity: Sensitivity of the function
            
        Returns:
            Noisy value
        """
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale)
        return value + noise
    
    def add_gaussian_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """Add Gaussian noise for differential privacy.
        
        Args:
            value: Original value
            sensitivity: Sensitivity of the function
            
        Returns:
            Noisy value
        """
        sigma = math.sqrt(2 * math.log(1.25 / self.delta)) * sensitivity / self.epsilon
        noise = np.random.normal(0, sigma)
        return value + noise
    
    def private_count(self, data: List[Any], query: callable) -> float:
        """Compute private count with differential privacy.
        
        Args:
            data: Dataset
            query: Query function
            
        Returns:
            Private count
        """
        true_count = sum(1 for item in data if query(item))
        return self.add_laplace_noise(true_count, sensitivity=1.0)
    
    def private_sum(self, data: List[float], sensitivity: float = 1.0) -> float:
        """Compute private sum with differential privacy.
        
        Args:
            data: Numeric dataset
            sensitivity: Sensitivity of the sum function
            
        Returns:
            Private sum
        """
        true_sum = sum(data)
        return self.add_laplace_noise(true_sum, sensitivity)
    
    def private_mean(self, data: List[float], sensitivity: float = 1.0) -> float:
        """Compute private mean with differential privacy.
        
        Args:
            data: Numeric dataset
            sensitivity: Sensitivity of the mean function
            
        Returns:
            Private mean
        """
        if not data:
            return 0.0
        
        true_mean = sum(data) / len(data)
        # Sensitivity for mean is sensitivity / n
        mean_sensitivity = sensitivity / len(data)
        return self.add_laplace_noise(true_mean, mean_sensitivity)
    
    def private_histogram(self, data: List[Any], bins: List[Any]) -> Dict[Any, float]:
        """Compute private histogram with differential privacy.
        
        Args:
            data: Dataset
            bins: Histogram bins
            
        Returns:
            Private histogram
        """
        # Compute true histogram
        true_hist = {}
        for bin_val in bins:
            true_hist[bin_val] = sum(1 for item in data if item == bin_val)
        
        # Add noise to each bin
        private_hist = {}
        for bin_val, count in true_hist.items():
            private_hist[bin_val] = self.add_laplace_noise(count, sensitivity=1.0)
        
        return private_hist

class DataAnonymizer:
    """Data anonymization techniques."""
    
    def __init__(self, config: PrivacyConfig):
        """Initialize data anonymizer.
        
        Args:
            config: Privacy configuration
        """
        self.config = config
        logger.info(f"Data anonymizer initialized with {config.technique.value}")
    
    def k_anonymize(self, data: List[Dict[str, Any]], quasi_identifiers: List[str]) -> List[Dict[str, Any]]:
        """Apply k-anonymity to data.
        
        Args:
            data: Dataset to anonymize
            quasi_identifiers: Quasi-identifier attributes
            
        Returns:
            K-anonymized dataset
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas required for k-anonymity")
        
        df = pd.DataFrame(data)
        
        # Group by quasi-identifiers
        groups = df.groupby(quasi_identifiers)
        
        # Filter groups with size >= k
        k_anonymous_groups = []
        for name, group in groups:
            if len(group) >= self.config.k:
                k_anonymous_groups.append(group)
        
        if k_anonymous_groups:
            result_df = pd.concat(k_anonymous_groups, ignore_index=True)
            return result_df.to_dict('records')
        else:
            return []
    
    def l_diversify(self, data: List[Dict[str, Any]], quasi_identifiers: List[str], sensitive_attribute: str) -> List[Dict[str, Any]]:
        """Apply l-diversity to data.
        
        Args:
            data: Dataset to anonymize
            quasi_identifiers: Quasi-identifier attributes
            sensitive_attribute: Sensitive attribute for diversity
            
        Returns:
            L-diverse dataset
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas required for l-diversity")
        
        df = pd.DataFrame(data)
        
        # Group by quasi-identifiers
        groups = df.groupby(quasi_identifiers)
        
        # Filter groups with l-diversity
        l_diverse_groups = []
        for name, group in groups:
            unique_sensitive = group[sensitive_attribute].nunique()
            if unique_sensitive >= self.config.l:
                l_diverse_groups.append(group)
        
        if l_diverse_groups:
            result_df = pd.concat(l_diverse_groups, ignore_index=True)
            return result_df.to_dict('records')
        else:
            return []
    
    def generalize_data(self, data: List[Dict[str, Any]], generalization_rules: Dict[str, callable]) -> List[Dict[str, Any]]:
        """Apply generalization to data.
        
        Args:
            data: Dataset to generalize
            generalization_rules: Rules for generalization
            
        Returns:
            Generalized dataset
        """
        generalized_data = []
        
        for record in data:
            generalized_record = record.copy()
            
            for attribute, rule in generalization_rules.items():
                if attribute in generalized_record:
                    generalized_record[attribute] = rule(generalized_record[attribute])
            
            generalized_data.append(generalized_record)
        
        return generalized_data
    
    def suppress_data(self, data: List[Dict[str, Any]], suppression_rules: Dict[str, callable]) -> List[Dict[str, Any]]:
        """Apply suppression to data.
        
        Args:
            data: Dataset to suppress
            suppression_rules: Rules for suppression
            
        Returns:
            Suppressed dataset
        """
        suppressed_data = []
        
        for record in data:
            suppressed_record = record.copy()
            
            for attribute, rule in suppression_rules.items():
                if attribute in suppressed_record and rule(suppressed_record[attribute]):
                    suppressed_record[attribute] = "[SUPPRESSED]"
            
            suppressed_data.append(suppressed_record)
        
        return suppressed_data
    
    def mask_data(self, data: List[Dict[str, Any]], masking_rules: Dict[str, str]) -> List[Dict[str, Any]]:
        """Apply masking to data.
        
        Args:
            data: Dataset to mask
            masking_rules: Rules for masking
            
        Returns:
            Masked dataset
        """
        masked_data = []
        
        for record in data:
            masked_record = record.copy()
            
            for attribute, mask_char in masking_rules.items():
                if attribute in masked_record:
                    value = str(masked_record[attribute])
                    if len(value) > 2:
                        masked_value = value[0] + mask_char * (len(value) - 2) + value[-1]
                    else:
                        masked_value = mask_char * len(value)
                    masked_record[attribute] = masked_value
            
            masked_data.append(masked_record)
        
        return masked_data
    
    def pseudonymize_data(self, data: List[Dict[str, Any]], pseudonymization_rules: Dict[str, str]) -> List[Dict[str, Any]]:
        """Apply pseudonymization to data.
        
        Args:
            data: Dataset to pseudonymize
            pseudonymization_rules: Rules for pseudonymization
            
        Returns:
            Pseudonymized dataset
        """
        pseudonymized_data = []
        pseudonym_mapping = {}
        
        for record in data:
            pseudonymized_record = record.copy()
            
            for attribute, prefix in pseudonymization_rules.items():
                if attribute in pseudonymized_record:
                    value = str(pseudonymized_record[attribute])
                    
                    # Create consistent pseudonym
                    if value not in pseudonym_mapping:
                        pseudonym = prefix + "_" + hashlib.md5(value.encode()).hexdigest()[:8]
                        pseudonym_mapping[value] = pseudonym
                    
                    pseudonymized_record[attribute] = pseudonym_mapping[value]
            
            pseudonymized_data.append(pseudonymized_record)
        
        return pseudonymized_data

class PrivacyPreserver:
    """Main privacy preserver combining all techniques."""
    
    def __init__(self, config: PrivacyConfig):
        """Initialize privacy preserver.
        
        Args:
            config: Privacy configuration
        """
        self.config = config
        
        # Initialize differential privacy
        self.dp = DifferentialPrivacy(
            epsilon=config.epsilon,
            delta=config.delta,
            seed=config.seed
        )
        
        # Initialize data anonymizer
        self.anonymizer = DataAnonymizer(config)
        
        logger.info("Privacy preserver initialized")
    
    def preserve_privacy(
        self,
        data: Union[List[Dict[str, Any]], List[float], List[Any]],
        technique: Optional[PrivacyTechnique] = None,
        **kwargs
    ) -> Union[List[Dict[str, Any]], List[float], List[Any]]:
        """Apply privacy-preserving technique to data.
        
        Args:
            data: Data to process
            technique: Privacy technique to apply
            **kwargs: Additional arguments for specific techniques
            
        Returns:
            Privacy-preserved data
        """
        technique = technique or self.config.technique
        
        if technique == PrivacyTechnique.DIFFERENTIAL_PRIVACY:
            return self._apply_differential_privacy(data, **kwargs)
        elif technique == PrivacyTechnique.K_ANONYMITY:
            return self._apply_k_anonymity(data, **kwargs)
        elif technique == PrivacyTechnique.L_DIVERSITY:
            return self._apply_l_diversity(data, **kwargs)
        elif technique == PrivacyTechnique.DATA_MASKING:
            return self._apply_data_masking(data, **kwargs)
        elif technique == PrivacyTechnique.PSEUDONYMIZATION:
            return self._apply_pseudonymization(data, **kwargs)
        elif technique == PrivacyTechnique.GENERALIZATION:
            return self._apply_generalization(data, **kwargs)
        elif technique == PrivacyTechnique.SUPPRESSION:
            return self._apply_suppression(data, **kwargs)
        else:
            raise ValueError(f"Unsupported technique: {technique}")
    
    def _apply_differential_privacy(self, data: List[float], **kwargs) -> List[float]:
        """Apply differential privacy to numeric data."""
        sensitivity = kwargs.get('sensitivity', 1.0)
        return [self.dp.add_laplace_noise(value, sensitivity) for value in data]
    
    def _apply_k_anonymity(self, data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Apply k-anonymity to data."""
        quasi_identifiers = kwargs.get('quasi_identifiers', [])
        return self.anonymizer.k_anonymize(data, quasi_identifiers)
    
    def _apply_l_diversity(self, data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Apply l-diversity to data."""
        quasi_identifiers = kwargs.get('quasi_identifiers', [])
        sensitive_attribute = kwargs.get('sensitive_attribute', '')
        return self.anonymizer.l_diversify(data, quasi_identifiers, sensitive_attribute)
    
    def _apply_data_masking(self, data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Apply data masking to data."""
        masking_rules = kwargs.get('masking_rules', {})
        return self.anonymizer.mask_data(data, masking_rules)
    
    def _apply_pseudonymization(self, data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Apply pseudonymization to data."""
        pseudonymization_rules = kwargs.get('pseudonymization_rules', {})
        return self.anonymizer.pseudonymize_data(data, pseudonymization_rules)
    
    def _apply_generalization(self, data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Apply generalization to data."""
        generalization_rules = kwargs.get('generalization_rules', {})
        return self.anonymizer.generalize_data(data, generalization_rules)
    
    def _apply_suppression(self, data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Apply suppression to data."""
        suppression_rules = kwargs.get('suppression_rules', {})
        return self.anonymizer.suppress_data(data, suppression_rules)
    
    def get_privacy_stats(self) -> Dict[str, Any]:
        """Get privacy preservation statistics."""
        return {
            "technique": self.config.technique.value,
            "epsilon": self.config.epsilon,
            "delta": self.config.delta,
            "k": self.config.k,
            "l": self.config.l,
            "t": self.config.t,
            "noise_scale": self.config.noise_scale
        }

# Convenience functions
def create_privacy_preserver(**kwargs) -> PrivacyPreserver:
    """Create a privacy preserver instance."""
    config = PrivacyConfig(**kwargs)
    return PrivacyPreserver(config)

def apply_differential_privacy(
    data: List[float],
    epsilon: float = 1.0,
    delta: float = 1e-5
) -> List[float]:
    """Convenience function to apply differential privacy."""
    dp = DifferentialPrivacy(epsilon=epsilon, delta=delta)
    return [dp.add_laplace_noise(value) for value in data]

def anonymize_data(
    data: List[Dict[str, Any]],
    technique: PrivacyTechnique,
    **kwargs
) -> List[Dict[str, Any]]:
    """Convenience function to anonymize data."""
    config = PrivacyConfig(technique=technique)
    preserver = PrivacyPreserver(config)
    return preserver.preserve_privacy(data, technique, **kwargs)
