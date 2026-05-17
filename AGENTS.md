# AGENTS.md — jules-ph-worker

Jules reads this file to understand how to set up and operate this repository.

---

## What this repo does

**jules-ph-worker** is a daily Philippine news scraper and civic impact classifier.

Each run it:
1. Scrapes today's articles from 10 Philippine news and government outlets
2. Classifies each article using Gemini AI — category, sentiment, affected citizen archetypes, and politician impact ratings
3. Consolidates articles covering the same news event into a single topic entry
4. Commits the structured JSON output to the `data/` folder on `main`

The output is used by a gamified civic awareness platform that maps news to 35 citizen archetypes (Farmer, OFW, Driver, etc.) and tracks whether politicians help or hurt ordinary Filipinos over time.

---

## How to run

```bash
python main.py
```

To test without pushing to git:

```bash
python main.py --dry-run
```

**Do not modify any source files during a scheduled run.** Only `python main.py` should be executed.

---

## Dependencies

```bash
pip install -r requirements.txt
```

Requires Python 3.10+.

---

## Jules UI — one-time setup steps

Before creating the scheduled task, do this once:

In Jules → left sidebar → select this repo → **Configuration tab → Initial Setup**, enter:

```bash
pip install -r requirements.txt
```

Click **"Run and Snapshot"** to cache the environment for faster future runs.

---

## Scheduled task prompt (copy-paste this into Jules)

When creating the scheduled task, use this prompt exactly:

> **This is a data pipeline execution task, not a coding task. Do NOT run pytest. Do NOT do code review. Do NOT modify any source files. Do NOT create a new branch. Do NOT open a pull request. Stay on `main` for the entire task.**
>
> Execute this single command in the repository root and wait for it to finish:
>
> ```
> python main.py
> ```
>
> The script handles everything: scraping 10 Philippine news sources, classifying articles with Gemini AI, and committing structured JSON to the `data/` folder on `main`. It pushes to `main` automatically — no further action is needed from you.
>
> After `python main.py` completes, verify it succeeded by running:
>
> ```
> git log origin/main --oneline -3
> ```
>
> The top commit should be dated today and mention the number of topics (e.g., `data: 2026-05-17 — 34 topics`). If it is, the task is done.

**Frequency:** Daily · **Time:** midnight Philippine time (UTC+8 = 16:00 UTC)

---

## Output location

After a successful run, the `data/` folder on `main` contains:

```
data/
├── daily/YYYY-MM-DD.json       ← today's consolidated news topics
├── politicians/{slug}.json     ← cumulative impact profile per politician
└── sectors/{slug}.json         ← rolling 30-day news feed per citizen archetype
```

---

## AI credentials

On Jules' VM, the script uses **Vertex AI with Application Default Credentials** — no API key needed if the VM's service account has `roles/aiplatform.user`.

If ADC is unavailable, set `GEMINI_API_KEY` in the task environment and the script will fall back to the public Gemini API automatically.

---

## Troubleshooting a failed run

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Jules runs pytest / code review instead of the script | Jules misread the task as a coding task | Re-issue the task using the exact prompt above |
| Jules creates a new branch or PR | Jules ignored the no-branch instruction | Close the PR, delete the branch, re-issue the task |
| `0 articles` from Senate or Congress | Government site layout changed | Update CSS selectors in `scrapers/senate_gov.py` or `scrapers/congress_gov.py` |
| RSS scraper returns 0 articles | Feed URL moved | Update `FEED_URLS` in the relevant scraper file |
| Classification returns `None` for many articles | Gemini quota exceeded or ADC misconfigured | Check Vertex AI quota or set `GEMINI_API_KEY` |

---

## Files Jules must not modify

```
AGENTS.md
CLAUDE.md
main.py
requirements.txt
startup.sh
scrapers/
classifier/
models/
output/
```

Source files for the automated pipeline — changes here affect every future run.
