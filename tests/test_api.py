from fastapi.testclient import TestClient

from verinli.api import app

client = TestClient(app)


def test_home_serves_workbench() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "VeriNLI Workbench" in response.text


def test_health_endpoint() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_verify_endpoint_returns_explainable_report() -> None:
    response = client.post(
        "/verify",
        json={
            "answer": "Insulin regulates blood glucose.",
            "passages": [
                {
                    "passage_id": "bio-1",
                    "text": "Insulin regulates blood glucose.",
                    "source": "demo",
                }
            ],
        },
    )

    assert response.status_code == 200
    report = response.json()
    assert report["summary"]["entailment"] == 1
    assert report["verdicts"][0]["evidence"]["source"] == "demo"
    assert report["verdicts"][0]["citations"][0]["citation_id"] == "[1]"


def test_verify_endpoint_rejects_empty_evidence() -> None:
    response = client.post("/verify", json={"answer": "A valid claim.", "passages": []})
    assert response.status_code == 422


def test_ingest_endpoint_splits_plain_text() -> None:
    response = client.post(
        "/ingest",
        json={
            "text": "First evidence paragraph.\n\nSecond evidence paragraph.",
            "source": "notes.txt",
        },
    )
    assert response.status_code == 200
    assert [item["passage_id"] for item in response.json()] == ["text-001", "text-002"]
    assert response.json()[0]["source"] == "notes.txt"


def test_csv_endpoint_exports_claim_and_citations() -> None:
    response = client.post(
        "/verify.csv",
        json={
            "answer": "Insulin regulates blood glucose.",
            "passages": [
                {"passage_id": "bio-1", "text": "Insulin regulates blood glucose."}
            ],
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "citation_passage_ids" in response.text
    assert "bio-1" in response.text
