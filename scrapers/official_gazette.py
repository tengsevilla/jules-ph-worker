from scrapers.base import RSSBaseScraper


class OfficialGazetteScraper(RSSBaseScraper):
    """Scrapes executive orders, proclamations, and official announcements
    from the Official Gazette of the Republic of the Philippines."""

    SOURCE_NAME = "official_gazette"
    FEED_URLS = [
        "https://www.officialgazette.gov.ph/feed/",
        "https://www.officialgazette.gov.ph/category/executive-orders/feed/",
        "https://www.officialgazette.gov.ph/category/proclamations/feed/",
    ]
