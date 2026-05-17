from scrapers.base import RSSBaseScraper


class InquirerScraper(RSSBaseScraper):
    SOURCE_NAME = "inquirer"
    FEED_URLS = [
        "https://newsinfo.inquirer.net/feed",
        "https://business.inquirer.net/feed",
        "https://globalnation.inquirer.net/feed",
    ]
