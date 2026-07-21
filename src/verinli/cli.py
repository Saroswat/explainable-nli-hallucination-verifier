from pathlib import Path
from typing import Annotated

import typer

from verinli.ingestion import load_evidence_file
from verinli.pipeline import VerificationPipeline
from verinli.reporting import OutputFormat, render_report

app = typer.Typer(help="Verify generated claims against an evidence corpus.")


@app.callback()
def main() -> None:
    """Evidence-grounded natural language inference."""


@app.command()
def verify(
    answer: str,
    evidence_file: Path,
    output_format: Annotated[OutputFormat, typer.Option("--format")] = OutputFormat.JSON,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    top_k: Annotated[int, typer.Option(min=1, max=10)] = 3,
) -> None:
    """Verify ANSWER against JSONL, Markdown, or plain-text evidence."""
    try:
        passages = load_evidence_file(evidence_file)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    report = VerificationPipeline(passages, top_k=top_k).verify(answer)
    rendered = render_report(report, output_format)
    if output:
        output.write_text(rendered, encoding="utf-8")
        typer.echo(f"Saved {output_format.value.upper()} report to {output}")
    else:
        typer.echo(rendered)


if __name__ == "__main__":
    app()
