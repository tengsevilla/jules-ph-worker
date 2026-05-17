from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .article import Sentiment


class ImpactRecord(BaseModel):
    date: str
    article_id: str
    article_title: str
    article_url: str
    impact: Sentiment
    reason: str
    source: str


class PoliticianProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")  # safely ignore computed fields on load

    slug: str
    name: str
    position: str
    party: Optional[str] = None
    branch: str  # executive | legislative | judicial
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    last_updated: datetime
    impact_history: list[ImpactRecord] = Field(default_factory=list)

    @computed_field
    @property
    def impact_score(self) -> float:
        total = self.positive_count + self.negative_count + self.neutral_count
        if total == 0:
            return 0.0
        return round((self.positive_count - self.negative_count) / total, 3)
