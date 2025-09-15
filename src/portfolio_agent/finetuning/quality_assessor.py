"""
Quality Assessment Module

This module provides response quality assessment and evaluation metrics
for fine-tuned models and generated responses.
"""

import logging
import re
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

try:
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available. Install with: pip install scikit-learn")

logger = logging.getLogger(__name__)

class QualityMetric(Enum):
    """Available quality metrics."""
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    FLUENCY = "fluency"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    DIVERSITY = "diversity"
    READABILITY = "readability"

@dataclass
class QualityMetrics:
    """Quality metrics for a response."""
    relevance_score: float = 0.0
    coherence_score: float = 0.0
    fluency_score: float = 0.0
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    consistency_score: float = 0.0
    diversity_score: float = 0.0
    readability_score: float = 0.0
    overall_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class QualityAssessor:
    """Quality assessor for evaluating response quality."""
    
    def __init__(self, use_sklearn: bool = True):
        """Initialize quality assessor.
        
        Args:
            use_sklearn: Whether to use scikit-learn for advanced metrics
        """
        self.use_sklearn = use_sklearn and SKLEARN_AVAILABLE
        
        if self.use_sklearn:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
        
        logger.info("Quality assessor initialized")
    
    def assess_response(
        self,
        response: str,
        query: str,
        context: Optional[str] = None,
        reference: Optional[str] = None
    ) -> QualityMetrics:
        """Assess the quality of a response.
        
        Args:
            response: The response to assess
            query: The original query
            context: Optional context information
            reference: Optional reference response
            
        Returns:
            QualityMetrics with assessment scores
        """
        logger.info("Assessing response quality")
        
        # Calculate individual metrics
        relevance_score = self._calculate_relevance(response, query, context)
        coherence_score = self._calculate_coherence(response)
        fluency_score = self._calculate_fluency(response)
        completeness_score = self._calculate_completeness(response, query)
        accuracy_score = self._calculate_accuracy(response, reference) if reference else 0.5
        consistency_score = self._calculate_consistency(response)
        diversity_score = self._calculate_diversity(response)
        readability_score = self._calculate_readability(response)
        
        # Calculate overall score (weighted average)
        weights = {
            'relevance': 0.25,
            'coherence': 0.20,
            'fluency': 0.15,
            'completeness': 0.15,
            'accuracy': 0.10,
            'consistency': 0.10,
            'diversity': 0.03,
            'readability': 0.02
        }
        
        overall_score = (
            relevance_score * weights['relevance'] +
            coherence_score * weights['coherence'] +
            fluency_score * weights['fluency'] +
            completeness_score * weights['completeness'] +
            accuracy_score * weights['accuracy'] +
            consistency_score * weights['consistency'] +
            diversity_score * weights['diversity'] +
            readability_score * weights['readability']
        )
        
        metrics = QualityMetrics(
            relevance_score=relevance_score,
            coherence_score=coherence_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            diversity_score=diversity_score,
            readability_score=readability_score,
            overall_score=overall_score,
            metadata={
                'query_length': len(query),
                'response_length': len(response),
                'context_provided': context is not None,
                'reference_provided': reference is not None
            }
        )
        
        logger.info(f"Quality assessment complete. Overall score: {overall_score:.3f}")
        return metrics
    
    def _calculate_relevance(
        self,
        response: str,
        query: str,
        context: Optional[str] = None
    ) -> float:
        """Calculate relevance score."""
        if not response or not query:
            return 0.0
        
        # Extract keywords from query
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        # Calculate keyword overlap
        if not query_words:
            return 0.0
        
        overlap = len(query_words.intersection(response_words))
        relevance = overlap / len(query_words)
        
        # Boost score if context is used
        if context:
            context_words = set(re.findall(r'\b\w+\b', context.lower()))
            context_overlap = len(context_words.intersection(response_words))
            if context_words:
                context_relevance = context_overlap / len(context_words)
                relevance = (relevance + context_relevance) / 2
        
        return min(1.0, relevance)
    
    def _calculate_coherence(self, response: str) -> float:
        """Calculate coherence score."""
        if not response:
            return 0.0
        
        # Check for sentence structure
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return 0.5  # Single sentence is somewhat coherent
        
        # Check for transition words
        transition_words = [
            'however', 'therefore', 'moreover', 'furthermore', 'additionally',
            'consequently', 'meanwhile', 'similarly', 'likewise', 'in contrast',
            'on the other hand', 'for example', 'for instance', 'specifically'
        ]
        
        transition_count = sum(1 for word in transition_words 
                             if word in response.lower())
        
        # Check for pronoun resolution (simple heuristic)
        pronouns = ['it', 'this', 'that', 'these', 'those', 'he', 'she', 'they']
        pronoun_count = sum(1 for word in pronouns 
                           if word in response.lower())
        
        # Calculate coherence score
        transition_score = min(1.0, transition_count / len(sentences))
        pronoun_score = min(1.0, pronoun_count / len(sentences))
        
        coherence = (transition_score + pronoun_score) / 2
        return min(1.0, coherence)
    
    def _calculate_fluency(self, response: str) -> float:
        """Calculate fluency score."""
        if not response:
            return 0.0
        
        # Check for common fluency issues
        issues = 0
        
        # Repetitive words
        words = response.lower().split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        repetitive_words = sum(1 for count in word_counts.values() if count > 3)
        issues += repetitive_words
        
        # Incomplete sentences
        incomplete_sentences = response.count('...') + response.count('--')
        issues += incomplete_sentences
        
        # Very short or very long sentences
        sentences = re.split(r'[.!?]+', response)
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count < 3 or word_count > 50:
                issues += 1
        
        # Calculate fluency score (lower issues = higher fluency)
        max_issues = len(words) // 10 + 5  # Allow some issues
        fluency = max(0.0, 1.0 - (issues / max_issues))
        
        return fluency
    
    def _calculate_completeness(self, response: str, query: str) -> float:
        """Calculate completeness score."""
        if not response or not query:
            return 0.0
        
        # Check if response addresses the query
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        # Calculate coverage
        coverage = len(query_words.intersection(response_words)) / len(query_words)
        
        # Check for question answering
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        is_question = any(word in query.lower() for word in question_words)
        
        if is_question:
            # Check if response provides an answer
            answer_indicators = ['because', 'due to', 'as a result', 'in order to', 'the answer is']
            has_answer = any(indicator in response.lower() for indicator in answer_indicators)
            completeness = coverage * 0.7 + (0.3 if has_answer else 0.0)
        else:
            completeness = coverage
        
        return min(1.0, completeness)
    
    def _calculate_accuracy(self, response: str, reference: Optional[str]) -> float:
        """Calculate accuracy score."""
        if not reference:
            return 0.5  # Neutral score when no reference
        
        if not response:
            return 0.0
        
        if self.use_sklearn:
            # Use TF-IDF similarity
            try:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform([response, reference])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                return similarity
            except Exception:
                pass
        
        # Fallback to simple word overlap
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        reference_words = set(re.findall(r'\b\w+\b', reference.lower()))
        
        if not reference_words:
            return 0.0
        
        overlap = len(response_words.intersection(reference_words))
        accuracy = overlap / len(reference_words)
        
        return min(1.0, accuracy)
    
    def _calculate_consistency(self, response: str) -> float:
        """Calculate consistency score."""
        if not response:
            return 0.0
        
        # Check for contradictory statements (simple heuristic)
        contradictions = [
            ('yes', 'no'), ('true', 'false'), ('always', 'never'),
            ('all', 'none'), ('every', 'no'), ('definitely', 'maybe')
        ]
        
        response_lower = response.lower()
        contradiction_count = 0
        
        for pos, neg in contradictions:
            if pos in response_lower and neg in response_lower:
                contradiction_count += 1
        
        # Check for tense consistency
        past_tense_words = ['was', 'were', 'had', 'did', 'went', 'came']
        present_tense_words = ['is', 'are', 'has', 'do', 'go', 'come']
        
        past_count = sum(1 for word in past_tense_words if word in response_lower)
        present_count = sum(1 for word in present_tense_words if word in response_lower)
        
        tense_consistency = 1.0 if (past_count == 0 or present_count == 0) else 0.5
        
        # Calculate consistency score
        contradiction_penalty = contradiction_count * 0.2
        consistency = max(0.0, tense_consistency - contradiction_penalty)
        
        return consistency
    
    def _calculate_diversity(self, response: str) -> float:
        """Calculate diversity score."""
        if not response:
            return 0.0
        
        words = response.lower().split()
        if len(words) < 2:
            return 0.0
        
        # Calculate type-token ratio
        unique_words = len(set(words))
        total_words = len(words)
        ttr = unique_words / total_words
        
        # Calculate diversity score
        diversity = min(1.0, ttr * 2)  # Scale up the TTR
        
        return diversity
    
    def _calculate_readability(self, response: str) -> float:
        """Calculate readability score using Flesch Reading Ease."""
        if not response:
            return 0.0
        
        # Count sentences
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        if sentence_count == 0:
            return 0.0
        
        # Count words and syllables
        words = response.split()
        word_count = len(words)
        
        if word_count == 0:
            return 0.0
        
        # Estimate syllables (simple heuristic)
        syllable_count = 0
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^a-zA-Z]', '', word.lower())
            if clean_word:
                # Simple syllable estimation
                vowels = 'aeiouy'
                syllable_count += sum(1 for char in clean_word if char in vowels)
                # Adjust for silent e
                if clean_word.endswith('e'):
                    syllable_count -= 1
                # Minimum 1 syllable per word
                syllable_count = max(1, syllable_count)
        
        # Calculate Flesch Reading Ease
        try:
            flesch_score = 206.835 - (1.015 * (word_count / sentence_count)) - (84.6 * (syllable_count / word_count))
            # Normalize to 0-1 scale
            readability = max(0.0, min(1.0, flesch_score / 100))
        except ZeroDivisionError:
            readability = 0.5
        
        return readability

