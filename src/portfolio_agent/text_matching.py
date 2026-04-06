"""
Lightweight text matching helpers used by the canonical retrieval and response path.

These helpers intentionally stay simple: they normalize common word variants,
support a small set of domain-relevant expansions, and allow the caller to
ignore non-discriminative query terms.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Set

STOP_WORDS = {
    "a", "an", "and", "are", "about", "as", "at", "be", "by", "describe", "described", "did", "do", "does",
    "for", "from", "has", "have", "how", "i", "in", "into", "is", "it", "me", "of", "on", "or", "the", "to",
    "what", "which", "who", "with", "you",
}

TERM_GROUPS = (
    {"leadership", "lead", "led"},
    {"mentor", "mentoring", "mentored"},
    {"founder", "founders"},
    {"prototype", "prototypes"},
    {"engineer", "engineering"},
    {"product", "products"},
)


def extract_terms(text: str, *, ignored_terms: Set[str] | None = None) -> List[str]:
    ignored = ignored_terms or set()
    terms: List[str] = []
    for token in re.findall(r"\b[a-zA-Z0-9][a-zA-Z0-9\-]+\b", text.lower()):
        normalized = normalize_term(token)
        if len(normalized) <= 2 or normalized in STOP_WORDS or normalized in ignored:
            continue
        terms.append(normalized)
    return terms


def normalize_term(term: str) -> str:
    token = term.lower().strip()
    if token.endswith("ies") and len(token) > 4:
        token = token[:-3] + "y"
    elif token.endswith("ing") and len(token) > 5:
        token = token[:-3]
    elif token.endswith("ed") and len(token) > 4:
        token = token[:-2]
    elif token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
        token = token[:-1]
    return token


def term_variants(term: str) -> Set[str]:
    normalized = normalize_term(term)
    variants = {normalized}
    for group in TERM_GROUPS:
        group_normalized = {normalize_term(item) for item in group}
        if normalized in group_normalized:
            variants.update(group_normalized)
    return variants


def keyword_overlap(query: str, content: str, *, ignored_terms: Set[str] | None = None) -> int:
    content_terms = set(extract_terms(content))
    overlap = 0
    for term in extract_terms(query, ignored_terms=ignored_terms):
        if term_variants(term).intersection(content_terms):
            overlap += 1
    return overlap


def non_discriminative_terms(query: str, contents: Iterable[str], *, threshold: float = 0.8) -> Set[str]:
    content_list = list(contents)
    if not content_list:
        return set()

    query_terms = set(extract_terms(query))
    if not query_terms:
        return set()

    ignored: Set[str] = set()
    doc_count = len(content_list)
    minimum_hits = max(2, int(doc_count * threshold + 0.999))
    for term in query_terms:
        hits = sum(1 for content in content_list if keyword_overlap(term, content) > 0)
        if hits >= minimum_hits:
            ignored.add(term)
    return ignored
