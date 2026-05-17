from __future__ import annotations

import json
import sys
import time

from models.article import Article, Classification
from scrapers.base import RawArticle
from classifier.prompts import BATCH_SIZE, build_batch_prompt
from classifier.ai_client import get_model

INTER_BATCH_DELAY = 1.5  # seconds between batches to respect rate limits


class GeminiClassifier:
    def __init__(self) -> None:
        self._model = get_model(temperature=0.1)

    def classify_all(self, raw_articles: list[RawArticle]) -> list[Article]:
        articles: list[Article] = []
        total_batches = (len(raw_articles) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_idx, start in enumerate(range(0, len(raw_articles), BATCH_SIZE)):
            batch = raw_articles[start : start + BATCH_SIZE]
            print(f"  Classifying batch {batch_idx + 1}/{total_batches} ({len(batch)} articles)...")

            try:
                classifications = self._classify_batch(batch)
            except Exception as exc:
                print(f"  Batch {batch_idx + 1} failed: {exc}", file=sys.stderr)
                classifications = [None] * len(batch)

            for raw, cls in zip(batch, classifications):
                articles.append(
                    Article(
                        source=raw.source,
                        url=raw.url,
                        title=raw.title,
                        summary=raw.summary,
                        published_at=raw.published_at,
                        classification=cls,
                    )
                )

            if start + BATCH_SIZE < len(raw_articles):
                time.sleep(INTER_BATCH_DELAY)

        return articles

    def _classify_batch(self, batch: list[RawArticle]) -> list[Classification | None]:
        prompt = build_batch_prompt(batch)
        response = self._model.generate_content(prompt)

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Model returned invalid JSON: {exc}") from exc

        if isinstance(data, dict):
            data = data.get("classifications", data.get("articles", list(data.values())[0]))

        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array, got {type(data)}")

        results: list[Classification | None] = []
        for i, item in enumerate(data):
            try:
                results.append(Classification(**item))
            except Exception as exc:
                print(f"  Article {i + 1} parse error: {exc}", file=sys.stderr)
                results.append(None)

        while len(results) < len(batch):
            results.append(None)

        return results
