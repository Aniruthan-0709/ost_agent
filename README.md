# OST Agent — Match Validation Agent

> Part of the **LG Agent Initiative** — an internal multi-agent platform automating sales operations across Public Sector, Healthcare, and Facilities verticals.

---

## What It Does

When a new sales initiative starts, incoming customer records from GPOs or third-party sources are run through an internal NLP/fuzzy matching process. That process returns a suggested match from our internal system — but it makes mistakes.

The OST Agent reviews each match result and issues a verdict, replacing what would otherwise be manual analyst review.

| Verdict | Meaning |
|---|---|
| `CONFIRM_MATCH` | Process got it right — same entity, valid relationship |
| `REJECT_MATCH` | Process got it wrong — wrong entity, wrong address, or invalid master |
| `GREYSPACE` | Right company, location we don't yet serve — expansion opportunity |
| `NEEDS_REVIEW` | Genuinely ambiguous — escalate to human analyst |
| `NO_MATCH_REVIEW` | Process returned no match — bypassed to human for manual verification |

---

## How Records Flow

```
Incoming Records (GPO / 3P)
        ↓
Internal NLP/Fuzzy Matching Process
        ↓
Process Output (Dataset 3)
        ↓
    loader.py
   ↙         ↘
Null match?   Has a match?
↓                  ↓
NO_MATCH_REVIEW   agent.py → Claude
(bypass)               ↓
        ↘         verdict
         output/results.csv
```

Null-matched records are bypassed before the agent runs — no API call, no decision, straight to human review. The agent only reasons about records where the process returned something.

---

## Reasoning Logic

For every record the agent receives, it works through five steps in order:

1. **Master relationship** — does the matched record legitimately roll up to the Master shown?
2. **Entity check** — same organization? Co-location and sub-tenant traps are caught here.
3. **Greyspace check** — same company but different location? Flag as expansion opportunity.
4. **Address variation** — is the address difference formatting noise or a genuinely different location?
5. **Needs review** — only escalates when a human analyst would also be uncertain.

---

## Performance (30-record synthetic eval)

| Metric | Score |
|---|---|
| Overall Accuracy | 85% (23/27 active rows) |
| Correct Match Detection | 100% |
| False Positive Rejection | 100% |
| Greyspace Detection | 67% |
| Error Detection F1 | 90% |

*3 rows excluded — hierarchy-level scenarios outside this agent's scope.*

---

## Repo Structure

```
ost_agent/
├── agent.py          # Main loop — runs Claude on matched records, writes output
├── prompt.py         # System prompt and verdict tool schema
├── loader.py         # Pre-filters null-match rows before agent run
├── evaluate.py       # Scores agent output against ground truth
├── data/
│   ├── dataset1_incoming_records.csv   # Incoming GPO/3P records
│   ├── dataset2_system_records.csv     # Internal system master data
│   ├── dataset3_process_output.csv     # NLP/fuzzy process output — agent input
│   └── dataset4_ground_truth.csv       # Answer key — evaluation only
├── output/
│   └── results.csv                     # Agent verdicts
├── prompts/                            # Prompt iteration history
├── pyproject.toml
└── uv.lock
```

---

## Setup & Usage

```bash
git clone https://github.com/Aniruthan-0709/ost_agent.git
cd ost_agent
uv sync
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

```bash
uv run agent.py      # Run the agent
uv run evaluate.py   # Score results against ground truth
```

---

## Tech Stack

- **Model** — Claude (Anthropic) via Python SDK, structured tool use
- **Language** — Python, managed with `uv`
- **Deployment target** — Databricks (LG Initiative platform)