from scrapers.base import RSSBaseScraper


class ManilaBulletinScraper(RSSBaseScraper):
    SOURCE_NAME = "manila_bulletin"
    FEED_URLS = [
        "https://mb.com.ph/feed",
        "https://mb.com.ph/category/news/feed",
        "https://mb.com.ph/category/business/feed",
    ]
