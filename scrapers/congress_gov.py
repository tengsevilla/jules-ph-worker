from __future__ import annotations

import sys

from scrapers.base import HTMLBaseScraper, RawArticle

NEWS_URL = "https://congress.gov.ph/news/"
BASE_URL = "https://congress.gov.ph"


class CongressScraper(HTMLBaseScraper):
    """Scrapes news releases from the House of Representatives website.

    No RSS feed is available; we parse the HTML news listing page.
    Adjust selectors in fetch() if the site layout changes.
    """

    SOURCE_NAME = "congress_gov"

    def fetch(self) -> list[RawArticle]:
        try:
            soup = self._get(NEWS_URL)
        except Exception as exc:
            print(f"  [{self.SOURCE_NAME}] fetch error: {exc}")
            return []

        articles: list[RawArticle] = []

        items = (
            soup.select("article")
            or soup.select(".news-item")
            or soup.select(".views-row")
            or soup.select(".post")
            or soup.find_all("li", class_=lambda c: c and "news" in (c or "").lower())
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
                "div", class_=lambda c: c and "excerpt" in (c or "").lower()
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
                "site layout may have changed. Check CSS selectors in congress_gov.py.",
                file=sys.stderr,
            )
        return articles
