"""Tests for health and the document CRUD endpoints."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_document_returns_201_and_server_fields(client):
    response = client.post(
        "/documents",
        json={"title": "Refund policy", "content": "Refunds within 30 days.", "tags": ["billing"]},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Refund policy"
    assert body["tags"] == ["billing"]
    assert "created_at" in body and "updated_at" in body


def test_create_document_tags_default_to_empty_list(client):
    response = client.post("/documents", json={"title": "A", "content": "B"})
    assert response.status_code == 201
    assert response.json()["tags"] == []


def test_ids_increase(client, make_doc):
    assert make_doc()["id"] == 1
    assert make_doc()["id"] == 2


def test_create_rejects_empty_title(client):
    response = client.post("/documents", json={"title": "", "content": "text"})
    assert response.status_code == 422


def test_create_rejects_missing_content(client):
    response = client.post("/documents", json={"title": "Only title"})
    assert response.status_code == 422


def test_create_rejects_too_long_title(client):
    response = client.post("/documents", json={"title": "x" * 201, "content": "text"})
    assert response.status_code == 422


def test_get_document(client, make_doc):
    created = make_doc(title="Shipping times")
    response = client.get(f"/documents/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Shipping times"


def test_get_missing_document_returns_404(client):
    response = client.get("/documents/999")
    assert response.status_code == 404
    assert "999" in response.json()["detail"]


def test_get_document_with_non_integer_id_returns_422(client):
    assert client.get("/documents/abc").status_code == 422


def test_list_documents(client, make_doc):
    make_doc(title="One")
    make_doc(title="Two")
    response = client.get("/documents")
    assert response.status_code == 200
    assert [d["title"] for d in response.json()] == ["One", "Two"]


def test_list_filters_by_tag_case_insensitively(client, make_doc):
    make_doc(title="Billing doc", tags=["Billing"])
    make_doc(title="Other doc", tags=["shipping"])
    response = client.get("/documents", params={"tag": "billing"})
    assert [d["title"] for d in response.json()] == ["Billing doc"]


def test_list_pagination(client, make_doc):
    for i in range(5):
        make_doc(title=f"Doc {i}")
    response = client.get("/documents", params={"skip": 2, "limit": 2})
    assert [d["title"] for d in response.json()] == ["Doc 2", "Doc 3"]


def test_list_rejects_invalid_limit(client):
    assert client.get("/documents", params={"limit": 0}).status_code == 422
    assert client.get("/documents", params={"limit": 101}).status_code == 422


def test_update_document(client, make_doc):
    created = make_doc(title="Old title")
    response = client.put(
        f"/documents/{created['id']}",
        json={"title": "New title", "content": "New content", "tags": ["x"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New title"
    assert body["id"] == created["id"]
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] >= created["updated_at"]


def test_update_missing_document_returns_404(client):
    response = client.put("/documents/42", json={"title": "A", "content": "B"})
    assert response.status_code == 404


def test_delete_document(client, make_doc):
    created = make_doc()
    assert client.delete(f"/documents/{created['id']}").status_code == 204
    assert client.get(f"/documents/{created['id']}").status_code == 404


def test_delete_missing_document_returns_404(client):
    assert client.delete("/documents/42").status_code == 404
