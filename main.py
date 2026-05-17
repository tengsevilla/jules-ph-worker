"""
Entrypoint for the jules-ph-worker scraper pipeline.

On Jules' VM: runs zero-config — Vertex AI ADC and existing git credentials
are used automatically.

Usage:
    python main.py            # full run: scrape → classify → consolidate → push
    python main.py --dry-run  # print digest JSON to stdout, no git push
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

from scrapers import ALL_SCRAPERS
from scrapers.base import RawArticle
from classifier.gemini_client import GeminiClassifier
from classifier.consolidator import TopicConsolidator, article_to_consolidated
from models.article import DailyDigest
from output.writer import DataWriter

PH_TZ = timezone(timedelta(hours=8))


def scrape_all() -> list[RawArticle]:
    raw: list[RawArticle] = []
    seen_urls: set[str] = set()

    for ScraperClass in ALL_SCRAPERS:
        try:
            with ScraperClass() as scraper:
                articles = scraper.fetch()
                new = [a for a in articles if a.url not in seen_urls]
                seen_urls.update(a.url for a in new)
                raw.extend(new)
                print(f"  {ScraperClass.SOURCE_NAME}: {len(new)} new articles")
        except Exception as exc:
            print(f"  {ScraperClass.SOURCE_NAME}: FAILED — {exc}", file=sys.stderr)

    return raw


def main(dry_run: bool = False) -> None:
    load_dotenv()  # no-op on Jules VM; useful for local .env files

    # 1. Scrape
    print("=== Scraping ===")
    raw_articles = scrape_all()
    print(f"Total unique articles scraped: {len(raw_articles)}\n")

    if not raw_articles:
        print("No articles found. Exiting.")
        return

    # 2. Classify
    print("=== Classifying ===")
    try:
        classifier = GeminiClassifier()
        classified = classifier.classify_all(raw_articles)
        print(f"Classified {len(classified)} articles\n")
    except RuntimeError as exc:
        print(f"Classification unavailable: {exc}", file=sys.stderr)
        print("Continuing without classification.\n", file=sys.stderr)
        classified = []

    # 3. Consolidate duplicate topics
    print("=== Consolidating topics ===")
    if classified:
        try:
            consolidator = TopicConsolidator()
            topics = consolidator.consolidate(classified)
        except Exception as exc:
            print(f"Consolidation failed: {exc} — using unmerged articles.", file=sys.stderr)
            topics = [article_to_consolidated(a) for a in classified]
    else:
        topics = []
    print(f"Consolidated {len(classified)} articles → {len(topics)} unique topics\n")

    # 4. Build digest
    now_ph = datetime.now(PH_TZ)
    digest = DailyDigest(
        date=now_ph.strftime("%Y-%m-%d"),
        scraped_at=datetime.now(timezone.utc),
        raw_article_count=len(classified),
        topic_count=len(topics),
        topics=topics,
    )

    # 5a. Dry-run: print to stdout
    if dry_run:
        print("=== Dry-run output ===")
        print(json.dumps(digest.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return

    # 5b. Write and push to data branch
    print("=== Writing to data branch ===")
    writer = DataWriter(
        github_repo=os.environ.get("GITHUB_REPO"),
        github_pat=os.environ.get("GITHUB_PAT"),
    )
    writer.write_daily(digest)
    print("\nDone.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
