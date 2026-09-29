from app.core.config import settings


def test_list_documents_returns_all_seeded_documents(client):
    response = client.get("/documents")
    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 2
    assert body["skip"] == 0
    assert body["limit"] == 10
    assert {item["id"] for item in body["items"]} == {101, 102}


def test_list_documents_respects_skip_and_limit(client):
    response = client.get("/documents", params={"skip": 1, "limit": 1})
    body = response.json()

    assert len(body["items"]) == 1
    assert body["total"] == 2
    assert body["skip"] == 1
    assert body["limit"] == 1


def test_list_documents_excludes_body(client):
    response = client.get("/documents")
    item = response.json()["items"][0]
    assert "body" not in item


def test_get_document_by_id_returns_full_detail_including_body(client):
    response = client.get("/documents/101")
    assert response.status_code == 200

    body = response.json()
    assert body["id"] == 101
    assert body["title"] == "Stale Grill SOP"
    assert body["body"] == "Body text for the stale SOP."


def test_get_document_unknown_id_returns_404(client):
    response = client.get("/documents/9999")
    assert response.status_code == 404


def test_stale_documents_excludes_fresh_ones(client):
    response = client.get("/documents/stale")
    assert response.status_code == 200

    ids = {item["id"] for item in response.json()}
    assert 101 in ids
    assert 102 not in ids


def test_stale_documents_respects_custom_threshold(client):
    # With a huge threshold, nothing should qualify as stale.
    response = client.get("/documents/stale", params={"threshold": 10_000})
    assert response.json() == []


def test_documents_require_api_key(client):
    response = client.get("/documents", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_documents_reject_missing_api_key(client):
    response = client.get("/documents", headers={"X-API-Key": ""})
    assert response.status_code == 401