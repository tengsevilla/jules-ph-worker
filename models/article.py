from __future__ import annotations

import sys
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    politics = "politics"
    economy = "economy"
    weather = "weather"
    health = "health"
    crime = "crime"
    education = "education"
    environment = "environment"
    disaster = "disaster"
    international = "international"
    sports = "sports"
    technology = "technology"
    social = "social"


class Sentiment(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class ImpactLevel(str, Enum):
    national = "national"
    regional = "regional"
    local = "local"


class EventType(str, Enum):
    law_passed = "law_passed"
    bill_filed = "bill_filed"
    calamity = "calamity"
    price_hike = "price_hike"
    scandal = "scandal"
    achievement = "achievement"
    arrest = "arrest"
    protest = "protest"
    election = "election"
    budget = "budget"
    infrastructure = "infrastructure"
    health_outbreak = "health_outbreak"
    trade_deal = "trade_deal"


class AffectedPopulation(str, Enum):
    all = "all"
    majority = "majority"
    minority = "minority"


class SectorSlug(str, Enum):
    # Agriculture & Natural Resources
    farmer = "farmer"
    fisherman = "fisherman"
    miner = "miner"
    forest_worker = "forest_worker"
    # Health & Social Services
    health_worker = "health_worker"
    social_worker = "social_worker"
    senior_citizen = "senior_citizen"
    pwd = "pwd"
    # Education
    teacher = "teacher"
    student = "student"
    # Labor & Employment
    labor_worker = "labor_worker"
    kasambahay = "kasambahay"
    security_guard = "security_guard"
    bpo_worker = "bpo_worker"
    retail_worker = "retail_worker"
    hospitality_worker = "hospitality_worker"
    # Transport & Logistics
    driver = "driver"
    seafarer = "seafarer"
    delivery_rider = "delivery_rider"
    # Business & Economy
    business_owner = "business_owner"
    vendor = "vendor"
    freelancer = "freelancer"
    # Overseas Workers
    ofw = "ofw"
    # Government & Public Service
    government_employee = "government_employee"
    barangay_official = "barangay_official"
    military_police = "military_police"
    # Professionals
    engineer_architect = "engineer_architect"
    lawyer = "lawyer"
    journalist = "journalist"
    it_tech_worker = "it_tech_worker"
    artist_creative = "artist_creative"
    # Vulnerable & Marginalized
    solo_parent = "solo_parent"
    informal_settler = "informal_settler"
    indigenous_people = "indigenous_people"
    youth = "youth"
    lgbtq = "lgbtq"
    prisoner_returnee = "prisoner_returnee"


class PoliticianMention(BaseModel):
    name: str
    position: str
    party: Optional[str] = None
    impact: Sentiment
    reason: str


class Gamification(BaseModel):
    event_type: EventType
    severity: int = Field(ge=1, le=5)
    affected_population_estimate: AffectedPopulation


class Classification(BaseModel):
    category: Category
    sentiment: Sentiment
    impact_level: ImpactLevel
    # str (not SectorSlug enum) so unknown slugs from Gemini are warned, not fatal
    affected_sectors: list[str] = Field(default_factory=list)
    politicians: list[PoliticianMention] = Field(default_factory=list)
    gamification: Gamification

    @field_validator("affected_sectors", mode="before")
    @classmethod
    def filter_valid_sectors(cls, v: list) -> list[str]:
        valid = {s.value for s in SectorSlug}
        result = []
        for s in v or []:
            if s in valid:
                result.append(s)
            else:
                print(f"  [warn] Unknown sector slug '{s}' — ignored", file=sys.stderr)
        return result


class Article(BaseModel):
    """Internal representation of a single scraped + classified article."""

    id: UUID = Field(default_factory=uuid4)
    source: str
    url: str
    title: str
    summary: str
    published_at: Optional[str] = None
    classification: Optional[Classification] = None


class SourceReference(BaseModel):
    """One source article that contributes to a consolidated topic."""

    source: str
    url: str
    title: str
    published_at: Optional[str] = None


class ConsolidatedArticle(BaseModel):
    """A news topic built from one or more source articles covering the same event."""

    id: UUID = Field(default_factory=uuid4)
    topic: str
    sources: list[SourceReference]
    summary: str
    classification: Optional[Classification] = None


class DailyDigest(BaseModel):
    date: str
    scraped_at: datetime
    raw_article_count: int
    topic_count: int
    topics: list[ConsolidatedArticle]
