# jules-ph-worker

Philippine news scraper and civic impact classifier, designed to be run daily by Google Jules on GCP.

## What It Does

1. **Scrapes** today's articles from 9 Philippine news and government sources
2. **Classifies** each article using Google Gemini — category, sentiment, affected citizen archetypes, and politician impact ratings
3. **Writes** structured JSON to the `data/` folder on the `main` branch

The output powers a gamified civic awareness system where every news event maps to citizen archetypes (Farmer, OFW, Driver, etc.) and tracks whether politicians are helping or hurting ordinary Filipinos over time.

---

## Running the Scraper

```bash
pip install -r requirements.txt
python main.py            # full run: scrape → classify → commit to data/ on main
python main.py --dry-run  # prints JSON to stdout, no git push (safe for testing)
```

For first-time setup, run `bash startup.sh` once to install dependencies before attaching to Jules.
After that, Jules' daily scheduled task runs `python main.py` directly — see `AGENTS.md` for the exact Jules UI configuration steps.

---

## Credentials

**On Jules' VM — zero config required.**

| What | How Jules provides it |
|------|-----------------------|
| AI classification | Vertex AI via Application Default Credentials (VM service account) |
| Git push to `main` | Existing repository credentials in the Jules VM |

**For local development**, copy `.env.example` to `.env` and fill in either:
- `GOOGLE_CLOUD_PROJECT` + `gcloud auth application-default login` (Vertex AI / ADC), or
- `GEMINI_API_KEY` (direct Gemini API fallback)

---

## Data Output (`data/` folder on `main`)

```
data/
├── daily/
│   └── YYYY-MM-DD.json       # Full daily digest: all articles + classifications
├── politicians/
│   └── {slug}.json           # Cumulative impact profile per politician
└── sectors/
    └── {slug}.json           # Last ~30 days of articles per citizen archetype
```

### Daily JSON shape

Articles from different outlets covering the same event are merged into a single **topic** entry. `raw_article_count` is the total scraped; `topic_count` is the deduplicated output.

```json
{
  "date": "2026-05-17",
  "scraped_at": "2026-05-17T16:00:00Z",
  "raw_article_count": 87,
  "topic_count": 34,
  "topics": [
    {
      "id": "uuid",
      "topic": "Senate Passes Anti-ENDO Bill on Third Reading",
      "sources": [
        { "source": "gma_news",        "url": "https://...", "title": "Senate OKs security of tenure bill", "published_at": "2026-05-17T09:00:00+08:00" },
        { "source": "inquirer",        "url": "https://...", "title": "Anti-ENDO bill hurdles Senate", "published_at": "2026-05-17T09:15:00+08:00" },
        { "source": "philippine_star", "url": "https://...", "title": "Senators approve job security measure", "published_at": "2026-05-17T09:30:00+08:00" }
      ],
      "summary": "The Philippine Senate approved on third and final reading...",
      "classification": {
        "category": "politics",
        "sentiment": "positive",
        "impact_level": "national",
        "affected_sectors": ["labor_worker", "kasambahay", "retail_worker", "bpo_worker"],
        "politicians": [
          {
            "name": "Joel Villanueva",
            "position": "Senator",
            "party": "Independent",
            "impact": "positive",
            "reason": "Authored and championed the security of tenure bill for workers."
          }
        ],
        "gamification": {
          "event_type": "law_passed",
          "severity": 4,
          "affected_population_estimate": "majority"
        }
      }
    }
  ]
}
```

---

## Citizen Archetypes (Sector Slugs)

These are the 35 citizen base classes used in gamification. Each news event can affect one or more.

### Agriculture & Natural Resources
| Slug | Label |
|------|-------|
| `farmer` | Farmer |
| `fisherman` | Fisherman |
| `miner` | Miner |
| `forest_worker` | Forest Worker |

### Health & Social Services
| Slug | Label |
|------|-------|
| `health_worker` | Health Worker |
| `social_worker` | Social Worker |
| `senior_citizen` | Senior Citizen |
| `pwd` | Person with Disability |

### Education
| Slug | Label |
|------|-------|
| `teacher` | Teacher |
| `student` | Student |

