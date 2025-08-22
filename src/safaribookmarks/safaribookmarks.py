import os
import plistlib
from typing import IO, Iterable, Optional

from .models import (
    WebBookmarkTypeList,
    WebBookmarkTypeLeaf,
    WebBookmarkType,
    WebBookmarkTypeProxy,
)


class SafariBookmarkItem:
    __slots__ = ("_node", "_parent")

    def __init__(
        self, node: WebBookmarkType, parent: Optional["SafariBookmarkItem"] = None
    ) -> None:
        if not getattr(parent, "is_folder", True):
            raise ValueError("Parent must be a folder")
        self._node = node
        self._parent = parent

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return repr(self._node)

    def __len__(self) -> int:
        return len(self.children)

    def __hash__(self) -> int:
        return hash(self._node)

    def __iter__(self) -> Iterable["SafariBookmarkItem"]:
        for child in getattr(self._node, "children", []):
            yield SafariBookmarkItem(
                node=child,
                parent=self,
            )

    def __contains__(self, other: object) -> bool:
        for child in iter(self):
            if child == other:
                return True
        return False

    def __eq__(self, value: object) -> bool:
        return type(self) == type(value) and self._node == getattr(value, "_node", None)

    def __getitem__(self, key) -> "SafariBookmarkItem":
        if isinstance(key, tuple):
            item = self
            for x in key:
                item = item[x]
            return item
        elif not isinstance(key, str):
            raise TypeError(type(key).__name__)
        for child in iter(self):
            if child.id == key or child.title == key:
                return child
        raise KeyError(key)

    @property
    def movable(self) -> bool:
        return self.is_bookmark or self.is_folder

    @property
    def is_bookmark(self) -> bool:
        return isinstance(self._node, WebBookmarkTypeLeaf)

    @property
    def is_folder(self) -> bool:
        return isinstance(self._node, WebBookmarkTypeList)

    @property
    def type(self) -> str:
        if isinstance(self._node, WebBookmarkTypeProxy):
            return "proxy"
        elif self.is_bookmark:
            return "bookmark"
        elif self.is_folder:
            return "folder"
        else:
            return ""

    @property
    def id(self) -> str:
        return self._node.web_bookmark_uuid

    @property
    def title(self) -> str:
        return getattr(self._node, "title", "")

    @title.setter
    def title(self, title: str) -> None:
        if hasattr(self._node, "title"):
            setattr(self._node, "title", title)

    @property
    def url(self) -> str:
        return getattr(self._node, "url_string", "")

    @url.setter
    def url(self, url: str) -> None:
        if hasattr(self._node, "url_string"):
            setattr(self._node, "url_string", url)

    @property
    def children(self) -> list["SafariBookmarkItem"]:
        return list(iter(self))

    @property
    def parent(self) -> Optional["SafariBookmarkItem"]:
        return self._parent

    def get(self, id: str) -> Optional["SafariBookmarkItem"]:
        if self.id.lower() == id.lower():
            return self
        for child in iter(self):
            result = child.get(id)
            if result is not None:
                return result
        return None

    def walk(self, *titles) -> Optional["SafariBookmarkItem"]:
        if len(titles) == 0:
            return self
        title = titles[0]
        for child in iter(self):
            if child.title == title:
                return child.walk(*titles[1:])
        return None

    def remove(self, item: "SafariBookmarkItem") -> None:
        if item not in self:
            raise RuntimeError("Not a child")
        if not item.movable:
            raise RuntimeError("Invalid item")
        getattr(self._node, "children", []).remove(item._node)
        item._parent = None

    def empty(self) -> None:
        getattr(self._node, "children", []).clear()

    def append(self, item: "SafariBookmarkItem") -> None:
        if not self.is_folder:
            raise RuntimeError("Not a folder")
        if not item.movable:
            raise RuntimeError("Invalid item")
        if item in self:
            return
        if parent := item.parent:
            parent.remove(item)
        getattr(self._node, "children", []).append(item._node)
        item._parent = self

    def add_bookmark(
        self, url: str, title: Optional[str] = None, id: Optional[str] = None
    ) -> "SafariBookmarkItem":
        kwargs = {"URLString": url, "URIDictionary": {}}
        if id is not None:
            kwargs["WebBookmarkUUID"] = id
        if title is not None:
            kwargs["URIDictionary"]["title"] = title
        item = SafariBookmarkItem(node=WebBookmarkTypeLeaf(**kwargs))
        self.append(item)
        return item

    def add_folder(self, title: str, id: Optional[str] = None) -> "SafariBookmarkItem":
        kwargs = {"Title": title, "Children": []}
        if id is not None:
            kwargs["WebBookmarkUUID"] = id
        item = SafariBookmarkItem(node=WebBookmarkTypeList(**kwargs))
        self.append(item)
        return item

    def json(self) -> str:
        return self._node.model_dump_json(by_alias=True)


class SafariBookmarks(SafariBookmarkItem):
    __slots__ = ("_node", "_parent", "_path", "_binary")

    def __init__(self, root: WebBookmarkTypeList) -> None:
        super().__init__(node=root)
        self._path = None
        self._binary = None

    def __enter__(self) -> "SafariBookmarks":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is None and self.path is not None:
            self.save()

    @property
    def movable(self) -> bool:
        return False

    @property
    def path(self) -> Optional[os.PathLike]:
        return self._path

    @property
    def binary(self) -> Optional[bool]:
        return self._binary

    def dump(self, fp: IO, *, binary=True) -> None:
        if hasattr(fp, "mode") and "b" not in fp.mode:
            raise IOError("Must be in binary mode")
        fmt = plistlib.FMT_BINARY if binary else plistlib.FMT_XML
        data = self._node.model_dump(by_alias=True)
        plistlib.dump(data, fp, fmt=fmt, sort_keys=True, skipkeys=False)

    def save(
        self, path: Optional[os.PathLike] = None, binary: Optional[bool] = None
    ) -> None:
        if path is None:
            path = self.path
        if path is None:
            raise RuntimeError("Not opened")
        if binary is None:
            binary = self.binary or True
        with open(path, "wb") as file:
            self.dump(fp=file, binary=binary)

    @classmethod
    def load(cls, fp: IO, *, binary=True) -> "SafariBookmarks":
        if hasattr(fp, "mode") and "b" not in fp.mode:
            raise IOError("Must be in binary mode")
        fmt = plistlib.FMT_BINARY if binary else plistlib.FMT_XML
        data = plistlib.load(fp, fmt=fmt)
        obj = cls(WebBookmarkTypeList.model_validate(data))
        obj._binary = binary
        return obj

    @classmethod
    def open(cls, path: os.PathLike, binary=True) -> "SafariBookmarks":
        with open(path, "rb") as file:
            obj = cls.load(fp=file, binary=binary)
            obj._path = path
            return obj
