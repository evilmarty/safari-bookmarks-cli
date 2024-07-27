from .safaribookmarks import SafariBookmarks, SafariBookmarkItem
from .helpers import load, dump

open = SafariBookmarks.open

__all__ = ["load", "dump", "SafariBookmarks", "SafariBookmarkItem", "open"]
