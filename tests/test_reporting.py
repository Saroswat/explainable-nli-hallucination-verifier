import csv
import io

from verinli.pipeline import VerificationPipeline
from verinli.reporting import report_to_csv
from verinli.retrieval import Passage


def test_csv_report_contains_auditable_citation_fields() -> None:
    report = VerificationPipeline(
        [Passage(passage_id="source-1", text="Insulin regulates blood glucose.")]
    ).verify("Insulin regulates blood glucose.")
    rows = list(csv.DictReader(io.StringIO(report_to_csv(report))))
    assert len(rows) == 1
    assert rows[0]["verdict"] == "entailment"
    assert rows[0]["primary_passage_id"] == "source-1"
    assert rows[0]["citation_ids"] == "[1]"
