# BüroKnakker

Germany bureaucracy, cracked. A city-aware checklist for expats, students, and international employees — in the right order, with deadlines, documents, costs, and official links.

## Problem

Newcomers to Germany miss deadlines and bring the wrong documents to the Bürgeramt, Ausländerbehörde, and health insurers. The information exists, but it is scattered across federal, state, and city websites, mostly in German.

## Solution

**BüroKnakker** takes a small profile (city, legal status, arrival date, family) and returns a personalized, ordered action plan:

- **Timeline** — what to do and by when, with a countdown
- **Checklist** — the exact documents for each step
- **City Info** — the correct Bürgeramt and Ausländerbehörde links per city
- **Export** — PDF checklist + `.ics` calendar with reminders

Bilingual (DE/EN). No accounts, no tracking, no data leaves the machine.

## Stack

- Python 3.11+
- Streamlit
- Pydantic (typed rule data)
- YAML (curated, versioned content)
- fpdf2 (PDF export)
- pytest

## Architecture

- `data/steps.yaml` — every bureaucratic step as structured data
- `data/cities/*.yaml` — city-specific offices and links
- `src/models.py` — Pydantic schemas
- `src/engine.py` — rule engine that resolves steps for a profile
- `src/i18n.py` — DE/EN strings
- `src/export.py` — PDF + ICS export
- `app.py` — Streamlit UI

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py ```

## Roadmap
More cities (Frankfurt, Stuttgart, Düsseldorf)

More statuses (refugee, posted worker, spouse of Blue Card holder)

Anmeldung appointment slot watcher

Localized PDF fonts (full Unicode)

Optional offline mode

## Why this project
Real problem, real users, real German context

Data-driven rule engine, not hardcoded ifs

Tested, typed, documented

Deployable on Streamlit Community Cloud
