from .gma_news import GMANewsScraper
from .abs_cbn import ABSCBNScraper
from .cnn_ph import CNNPhilippinesScraper
from .inquirer import InquirerScraper
from .philippine_star import PhilippineStarScraper
from .manila_bulletin import ManilaBulletinScraper
from .rappler import RapplerScraper
from .senate_gov import SenateScraper
from .congress_gov import CongressScraper
from .official_gazette import OfficialGazetteScraper

ALL_SCRAPERS = [
    GMANewsScraper,
    ABSCBNScraper,
    CNNPhilippinesScraper,
    InquirerScraper,
    PhilippineStarScraper,
    ManilaBulletinScraper,
    RapplerScraper,
    SenateScraper,
    CongressScraper,
    OfficialGazetteScraper,
]

__all__ = ["ALL_SCRAPERS"]
