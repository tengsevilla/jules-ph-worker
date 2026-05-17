from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

import feedparser
import httpx
from bs4 import BeautifulSoup

PH_TZ = timezone(timedelta(hours=8))
USER_AGENT = (
    "jules-ph-worker/1.0 "
    "(Philippine civic news aggregator; "
    "github.com/tenghuey-ai/jules-ph-worker)"
)


@dataclass
class RawArticle:
    source: str
    url: str
    title: str
    summary: str
    published_at: Optional[str] = None


class BaseScraper(ABC):
    SOURCE_NAME: str = ""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=30,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BaseScraper:
        return self

    def __exit__(self, *args) -> None:
        self.close()

    @abstractmethod
    def fetch(self) -> list[RawArticle]: ...


class RSSBaseScraper(BaseScraper):
    """Scraper for sources that expose RSS / Atom feeds."""

    FEED_URLS: list[str] = []

    def fetch(self) -> list[RawArticle]:
        articles: list[RawArticle] = []
        seen: set[str] = set()

        for feed_url in self.FEED_URLS:
            try:
                feed = feedparser.parse(
                    feed_url,
                    request_headers={"User-Agent": USER_AGENT},
                )
                for entry in feed.entries:
                    url = entry.get("link", "")
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    if not self._is_today(entry.get("published_parsed")):
                        continue
                    articles.append(
                        RawArticle(
                            source=self.SOURCE_NAME,
                            url=url,
                            title=entry.get("title", "").strip(),
                            summary=self._strip_html(
                                entry.get("summary", "")
                                or entry.get("description", "")
                            ),
                            published_at=entry.get("published", ""),
                        )
                    )
            except Exception as exc:
                print(f"  [{self.SOURCE_NAME}] RSS error ({feed_url}): {exc}")

        return articles

    def _is_today(self, published_parsed) -> bool:
        if not published_parsed:
            # Exclude undated entries — including them causes stale pinned
            # articles to be re-scraped and re-classified every single day.
            return False
        pub_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc).astimezone(PH_TZ)
        return pub_dt.date() == datetime.now(PH_TZ).date()

    def _strip_html(self, html: str) -> str:
        if not html:
            return ""
        return BeautifulSoup(html, "html.parser").get_text(separator=" ").strip()


class HTMLBaseScraper(BaseScraper):
    """Scraper for sources without RSS feeds (government sites, etc.)."""

    def _get(self, url: str) -> BeautifulSoup:
        response = self._client.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _strip_html(self, html: str) -> str:
        if not html:
            return ""
        return BeautifulSoup(html, "html.parser").get_text(separator=" ").strip()
