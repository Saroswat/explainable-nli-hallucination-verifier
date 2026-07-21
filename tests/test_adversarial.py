import json
from pathlib import Path

import pytest

from verinli.models import NLILabel
from verinli.nli import HeuristicNLI

CASES = [
    json.loads(line)
    for line in (Path(__file__).parents[1] / "evaluation" / "adversarial_cases.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
]


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_adversarial_fixture(case: dict[str, str]) -> None:
    result = HeuristicNLI().predict(case["premise"], case["hypothesis"])
    assert result.label is NLILabel(case["label"])
    assert sum(result.probabilities.values()) == pytest.approx(1.0)
