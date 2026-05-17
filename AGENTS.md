# AGENTS.md — jules-ph-worker

Jules reads this file to understand how to set up and operate this repository.

---

## What this repo does

**jules-ph-worker** is a daily Philippine news scraper and civic impact classifier.

Each run it:
1. Scrapes today's articles from 10 Philippine news and government outlets
2. Classifies each article using Gemini AI — category, sentiment, affected citizen archetypes, and politician impact ratings
3. Consolidates articles covering the same news event into a single topic entry
4. Pushes the structured JSON output to the `data` branch of this repository

The output is used by a gamified civic awareness platform that maps news to 35 citizen archetypes (Farmer, OFW, Driver, etc.) and tracks whether politicians help or hurt ordinary Filipinos over time.

---

## How to run

```bash
python main.py
```

To test without pushing to the `data` branch:

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

Before creating the scheduled task, do these once:

### 1. Initial Setup script (Configuration tab)

In Jules → left sidebar → select this repo → **Configuration tab → Initial Setup**, enter:

```bash
pip install -r requirements.txt
```

Click **"Run and Snapshot"** to cache the environment for faster future runs.

### 2. Bootstrap the `data` branch (run once locally or in a one-off Jules task)

The `data` branch must exist before the scheduled task runs. Create it with:

```bash
bash startup.sh
```

This is a one-time step. After the branch exists, subsequent runs only need `python main.py`.

---

## Scheduled task prompt (copy-paste this into Jules)

When creating the scheduled task, use this prompt exactly:

> **This is a data pipeline execution task, not a coding task. Do NOT run pytest. Do NOT do code review. Do NOT modify any source files.**
>
> Execute this single command in the repository root and wait for it to finish:
>
> ```
> python main.py
> ```
>
> The script handles everything: scraping 10 Philippine news sources, classifying articles with Gemini AI, and pushing structured JSON to the `data` branch. It will print progress and push to git automatically — no further action is needed from you.
>
> After `python main.py` completes, verify it succeeded by running:
>
> ```
> git fetch origin data && git log origin/data --oneline -3
> ```
>
> The top commit should be dated today and mention the number of topics (e.g., `data: 2026-05-17 — 34 topics`). If it is, the task is done.

**Frequency:** Daily · **Time:** midnight Philippine time (UTC+8 = 16:00 UTC)

---

## Output location

After a successful run, the `data` branch contains:

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
| Jules runs pytest / code review instead of the script | Jules misread the task as a coding task | Re-issue the task using the exact prompt above; it must start with "This is a data pipeline execution task, not a coding task." |
| `0 articles` from Senate or Congress | Government site layout changed | Update CSS selectors in `scrapers/senate_gov.py` or `scrapers/congress_gov.py` |
| RSS scraper returns 0 articles | Feed URL moved | Update `FEED_URLS` in the relevant scraper file |
| `data` branch not found | Branch not bootstrapped | Run `bash startup.sh` once |
| Classification returns `None` for many articles | Gemini quota exceeded or ADC misconfigured | Check Vertex AI quota or set `GEMINI_API_KEY` |
| `_data_wt` directory error | Previous run crashed mid-write | Run `git worktree prune` then retry |

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
