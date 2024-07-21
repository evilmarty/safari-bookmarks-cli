from contextlib import contextmanager
import plistlib
from typing import cast, Generator, IO, List, Optional
import uuid as UUID
from .helpers import load, dump
from .models import (
    ChildrenType,
    WebBookmarkTypeList,
    WebBookmarkTypeLeaf,
    WebBookmarkTypeProxy,
)

DEFAULT_LIST_FORMAT = "{prefix: <{depth}}{title: <50}{type: <6}{id: <38}{url}"


class CLI:
    def __init__(self, path: str, out: IO) -> None:
        self.path = path
        self.output = out

    def run(self, command: str, **kwargs) -> None:
        if command is None:
            raise ValueError("No command specified")
        func = getattr(self, command, None)
        if command.startswith("_") or not callable(func):
            raise ValueError(f"Invalid command: {command}")
        func(**kwargs)

    def _load(self) -> WebBookmarkTypeList:
        with open(self.path, "rb") as file:
            return load(file, plistlib.FMT_BINARY)

    def _dump(self, bookmarks: WebBookmarkTypeList) -> None:
        with open(self.path, "wb") as file:
            dump(bookmarks, file, plistlib.FMT_BINARY)

    @contextmanager
    def _with_bookmarks(
        self, update: bool = False
    ) -> Generator[WebBookmarkTypeList, None, None]:
        bookmarks = self._load()
        yield bookmarks
        if update:
            self._dump(bookmarks)

    def _walk(self, path: List[str], root: ChildrenType) -> Optional[ChildrenType]:
        if len(path) == 0:
            return root
        title = path[0]
        if title == root.title:
            return root
        if isinstance(root, WebBookmarkTypeList):
            list_ = cast(WebBookmarkTypeList, root)
            for node in list_.children:
                if node.title == title:
                    return self._walk(path[1:], node)
        return None

    def _get(self, uuid: str, root: ChildrenType) -> Optional[ChildrenType]:
        if uuid.lower() == str(root.web_bookmark_uuid).lower():
            return root
        elif isinstance(root, WebBookmarkTypeList):
            list_ = cast(WebBookmarkTypeList, root)
            for child in list_.children:
                if result := self._get(uuid, child):
                    return result
        return None

    def _get_or_walk(
        self, path: List[str], root: ChildrenType
    ) -> Optional[ChildrenType]:
        if len(path) == 1:
            if result := self._get(path[0], root):
                return result
        return self._walk(path, root)

    def _parent(
        self, target: ChildrenType, root: ChildrenType
    ) -> Optional[ChildrenType]:
        if target == root:
            return root
        elif isinstance(root, WebBookmarkTypeList):
            list_ = cast(WebBookmarkTypeList, root)
            if target in list_.children:
                return root
            for child in root.children:
                if result := self._parent(target, child):
                    return result
        return None

    def _get_info(self, item: ChildrenType) -> tuple[str, str, str]:
        if isinstance(item, WebBookmarkTypeLeaf):
            return (
                "leaf",
                item.title,
                item.url_string,
            )
        elif isinstance(item, WebBookmarkTypeProxy):
            return ("proxy", item.title, "")
        elif isinstance(item, WebBookmarkTypeList):
            return (
                "list",
                item.title,
                "",
            )
        else:
            return ("unknown", "", "")

    def _render_item(self, item: ChildrenType, format: str, depth: int = 0):
        id = item.web_bookmark_uuid
        type_, title, url = self._get_info(item)
        self.output.write(
            f"{format}\n".format(
                depth=depth,
                prefix="",
                suffix="",
                title=title.replace("\n", ""),
                type=type_,
                url=url,
                id=str(id),
            )
        )
        if isinstance(item, WebBookmarkTypeList):
            self._render_children(item, format=format, depth=depth + 1)
            self.output.write("\n")

    def _render_children(self, item: ChildrenType, format: str, depth: int = 0):
        if not isinstance(item, WebBookmarkTypeList):
            return
        list_ = cast(WebBookmarkTypeList, item)
        for child in list_.children:
            self._render_item(child, format, depth=depth)

    def _render(
        self,
        root: ChildrenType,
        format: Optional[str] = None,
        only_children=False,
        json=False,
    ):
        if json:
            self.output.write(root.model_dump_json(by_alias=True))
        else:
            if format is None:
                format = DEFAULT_LIST_FORMAT
            if only_children:
                self._render_children(root, format=format)
            else:
                self._render_item(root, format=format)

    def list(self, path: List[str] = [], **kwargs):
        with self._with_bookmarks() as root:
            target = self._get_or_walk(path, root)
            if target is None:
                raise ValueError("Target not found")
            self._render(
                target, only_children=isinstance(target, WebBookmarkTypeList), **kwargs
            )

    def add(
        self,
        title: Optional[str],
        uuid: Optional[str] = None,
        url: Optional[str] = None,
        path: List[str] = [],
        list=False,
        **kwargs,
    ):
        uuid = str(uuid or UUID.uuid4()).upper()
        if list:
            if url:
                raise ValueError("URL is not supported by lists")
            if not title:
                raise ValueError("Title is required")
            web_bookmark = WebBookmarkTypeList(
                WebBookmarkUUID=uuid,
                Title=title,
            )
        elif url is None:
            raise ValueError("URL is required")
        else:
            web_bookmark = WebBookmarkTypeLeaf(
                WebBookmarkUUID=uuid,
                URLString=url,
            )
            if title:
                web_bookmark.title = title
        with self._with_bookmarks(True) as root:
            target = self._get_or_walk(path, root)
            if not isinstance(target, WebBookmarkTypeList):
                raise ValueError("Invalid destination")
            target.children.append(web_bookmark)
            self._render(web_bookmark, **kwargs)

    def remove(self, path: List[str], **kwargs):
        with self._with_bookmarks(True) as root:
            target = self._get_or_walk(path, root)
            if target is None:
                raise ValueError("Target not found")
            parent = cast(WebBookmarkTypeList, self._parent(target, root))
            parent.remove(target)
            self._render(root, **kwargs)

    def move(self, path: List[str], to: List[str] = [], **kwargs):
        with self._with_bookmarks(True) as root:
            target = self._get_or_walk(path, root)
            if target is None:
                raise ValueError("Target not found")
            parent = cast(WebBookmarkTypeList, self._parent(target, root))
            if not to:
                raise ValueError("Missing destination")
            dest = self._get_or_walk(to, root)
            if not isinstance(dest, WebBookmarkTypeList):
                raise ValueError("Invalid destination")
            parent.remove(target)
            dest.append(target)
            self._render(dest, **kwargs)

    def edit(
        self,
        path: List[str],
        title: Optional[str] = None,
        url: Optional[str] = None,
        **kwargs,
    ):
        with self._with_bookmarks(True) as root:
            target = self._get_or_walk(path, root)
            if target is None:
                raise ValueError("Target not found")
            if title is not None:
                target.title = title
            if url is not None:
                if isinstance(target, WebBookmarkTypeLeaf):
                    target.url_string = url
                else:
                    raise ValueError("Cannot update target url")
            self._render(target, **kwargs)

    def empty(self, path: List[str], **kwargs):
        with self._with_bookmarks(True) as root:
            target = self._get_or_walk(path, root)
            if target is None:
                raise ValueError("Target not found")
            if not isinstance(target, WebBookmarkTypeList):
                raise ValueError("Target is not a list")
            target.empty()
            self._render(
                root, only_children=isinstance(target, WebBookmarkTypeList), **kwargs
            )
