from scrapers.base import RSSBaseScraper


class GMANewsScraper(RSSBaseScraper):
    SOURCE_NAME = "gma_news"
    FEED_URLS = [
        "https://www.gmanetwork.com/news/rss/topstories/",
        "https://www.gmanetwork.com/news/rss/nation/",
        "https://www.gmanetwork.com/news/rss/economy/",
        "https://www.gmanetwork.com/news/rss/scitech/",
    ]
