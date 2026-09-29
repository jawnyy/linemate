def test_list_tickets_returns_all_seeded_tickets(client):
    response = client.get("/tickets")
    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 3
    assert {item["id"] for item in body["items"]} == {201, 202, 203}


def test_list_tickets_respects_skip_and_limit(client):
    response = client.get("/tickets", params={"skip": 0, "limit": 2})
    body = response.json()

    assert len(body["items"]) == 2
    assert body["total"] == 3


def test_get_ticket_by_id(client):
    response = client.get("/tickets/201")
    assert response.status_code == 200

    body = response.json()
    assert body["id"] == 201
    assert body["assignee_id"] == 2
    assert body["related_document_id"] == 101


def test_get_ticket_unknown_id_returns_404(client):
    response = client.get("/tickets/9999")
    assert response.status_code == 404


def test_station_mismatches_flags_only_the_true_mismatch(client):
    response = client.get("/tickets/mismatches")
    assert response.status_code == 200

    mismatches = response.json()
    assert len(mismatches) == 1

    mismatch = mismatches[0]
    assert mismatch["ticket_id"] == 201
    assert mismatch["document_id"] == 101
    assert mismatch["assignee_station"] == "Pastry"
    assert mismatch["owner_station"] == "Grill"


def test_station_mismatches_excludes_closed_tickets(client):
    # ticket 203 is CLOSED and has no related_document_id, so it must never appear
    response = client.get("/tickets/mismatches")
    ticket_ids = {m["ticket_id"] for m in response.json()}
    assert 203 not in ticket_ids


def test_tickets_require_api_key(client):
    response = client.get("/tickets", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401