from scrapers.base import RSSBaseScraper


class PhilippineStarScraper(RSSBaseScraper):
    SOURCE_NAME = "philippine_star"
    FEED_URLS = [
        "https://www.philstar.com/rss/headlines",
        "https://www.philstar.com/rss/nation",
        "https://www.philstar.com/rss/business",
    ]
