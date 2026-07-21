# VeriNLI - Explainable Hallucination Verification

[![CI](https://github.com/Saroswat/explainable-nli-hallucination-verifier/actions/workflows/ci.yml/badge.svg)](https://github.com/Saroswat/explainable-nli-hallucination-verifier/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-43d6c5.svg)](LICENSE)

VeriNLI checks an AI-generated answer against a supplied evidence corpus. It splits the
answer into claims, retrieves the strongest matching passage, classifies the relationship,
and explains which claims are supported, contradicted, uncertain, or require human review.

Everything runs locally. The default verifier does not send answers or evidence to an
external AI service.

## Run the local app on Windows

### Prerequisites

- [Git](https://git-scm.com/download/win)
- [Python 3.11 or newer](https://www.python.org/downloads/windows/)

When installing Python, enable **Add python.exe to PATH**.

### One-command launch

Open PowerShell and run:

```powershell
git clone https://github.com/Saroswat/explainable-nli-hallucination-verifier.git
cd explainable-nli-hallucination-verifier
.\run.ps1
```

If you are using Command Prompt instead, run `run.cmd` after entering the repository.
You can also double-click `run.cmd` in File Explorer.

The launcher automatically:

1. finds a compatible Python installation;
2. creates an isolated `.venv` environment;
3. installs the API and web-app dependencies;
4. starts VeriNLI only on `127.0.0.1`;
5. checks that the service is healthy;
6. opens [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

The first run downloads Python packages. Later launches reuse the environment and start
much faster. Press `Ctrl+C` in the launcher window to stop the server.

### Launcher options

```powershell
# Use another port
.\run.ps1 -Port 8080

# Start without opening a browser
.\run.ps1 -NoBrowser

# Reinstall dependencies
.\run.ps1 -Reinstall
```

## Using the workbench

1. Enter the answer or statement you want to inspect.
2. Add evidence as JSON Lines: one JSON object per line.
3. Select **Verify claims**.
4. Review the groundedness score and every claim-level verdict.

Each evidence line needs `passage_id` and `text`; `source` is optional:

```json
{"passage_id":"bio-001","text":"BRCA1 pathogenic variants increase breast cancer risk.","source":"example-guideline"}
{"passage_id":"bio-002","text":"Metformin is commonly used for type 2 diabetes.","source":"example-guideline"}
```

The browser interface includes a safe sample so you can see the full workflow immediately.

## What the report means

| Verdict | Meaning | Human review |
| --- | --- | --- |
| `entailment` | The selected evidence supports the claim. | Usually not required |
| `contradiction` | Evidence conflicts through negation or numerical values. | Required |
| `neutral` | Evidence neither proves nor directly contradicts the claim. | Not automatically required |
| `abstain` | Retrieval relevance or NLI confidence is below the safety threshold. | Required |

Every claim verdict includes:

- the atomic claim;
- the selected evidence passage and source;
- retrieval relevance and NLI confidence;
- class probabilities;
- a human-readable rationale;
- review status and reasons.

The answer-level report includes groundedness, contradiction rate, label counts, and an
overall review flag.

## How it works

```mermaid
flowchart LR
    A["Generated answer"] --> B["Atomic claim splitter"]
    B --> C["Lexical evidence retrieval"]
    C --> D["Premise and hypothesis pair"]
    D --> E["Explainable NLI classifier"]
    E --> F["Confidence and abstention policy"]
    F --> G["Groundedness report"]
    F --> H["Human review queue"]
```

The default NLI engine is a transparent, deterministic baseline. It is deliberately easy to
audit and works offline. The package also contains an optional Hugging Face transformer
backend for research experiments.

## API usage

While the local app is running:

- interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- verification endpoint: `POST http://127.0.0.1:8000/verify`

Example request:

```powershell
$body = @{
    answer = "Insulin regulates blood glucose."
    passages = @(
        @{
            passage_id = "bio-1"
            text = "Insulin regulates blood glucose."
            source = "demo"
        }
    )
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/verify" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

## Command-line usage

After `run.ps1` has prepared the environment:

```powershell
.\.venv\Scripts\verinli.exe verify `
    "BRCA1 pathogenic variants do not increase breast cancer risk." `
    ".\examples\evidence.jsonl"
```

The CLI prints a structured JSON report suitable for scripts and evaluation pipelines.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"

ruff check .
mypy
pytest
```

CI runs linting, strict type checking, unit tests, API tests, and coverage on every push and
pull request.

### Project structure

```text
.
|-- run.ps1                 # One-command Windows launcher
|-- run.cmd                 # Command Prompt and double-click wrapper
|-- examples/               # Sample evidence corpus
|-- evaluation/             # Adversarial evaluation fixtures
|-- src/verinli/
|   |-- api.py              # FastAPI and browser workbench
|   |-- claims.py           # Atomic claim decomposition
|   |-- retrieval.py        # Evidence retrieval
|   |-- nli.py              # Heuristic and transformer backends
|   |-- calibration.py      # Confidence and abstention policy
|   |-- pipeline.py         # End-to-end orchestration
|   `-- web/index.html      # Dependency-free local interface
`-- tests/                  # Unit and API tests
```

## Troubleshooting

### PowerShell says scripts are disabled

Use the included Command Prompt wrapper:

```cmd
run.cmd
```

It changes the execution policy only for that launcher process and does not modify your
machine-wide PowerShell policy.

### Python is not found

Install Python 3.11+ and select **Add python.exe to PATH**, then open a new terminal. Check:

```powershell
python --version
```

### Port 8000 is already in use

```powershell
.\run.ps1 -Port 8080
```

### Dependencies changed or the environment is stale

```powershell
.\run.ps1 -Reinstall
```

## Limitations and safety

VeriNLI is a research and portfolio project, not a fact oracle or clinical decision system.
The lexical retriever and heuristic NLI model are interpretable baselines and can miss
paraphrases, implicit facts, entity substitutions, and complex reasoning. Treat an
`entailment` verdict as model output, not a guarantee of truth.

Biomedical outputs must be reviewed by qualified humans. An `abstain` result means the
system lacks confidence; it does not mean a claim is safe.

## Roadmap

- hybrid BM25 and dense retrieval with reranking;
- calibrated transformer and biomedical NLI backends;
- dataset adapters and reproducible evaluation commands;
- biomedical entity linking and claim normalization;
- persisted reviewer decisions and disagreement metrics;
- adversarial generation for negation, numbers, entities, and time;
- observability and a dedicated review dashboard.

## License

[MIT](LICENSE). Third-party models and datasets retain their own licences and terms.
