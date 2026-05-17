from __future__ import annotations

import json

BATCH_SIZE = 10

SECTOR_SLUGS = [
    # Agriculture & Natural Resources
    "farmer", "fisherman", "miner", "forest_worker",
    # Health & Social Services
    "health_worker", "social_worker", "senior_citizen", "pwd",
    # Education
    "teacher", "student",
    # Labor & Employment
    "labor_worker", "kasambahay", "security_guard", "bpo_worker",
    "retail_worker", "hospitality_worker",
    # Transport & Logistics
    "driver", "seafarer", "delivery_rider",
    # Business & Economy
    "business_owner", "vendor", "freelancer",
    # Overseas Workers
    "ofw",
    # Government & Public Service
    "government_employee", "barangay_official", "military_police",
    # Professionals
    "engineer_architect", "lawyer", "journalist", "it_tech_worker", "artist_creative",
    # Vulnerable & Marginalized
    "solo_parent", "informal_settler", "indigenous_people", "youth", "lgbtq",
    "prisoner_returnee",
]

_SCHEMA_DESCRIPTION = f"""
Each object in the returned array must have:
- "category": one of [politics, economy, weather, health, crime, education, environment, disaster, international, sports, technology, social]
- "sentiment": one of [positive, negative, neutral] — from the perspective of ordinary Filipino citizens
- "impact_level": one of [national, regional, local]
- "affected_sectors": array of strings — only include slugs from this exact list where the article has a direct, meaningful impact:
  {json.dumps(SECTOR_SLUGS)}
- "politicians": array of objects for each Philippine politician or senior public official mentioned:
  - "name": full name
  - "position": e.g. Senator, House Representative, President, Secretary, Governor, Mayor
  - "party": political party affiliation, or null if unknown
  - "impact": one of [positive, negative, neutral] — the effect of their action/statement on ordinary Filipinos
  - "reason": one sentence explaining why (be specific, cite the action)
- "gamification": object with:
  - "event_type": one of [law_passed, bill_filed, calamity, price_hike, scandal, achievement, arrest, protest, election, budget, infrastructure, health_outbreak, trade_deal]
  - "severity": integer 1–5 (1 = minor local incident, 5 = major national crisis or landmark event)
  - "affected_population_estimate": one of [all, majority, minority]
""".strip()


def build_batch_prompt(articles: list) -> str:
    articles_block = ""
    for i, a in enumerate(articles, 1):
        summary = (a.summary or "")[:600]
        articles_block += (
            f"\n--- Article {i} ---\n"
            f"Title: {a.title}\n"
            f"Source: {a.source}\n"
            f"Summary: {summary}\n"
        )

    return (
        "You are a Philippine news classifier for a civic awareness platform.\n\n"
        f"Classify each of the {len(articles)} articles below.\n\n"
        f"{_SCHEMA_DESCRIPTION}\n\n"
        "Rules:\n"
        "- Return a JSON array [...] with EXACTLY one object per article, in the same order.\n"
        "- Only list politicians who are explicitly named and whose action is described.\n"
        "- Only include sector slugs that are directly and meaningfully affected — not tangentially.\n"
        "- Return ONLY valid JSON. No markdown fences, no explanation.\n\n"
        f"Articles to classify:{articles_block}"
    )
