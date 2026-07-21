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


def test_verify_endpoint_rejects_empty_evidence() -> None:
    response = client.post("/verify", json={"answer": "A valid claim.", "passages": []})
    assert response.status_code == 422
