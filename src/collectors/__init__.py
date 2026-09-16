from .base import Collector
from .local_library import LocalLibraryCollector
from .rss import RSSCollector
from .webpage import WebpageCollector

__all__ = ["Collector", "LocalLibraryCollector", "RSSCollector", "WebpageCollector"]
