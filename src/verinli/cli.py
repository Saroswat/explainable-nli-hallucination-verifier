import json
from pathlib import Path

import typer

from verinli.pipeline import VerificationPipeline
from verinli.retrieval import Passage

app = typer.Typer(help="Verify generated claims against an evidence corpus.")


@app.callback()
def main() -> None:
    """Evidence-grounded natural language inference."""


@app.command()
def verify(answer: str, evidence_file: Path) -> None:
    """Verify ANSWER against a JSONL evidence file."""
    if not evidence_file.is_file():
        raise typer.BadParameter(f"Evidence file not found: {evidence_file}")
    passages = [
        Passage(**json.loads(line))
        for line in evidence_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not passages:
        raise typer.BadParameter("The evidence file must contain at least one passage.")
    report = VerificationPipeline(passages).verify(answer)
    typer.echo(report.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
