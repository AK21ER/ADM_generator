# ADM Generator

ADM Generator is a Python 3.11+ pipeline that produces a complete Account Development Master (ADM) consulting report as one self-contained HTML file.

It automates a 12-section workflow, persists prompts/responses/fragments for debugging, and guarantees all financial values are deterministic code outputs (never AI-invented).

## Project Overview

- Input: structured client JSON (`data/<client>.json`)
- Processing:
  - Pydantic validation (`src/models.py`)
  - Deterministic financial/roadmap/matrix/benchmark computations (`src/financials.py`)
  - 12 sequential section generations with retry and persistence (`src/generator.py`)
  - Jinja2 rendering into offline single-file HTML (`src/templates/base.html.j2`)
- Output:
  - final report HTML in `output/`
  - per-section prompt, raw response, and section fragment artifacts

## Install Instructions

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

## Set `OPENAI_API_KEY`

1. Copy `.env.example` to `.env`
2. Set:
   - `OPENAI_API_KEY=<your key>`
   - optional: `OPENAI_MODEL=<model>`
   - optional: `DISCOUNT_RATE=<float>`

If no key is set, the pipeline still generates a complete report in offline fallback mode.

## Run Pipeline

```bash
python -m src.main --client data/fictional_client.json --output output/fictional_client_ADM.html
```

Flags:
- `--force` regenerates section files even if they exist
- `--model` overrides model from `.env`
- `--debug` enables verbose logs

## Add a New Client JSON

1. Copy `data/fictional_client.json` to `data/<new_client>.json`
2. Update fields per schema in `src/models.py`
3. Run:

```bash
python -m src.main --client data/<new_client>.json --output output/<new_client>_ADM.html
```

## Financial Assumptions

- Savings rates by modernization recommendation:
  - Retire 90%
  - Retain 5%
  - Rehost 15%
  - Replatform 30%
  - Refactor 45%
  - Rearchitect 60%
- Savings ramp:
  - Y1 10%, Y2 25%, Y3 50%, Y4 75%, Y5 100%
- Investment distribution:
  - Y1 30%, Y2 25%, Y3 20%, Y4 15%, Y5 10%
- Default discount rate:
  - 10%

## Persistence and Retry Behavior

For each section (`01` to `12`) the pipeline writes:
- `output/prompts/section_XX_prompt.txt`
- `output/raw_responses/section_XX_raw.txt`
- `output/sections/section_XX_<section-id>.html`

Behavior:
- Existing section fragments are reused unless `--force` is passed
- OpenAI calls retry up to 5 times with exponential backoff (tenacity)
- If generation fails after retries, execution stops with all previously generated artifacts preserved

## Optional Master Prompt Support

If `data/master_prompt.txt` exists and is non-empty, it is automatically prepended to every section prompt.

## Cisco Template Reference Note

- Keep `templates/reference/Cisco_ADM.html` as your unchanged visual reference baseline.
- Runtime rendering uses `src/templates/base.html.j2` and is fully offline (no CDN, no external assets).
