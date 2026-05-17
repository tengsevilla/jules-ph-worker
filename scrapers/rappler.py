from scrapers.base import RSSBaseScraper


class RapplerScraper(RSSBaseScraper):
    """Rappler — critical for Philippine political journalism and accountability coverage."""

    SOURCE_NAME = "rappler"
    FEED_URLS = [
        "https://www.rappler.com/feed/",
        "https://www.rappler.com/nation/feed/",
        "https://www.rappler.com/business-economy/feed/",
    ]
