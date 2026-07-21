import csv
import io
from enum import StrEnum

from verinli.models import GroundednessReport


class OutputFormat(StrEnum):
    JSON = "json"
    CSV = "csv"


def report_to_json(report: GroundednessReport) -> str:
    return report.model_dump_json(indent=2)


def report_to_csv(report: GroundednessReport) -> str:
    """Flatten a groundedness report to one auditable row per claim."""
    output = io.StringIO(newline="")
    fieldnames = [
        "claim_number",
        "claim",
        "verdict",
        "nli_confidence",
        "requires_human_review",
        "review_reasons",
        "evidence_conflict",
        "primary_passage_id",
        "primary_source",
        "primary_retrieval_score",
        "citation_ids",
        "citation_passage_ids",
        "rationale",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for index, verdict in enumerate(report.verdicts, start=1):
        writer.writerow(
            {
                "claim_number": index,
                "claim": verdict.claim,
                "verdict": verdict.nli.label.value,
                "nli_confidence": f"{verdict.nli.confidence:.6f}",
                "requires_human_review": verdict.requires_human_review,
                "review_reasons": ";".join(verdict.review_reasons),
                "evidence_conflict": verdict.evidence_conflict,
                "primary_passage_id": verdict.evidence.passage_id if verdict.evidence else "",
                "primary_source": verdict.evidence.source if verdict.evidence else "",
                "primary_retrieval_score": (
                    f"{verdict.evidence.retrieval_score:.6f}" if verdict.evidence else ""
                ),
                "citation_ids": ";".join(item.citation_id for item in verdict.citations),
                "citation_passage_ids": ";".join(
                    item.evidence.passage_id for item in verdict.citations
                ),
                "rationale": verdict.nli.rationale,
            }
        )
    return output.getvalue()


def render_report(report: GroundednessReport, output_format: OutputFormat) -> str:
    if output_format is OutputFormat.CSV:
        return report_to_csv(report)
    return report_to_json(report)
