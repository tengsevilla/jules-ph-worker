from __future__ import annotations

import sys

from scrapers.base import HTMLBaseScraper, RawArticle

NEWS_URL = "https://www.senate.gov.ph/news-releases/"
BASE_URL = "https://www.senate.gov.ph"


class SenateScraper(HTMLBaseScraper):
    """Scrapes press releases from the Philippine Senate website.

    The Senate site does not publish an RSS feed, so we parse the HTML
    news-releases listing page. Selectors may need updating if the site
    is redesigned — adjust the CSS selectors in fetch() accordingly.
    """

    SOURCE_NAME = "senate_gov"

    def fetch(self) -> list[RawArticle]:
        try:
            soup = self._get(NEWS_URL)
        except Exception as exc:
            print(f"  [{self.SOURCE_NAME}] fetch error: {exc}")
            return []

        articles: list[RawArticle] = []

        # Try several common patterns used by Philippine government CMS layouts.
        items = (
            soup.select("article")
            or soup.select(".views-row")
            or soup.select(".news-release-item")
            or soup.select(".field-content a")
            or soup.find_all("li", class_=lambda c: c and "news" in c.lower())
        )

        for item in items[:30]:
            link_tag = item.find("a", href=True)
            if not link_tag:
                continue

            href = link_tag["href"]
            url = href if href.startswith("http") else BASE_URL + href
            title = link_tag.get_text(strip=True)
            if not title:
                continue

            summary_tag = item.find("p") or item.find(
                "div", class_=lambda c: c and "summary" in (c or "").lower()
            )
            summary = summary_tag.get_text(strip=True) if summary_tag else title

            date_tag = item.find("time") or item.find(
                "span", class_=lambda c: c and "date" in (c or "").lower()
            )
            published_at = None
            if date_tag:
                published_at = date_tag.get("datetime") or date_tag.get_text(strip=True)

            articles.append(
                RawArticle(
                    source=self.SOURCE_NAME,
                    url=url,
                    title=title,
                    summary=summary,
                    published_at=published_at,
                )
            )

        if not articles:
            print(
                f"  [{self.SOURCE_NAME}] WARNING: 0 articles found — "
                "site layout may have changed. Check CSS selectors in senate_gov.py.",
                file=sys.stderr,
            )
        return articles