### Labor & Employment
| Slug | Label |
|------|-------|
| `labor_worker` | Labor Worker |
| `kasambahay` | Kasambahay |
| `security_guard` | Security Guard |
| `bpo_worker` | BPO / Call Center Worker |
| `retail_worker` | Retail Worker |
| `hospitality_worker` | Hospitality Worker |

### Transport & Logistics
| Slug | Label |
|------|-------|
| `driver` | Driver |
| `seafarer` | Seafarer |
| `delivery_rider` | Delivery Rider |

### Business & Economy
| Slug | Label |
|------|-------|
| `business_owner` | Business Owner |
| `vendor` | Vendor / Tindera |
| `freelancer` | Freelancer |

### Overseas Workers
| Slug | Label |
|------|-------|
| `ofw` | OFW |

### Government & Public Service
| Slug | Label |
|------|-------|
| `government_employee` | Gov't Employee |
| `barangay_official` | Barangay Official |
| `military_police` | Military / Police |

### Professionals
| Slug | Label |
|------|-------|
| `engineer_architect` | Engineer / Architect |
| `lawyer` | Lawyer |
| `journalist` | Journalist |
| `it_tech_worker` | IT / Tech Worker |
| `artist_creative` | Artist / Creative |

### Vulnerable & Marginalized Groups
| Slug | Label |
|------|-------|
| `solo_parent` | Solo Parent |
| `informal_settler` | Informal Settler |
| `indigenous_people` | Indigenous People |
| `youth` | Youth / NEET |
| `lgbtq` | LGBTQ+ |
| `prisoner_returnee` | Prisoner / Returnee |

---

## News Sources

| Source | Type | What Is Scraped |
|--------|------|-----------------|
| GMA News | RSS | Top stories, nation, economy |
| ABS-CBN News | RSS | News headlines |
| CNN Philippines | RSS | Headlines |
| Philippine Daily Inquirer | RSS | Top stories, news |
| Philippine Star | RSS | Headlines, nation |
| Manila Bulletin | RSS | Latest headlines |
| Rappler | RSS | Nation, business, accountability journalism |
| Senate of the Philippines | HTML | Press releases, bills filed |
| House of Representatives | HTML | News releases |
| Official Gazette | RSS | Executive orders, proclamations |

---

## Adding a New Scraper

### RSS source (preferred)

1. Create `scrapers/your_source.py`:

```python
from scrapers.base import RSSBaseScraper

class YourSourceScraper(RSSBaseScraper):
    SOURCE_NAME = "your_source"
    FEED_URLS = [
        "https://yoursource.com/feed/",
        "https://yoursource.com/category/news/feed/",
    ]
```

2. Register in `scrapers/__init__.py`:

```python
from .your_source import YourSourceScraper

ALL_SCRAPERS = [..., YourSourceScraper]
```

### HTML source

Extend `HTMLBaseScraper` and implement `fetch()`. Use `self._get(url)` which returns a `BeautifulSoup` object. Return a list of `RawArticle` objects.

---

## Classifier

Articles are classified in batches of 10 using **Gemini 1.5 Flash** (`gemini-1.5-flash`).

Each classification returns:
- `category` — politics, economy, health, weather, crime, education, environment, disaster, international, sports, technology, or social
- `sentiment` — positive / negative / neutral (from Filipino citizens' perspective)
- `impact_level` — national / regional / local
- `affected_sectors` — list of sector slugs from the 35-archetype list
- `politicians` — list of mentioned politicians with impact rating and one-sentence reason
- `gamification` — event type, severity (1–5), and affected population estimate

The model is called with `response_mime_type="application/json"` for reliable structured output.

---

## Politician Profiles

Each politician mentioned across all articles accumulates an impact history in `data/politicians/{slug}.json`:

```json
{
  "slug": "juan-dela-cruz",
  "name": "Juan Dela Cruz",
  "position": "Senator",
  "party": "PDP-Laban",
  "branch": "legislative",
  "positive_count": 12,
  "negative_count": 5,
  "neutral_count": 3,
  "impact_score": 0.35,
  "last_updated": "2026-05-17T16:00:00Z",
  "impact_history": [...]
}
```

`impact_score` = (positive − negative) / total, ranging from −1.0 to +1.0.

---

## Schedule

Jules runs this script daily at **midnight Philippine time (UTC+8 = 16:00 UTC)**.

Reference cron expression: `0 16 * * *`
