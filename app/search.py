"""Keyword search over documents.

Simple, explainable scoring: for every word in the query, count how many times
it appears in the document. A match in the title counts more than one in the
body, because titles describe what a document is about.

This is the baseline. Later, the RAG project replaces it with BM25 plus
embedding (semantic) search, and we can measure whether that is really better.
"""
import re

from app.schemas import Document, SearchResult

TITLE_WEIGHT = 3.0
TAG_WEIGHT = 2.0

_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase text and split it into words: 'Reset Password!' -> ['reset', 'password']."""
    return _WORD.findall(text.lower())


def score_document(query_terms: list[str], doc: Document) -> float:
    title_words = tokenize(doc.title)
    body_words = tokenize(doc.content)
    tag_words = [w for tag in doc.tags for w in tokenize(tag)]

    score = 0.0
    for term in query_terms:
        score += TITLE_WEIGHT * title_words.count(term)
        score += TAG_WEIGHT * tag_words.count(term)
        score += body_words.count(term)
    return score


def search(query: str, docs: list[Document], limit: int = 10) -> list[SearchResult]:
    terms = tokenize(query)
    if not terms:
        return []
    results = [SearchResult(score=s, document=d) for d in docs if (s := score_document(terms, d)) > 0]
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
