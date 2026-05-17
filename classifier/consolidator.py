"""
Topic consolidation: groups classified articles that cover the same news event
into a single ConsolidatedArticle, merging their classifications.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from uuid import uuid4

from classifier.ai_client import get_model
from models.article import (
    Article,
    Classification,
    ConsolidatedArticle,
    ImpactLevel,
    PoliticianMention,
    Sentiment,
    SourceReference,
)

_IMPACT_PRIORITY = {Sentiment.negative: 2, Sentiment.positive: 1, Sentiment.neutral: 0}
_LEVEL_RANK = {ImpactLevel.national: 2, ImpactLevel.regional: 1, ImpactLevel.local: 0}
_POP_RANK = {"all": 2, "majority": 1, "minority": 0}


class TopicConsolidator:
    """Clusters articles covering the same news event, then merges each cluster."""

    def __init__(self) -> None:
        self._model = get_model(temperature=0.0)

    def consolidate(self, articles: list[Article]) -> list[ConsolidatedArticle]:
        if not articles:
            return []
        if len(articles) == 1:
            return [article_to_consolidated(articles[0])]

        try:
            raw_groups = self._get_topic_groups(articles)
            groups = _validate_groups(raw_groups, len(articles))
        except Exception as exc:
            print(
                f"  Consolidation grouping failed: {exc} — each article becomes its own topic.",
                file=sys.stderr,
            )
            groups = [
                {"topic": a.title, "indices": [i]} for i, a in enumerate(articles)
            ]


        consolidated = []
        for group in groups:
            result = _build_consolidated(articles, group)
            if result is not None:
                consolidated.append(result)

        return consolidated

    def _get_topic_groups(self, articles: list[Article]) -> list[dict]:
        articles_text = "\n".join(
            f"{i}: [{a.source}] {a.title}" for i, a in enumerate(articles)
        )
        prompt = (
            f"Group these {len(articles)} Philippine news articles by the news event they cover.\n"
            "Articles from different outlets reporting on the SAME event should share a group.\n"
            "Return a JSON array of group objects, each with:\n"
            '  "topic": a concise 6-10 word headline summarizing the event\n'
            '  "indices": array of 0-based article indices belonging to this group\n\n'
            f"Every index 0 to {len(articles) - 1} must appear in exactly one group.\n\n"
            f"Articles:\n{articles_text}\n\n"
            "Return ONLY a valid JSON array. No markdown fences, no explanation."
        )
        response = self._model.generate_content(prompt)
        data = json.loads(response.text)
        # Unwrap if Gemini returned {groups: [...]}
        if isinstance(data, dict):
            data = next(iter(data.values()))
        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array, got {type(data)}")
        return data


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _validate_groups(groups: list[dict], n: int) -> list[dict]:
    """Ensure every article index 0..n-1 appears in exactly one group."""
    used: set[int] = set()
    valid: list[dict] = []

    for group in groups:
        indices = [i for i in group.get("indices", []) if 0 <= i < n and i not in used]
        if indices:
            used.update(indices)
            valid.append({**group, "indices": indices})

    # Rescue any article Gemini dropped
    for i in range(n):
        if i not in used:
            valid.append({"topic": f"(ungrouped article {i})", "indices": [i]})

    return valid


def _build_consolidated(articles: list[Article], group: dict) -> ConsolidatedArticle | None:
    indices = group.get("indices", [])
    topic = group.get("topic", "").strip() or "Untitled topic"
    group_articles = [articles[i] for i in indices if 0 <= i < len(articles)]
    if not group_articles:
        return None

    sources = [
        SourceReference(
            source=a.source,
            url=a.url,
            title=a.title,
            published_at=a.published_at,
        )
        for a in group_articles
    ]
    summary = max((a.summary for a in group_articles), key=len, default="")
    classified = [a.classification for a in group_articles if a.classification]
    classification = _merge_classifications(classified) if classified else None

    return ConsolidatedArticle(
        topic=topic,
        sources=sources,
        summary=summary,
        classification=classification,
    )


def article_to_consolidated(article: Article) -> ConsolidatedArticle:
    return ConsolidatedArticle(
        topic=article.title,
        sources=[
            SourceReference(
                source=article.source,
                url=article.url,
                title=article.title,
                published_at=article.published_at,
            )
        ],
        summary=article.summary,
        classification=article.classification,
    )


def _merge_classifications(classifications: list[Classification]) -> Classification:
    # Category: most common
    category = Counter(c.category for c in classifications).most_common(1)[0][0]

    # Sentiment: most common
    sentiment = Counter(c.sentiment for c in classifications).most_common(1)[0][0]

    # Impact level: highest
    impact_level = max(
        (c.impact_level for c in classifications),
        key=lambda lv: _LEVEL_RANK[lv],
    )

    # Sectors: union, deduped
    affected_sectors = list({s for c in classifications for s in c.affected_sectors})

    # Politicians: dedup by normalised name; prefer most severe impact rating
    pol_map: dict[str, PoliticianMention] = {}
    for c in classifications:
        for pm in c.politicians:
            key = pm.name.lower().strip()
            if key not in pol_map or (
                _IMPACT_PRIORITY[pm.impact] > _IMPACT_PRIORITY[pol_map[key].impact]
            ):
                pol_map[key] = pm
    politicians = list(pol_map.values())

    # Gamification: take the entry with the highest severity
    gamification = max(
        (c.gamification for c in classifications),
        key=lambda g: g.severity,
    )
    # But use the most inclusive population estimate
    gamification = gamification.model_copy(
        update={
            "affected_population_estimate": max(
                (c.gamification.affected_population_estimate for c in classifications),
                key=lambda p: _POP_RANK.get(p.value if hasattr(p, "value") else p, 0),
            )
        }
    )

    return Classification(
        category=category,
        sentiment=sentiment,
        impact_level=impact_level,
        affected_sectors=affected_sectors,
        politicians=politicians,
        gamification=gamification,
    )
