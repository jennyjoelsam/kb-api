"""Tests for tokenizing, scoring and the /search endpoint."""
from app.search import tokenize


def test_tokenize_lowercases_and_strips_punctuation():
    assert tokenize("Reset Password!") == ["reset", "password"]


def test_tokenize_empty_and_symbols_only():
    assert tokenize("") == []
    assert tokenize("!!! ???") == []


def test_search_finds_matching_document(client, make_doc):
    make_doc(title="Refund policy", content="Refunds are issued within 30 days.")
    make_doc(title="Shipping", content="Orders ship in 2 days.")
    response = client.get("/search", params={"q": "refunds"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["document"]["title"] == "Refund policy"
    assert results[0]["score"] > 0


def test_search_is_case_insensitive(client, make_doc):
    make_doc(title="Password reset", content="Use the forgot link.")
    assert len(client.get("/search", params={"q": "PASSWORD"}).json()) == 1


def test_title_match_ranks_above_body_match(client, make_doc):
    make_doc(title="Shipping", content="Contact support about refund questions.")
    make_doc(title="Refund policy", content="Details below.")
    results = client.get("/search", params={"q": "refund"}).json()
    assert [r["document"]["title"] for r in results] == ["Refund policy", "Shipping"]
    assert results[0]["score"] > results[1]["score"]


def test_tag_match_counts(client, make_doc):
    make_doc(title="Misc", content="Nothing relevant.", tags=["billing"])
    assert len(client.get("/search", params={"q": "billing"}).json()) == 1


def test_search_with_no_match_returns_empty_list(client, make_doc):
    make_doc()
    response = client.get("/search", params={"q": "zebra"})
    assert response.status_code == 200
    assert response.json() == []


def test_search_query_of_only_symbols_returns_empty_list(client, make_doc):
    make_doc()
    assert client.get("/search", params={"q": "!!!"}).json() == []


def test_search_requires_q(client):
    assert client.get("/search").status_code == 422


def test_search_respects_limit(client, make_doc):
    for i in range(5):
        make_doc(title=f"Refund {i}")
    assert len(client.get("/search", params={"q": "refund", "limit": 3}).json()) == 3


def test_deleted_document_no_longer_found(client, make_doc):
    doc = make_doc(title="Temporary refund note")
    client.delete(f"/documents/{doc['id']}")
    assert client.get("/search", params={"q": "refund"}).json() == []