class ResponseEvaluator:
    """Evaluator for comparing multiple responses."""
    
    def __init__(self, quality_assessor: QualityAssessor):
        """Initialize response evaluator.
        
        Args:
            quality_assessor: Quality assessor instance
        """
        self.quality_assessor = quality_assessor
    
    def compare_responses(
        self,
        responses: List[str],
        query: str,
        context: Optional[str] = None,
        reference: Optional[str] = None
    ) -> List[Tuple[str, QualityMetrics]]:
        """Compare multiple responses.
        
        Args:
            responses: List of responses to compare
            query: Original query
            context: Optional context
            reference: Optional reference response
            
        Returns:
            List of (response, metrics) tuples sorted by overall score
        """
        logger.info(f"Comparing {len(responses)} responses")
        
        results = []
        for response in responses:
            metrics = self.quality_assessor.assess_response(
                response, query, context, reference
            )
            results.append((response, metrics))
        
        # Sort by overall score (descending)
        results.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        return results
    
    def get_best_response(
        self,
        responses: List[str],
        query: str,
        context: Optional[str] = None,
        reference: Optional[str] = None
    ) -> Tuple[str, QualityMetrics]:
        """Get the best response based on quality assessment.
        
        Args:
            responses: List of responses
            query: Original query
            context: Optional context
            reference: Optional reference response
            
        Returns:
            Tuple of (best_response, metrics)
        """
        results = self.compare_responses(responses, query, context, reference)
        return results[0] if results else ("", QualityMetrics())
    
    def evaluate_model_performance(
        self,
        test_data: List[Dict[str, str]],
        model_responses: List[str]
    ) -> Dict[str, float]:
        """Evaluate model performance on test data.
        
        Args:
            test_data: List of test examples with 'query', 'context', 'reference'
            model_responses: List of model responses
            
        Returns:
            Dictionary with performance metrics
        """
        if len(test_data) != len(model_responses):
            raise ValueError("Test data and model responses must have the same length")
        
        logger.info(f"Evaluating model performance on {len(test_data)} examples")
        
        all_metrics = []
        for i, (test_example, response) in enumerate(zip(test_data, model_responses)):
            metrics = self.quality_assessor.assess_response(
                response=response,
                query=test_example['query'],
                context=test_example.get('context'),
                reference=test_example.get('reference')
            )
            all_metrics.append(metrics)
        
        # Calculate average metrics
        avg_metrics = {
            'relevance': np.mean([m.relevance_score for m in all_metrics]),
            'coherence': np.mean([m.coherence_score for m in all_metrics]),
            'fluency': np.mean([m.fluency_score for m in all_metrics]),
            'completeness': np.mean([m.completeness_score for m in all_metrics]),
            'accuracy': np.mean([m.accuracy_score for m in all_metrics]),
            'consistency': np.mean([m.consistency_score for m in all_metrics]),
            'diversity': np.mean([m.diversity_score for m in all_metrics]),
            'readability': np.mean([m.readability_score for m in all_metrics]),
            'overall': np.mean([m.overall_score for m in all_metrics])
        }
        
        logger.info(f"Model performance evaluation complete. Overall score: {avg_metrics['overall']:.3f}")
        return avg_metrics

# Convenience functions
def create_quality_assessor(use_sklearn: bool = True) -> QualityAssessor:
    """Create a quality assessor instance."""
    return QualityAssessor(use_sklearn=use_sklearn)

def create_response_evaluator(quality_assessor: QualityAssessor = None) -> ResponseEvaluator:
    """Create a response evaluator instance."""
    if quality_assessor is None:
        quality_assessor = create_quality_assessor()
    return ResponseEvaluator(quality_assessor)
