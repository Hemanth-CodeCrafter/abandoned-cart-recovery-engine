# Abandoned Cart Recovery & Attribution Engine

## Overview

I built this project as an assignment to simulate an e-commerce abandoned-cart recovery and attribution system using Python, FastAPI, and deterministic synthetic data.

The project models customer consent, cart activity, campaign decisions, simulated message events, orders, and conversion attribution. I also implemented data-validation checks and reproducibility verification to assess the consistency and integrity of the generated datasets.

All records are synthetic. The project does not send real messages or require paid APIs, Docker, or cloud hosting.

## Features

- Deterministic synthetic-data generation using a configurable seed.
- Relational data generation across 11 entities.
- Consent-aware message eligibility and suppression.
- Rolling seven-day frequency-cap checks.
- Simulated campaign sends and message-event histories.
- Click-based order attribution.
- Four intentional, labelled data anomalies for validation.
- CSV, JSON, and SQL exports.
- Data-integrity validation and reproducibility checks.
- FastAPI endpoints for health checks, metrics, cart lookup, campaign decisions, and validation.
- Automated tests for core functionality and business rules.

## Technology Stack

- Python 3.11+
- FastAPI
- SQLite-compatible SQL
- CSV and JSON
- Pytest

## Project Setup

### Prerequisites

- Python 3.11 or later
- pip
- Windows PowerShell, macOS Terminal, or a Linux terminal

### Windows PowerShell

Create and activate a virtual environment, then install the dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Generate the starter dataset, validate it, and run the tests:

```powershell
python scripts/generate_data.py --scale starter --seed 20261022
python scripts/validate_data.py --scale starter
python -m pytest -q
```

Start the API server:

```powershell
uvicorn app.main:app --reload
```

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python scripts/generate_data.py --scale starter --seed 20261022
python scripts/validate_data.py --scale starter
python -m pytest -q

uvicorn app.main:app --reload
```

Once the server is running, I can inspect the API through:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

## Data Generation

I implemented two dataset scales for development and verification.

| Scale | Purpose | Cart count |
|---|---|---:|
| `starter` | Quick development and testing | 500 |
| `full` | Full-scale challenge dataset | 50,000 |

The full-scale configuration is designed to generate 20,000 base abandoned-cart candidates and 10,000 send attempts.

### Generate the starter dataset

```bash
python scripts/generate_data.py --scale starter --seed 20261022
```

### Generate the full dataset

```bash
python scripts/generate_data.py --scale full --seed 20261022
```

Using the same seed and configuration allows me to check whether the generated output is reproducible.

## Validation and Reproducibility

I included separate scripts to validate the generated data and compare outputs from repeated generation runs.

Validate the starter dataset:

```bash
python scripts/validate_data.py --scale starter
```

Validate the full dataset:

```bash
python scripts/validate_data.py --scale full
```

Check starter reproducibility:

```bash
python scripts/compare_reproducibility.py --scale starter --seed 20261022
```

Check full-scale reproducibility:

```bash
python scripts/compare_reproducibility.py --scale full --seed 20261022
```

Run the automated tests:

```bash
python -m pytest -q
```

During development, the recorded checks showed successful generation at both scales, no reported validation errors, four labelled anomaly warnings, reproducible output, and passing automated tests.

A successful validation does not mean the dataset contains no anomalies. The intentional anomalies are part of the assignment and are evaluated according to the implemented validation rules.

## Data Model

I structured the project around the following 11 entities:

1. Customer
2. Consent
3. Session
4. Cart
5. CartLine
6. Campaign
7. MessageTemplate
8. SendAttempt
9. SendEvent
10. Order
11. Attribution

The relationships connect customer activity, cart contents, consent history, campaign execution, message events, orders, and attribution records.

The generated data includes entity-level CSV and JSON files, consolidated records, SQL schema and seed data, a generation manifest, and a separate ground-truth file containing anomaly labels.

For detailed field definitions and relationships, see [`docs/data_dictionary.md`](docs/data_dictionary.md).

## Business Rules

### Cart abandonment

A cart is ineligible if it has been purchased or recovered. Otherwise, the abandonment check uses the cart status, last activity timestamp, and a default inactivity threshold of 24 hours.

### Consent enforcement

The latest effective consent for the relevant customer and communication channel determines eligibility at send time. The effective status must be `opt_in`.

### Frequency cap

The implemented baseline permits no more than three sent messages per customer and channel within a rolling seven-day window.

### Conversion attribution

Attribution requires a qualifying click associated with a sent message and the same customer as the order. The click must occur before the order and within the seven-day attribution window. The baseline logic selects the earliest qualifying click.

These are assignment-specific assumptions rather than a complete production marketing-compliance implementation.

## API Reference

After starting the server, the following endpoints are available:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Checks API health. |
| `GET` | `/metrics` | Returns dataset metrics. |
| `GET` | `/carts/{cart_id}` | Retrieves a cart, its lines, and associated send attempts. |
| `GET` | `/campaign-decisions?limit=100` | Retrieves campaign send decisions, with a configurable limit. |
| `POST` | `/validate` | Returns validation results for the loaded dataset. |

The cart endpoint returns HTTP 404 when the requested cart ID does not exist.

The interactive documentation at `/docs` provides a convenient way to try the endpoints.

## Intentional Data Anomalies

I included four labelled anomaly categories to test the validation process:

1. A message sent after opt-out.
2. A cart marked abandoned after purchase.
3. An order attributed more than once.
4. A stale cart total after a quantity update.

These cases help demonstrate how data-quality problems can be detected. The ground-truth labels are maintained separately from the normal data and are intended for evaluation.

## Assumptions and Limitations

- All generated records are synthetic.
- Message sends and customer engagement events are simulated.
- The abandonment threshold, consent policy, frequency cap, and attribution window are configurable or defined by the implemented challenge rules.
- The API exposes the implemented functionality rather than a complete e-commerce platform.
- The system is a challenge implementation, not a production-ready marketing service.
- Full-scale generation can require additional disk space and processing time.
- Validation covers the checks implemented in the project; it does not prove that every possible edge case is handled.

## AI Assistance and My Contribution

I developed this project with substantial assistance from ChatGPT. I used it to understand the assignment, plan the implementation, generate and modify code, implement business rules, develop tests, troubleshoot issues, and improve the documentation.

I applied the suggested changes to my project and ran the implementation locally. I used dataset generation, validation, reproducibility checks, automated tests, and SQLite integrity checks to assess the results.

ChatGPT generated substantial portions of the code, and I acknowledge that contribution. I am responsible for reviewing the submitted project, understanding its implementation, explaining its design decisions, and being transparent about its limitations.

The [`PROMPT_HISTORY.md`](PROMPT_HISTORY.md) file documents my ChatGPT-assisted development process.

## Additional Documentation

- [`PROMPT_HISTORY.md`](PROMPT_HISTORY.md) — Prompt history and AI assistance disclosure.
- [`docs/data_dictionary.md`](docs/data_dictionary.md) — Entity definitions, fields, and relationships.