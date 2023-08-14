import plistlib
from plistlib import PlistFormat
from typing import IO
from .models import WebBookmarkTypeList


def load(fp: IO, fmt: PlistFormat | None = None) -> WebBookmarkTypeList:
    if hasattr(fp, "mode"):
        assert 'b' in fp.mode
    data = plistlib.load(fp, fmt=fmt)
    return WebBookmarkTypeList.model_validate(data)


def dump(bookmarks: WebBookmarkTypeList, fp: IO, fmt: PlistFormat) -> None:
    if hasattr(fp, "mode"):
        assert 'b' in fp.mode
    data = bookmarks.model_dump(by_alias=True)
    return plistlib.dump(data, fp, fmt=fmt, sort_keys=True, skipkeys=False)
