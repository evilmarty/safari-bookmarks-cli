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
        if func := getattr(self, command):
            func(args)
        else:
            raise ValueError(f"Invalid command: {command}")

    @contextmanager
    def with_bookmarks(
        self, update: bool = False
    ) -> Generator[WebBookmarkTypeList, None, None]:
        with open(self.path, "rb") as file:
            bookmarks = load(file, plistlib.FMT_BINARY)
        yield bookmarks
        if update:
            with open(self.path, "wb") as file:
                dump(bookmarks, file, plistlib.FMT_BINARY)

    def lookup(self, title: str, root: ChildrenType) -> Optional[ChildrenType]:
        if title.lower() == str(root.web_bookmark_uuid).lower():
            return root
        elif getattr(root, "title", None) == title:
            return root
        elif isinstance(root, WebBookmarkTypeList):
            list_ = cast(WebBookmarkTypeList, root)
            for child in iter(list_.children):
                if result := self.lookup(title, child):
                    return result
        return None

    def parent(
        self, target: ChildrenType, root: ChildrenType
    ) -> Optional[ChildrenType]:
        if target == root:
            return root
        elif isinstance(root, WebBookmarkTypeList):
            list_ = cast(WebBookmarkTypeList, root)
            if target in list_.children:
                return root
            for child in root.children:
                if result := self.parent(target, child):
                    return result
        return None

    def get_info(self, item: ChildrenType) -> tuple[str, str, str]:
        if isinstance(item, WebBookmarkTypeLeaf):
            return (
                "leaf",
                item.uri_dictionary.get("title", ""),
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

    def render_item(self, item: ChildrenType, format: str, depth: int = 0):
        id = item.web_bookmark_uuid
        type_, title, url = self.get_info(item)
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
            self.render_children(item, format=format, depth=depth + 1)
            self.output.write("\n")

    def render_children(self, item: ChildrenType, format: str, depth: int = 0):
        if not isinstance(item, WebBookmarkTypeList):
            return
        list_ = cast(WebBookmarkTypeList, item)
        for child in list_.children:
            self.render_item(child, format, depth=depth)

    def render(
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
                self.render_children(root, format=format)
            else:
                self.render_item(root, format=format)

    def list(self, target: Optional[str] = None, **kwargs):
        with self.with_bookmarks() as root:
            if target:
                root = self.lookup(target, root)
            if root is None:
                raise ValueError("Target not found")
            self.render(
                root, only_children=isinstance(root, WebBookmarkTypeList), **kwargs
            )

    def add(
        self,
        title: Optional[str] = None,
        uuid: Optional[str] = None,
        url: Optional[str] = None,
        to: Optional[str] = None,
        list=False,
        **kwargs,
    ):
        uuid = str(uuid or UUID.uuid4()).upper()
        if list:
            if not title:
                raise ValueError("Title is required")
            web_bookmark = WebBookmarkTypeList(
                WebBookmarkUUID=uuid,
                Title=title,
            )
            if url:
                raise ValueError("URL is not supported by lists")
        elif url is None:
            raise ValueError("URL is required")
        else:
            web_bookmark = WebBookmarkTypeLeaf(
                WebBookmarkUUID=uuid,
                URLString=url,
            )
            if title:
                web_bookmark.title = title
        with self.with_bookmarks(True) as target:
            if to:
                target = self.lookup(to, target)
                if not isinstance(target, WebBookmarkTypeList):
                    raise ValueError("Invalid destination")
            target.children.append(web_bookmark)
            self.render(web_bookmark, **kwargs)

    def remove(self, targets: List[str], **kwargs):
        with self.with_bookmarks(True) as root:
            for target in targets:
                node = self.lookup(target, root)
                if node is None:
                    raise ValueError("Target not found")
                parent = cast(WebBookmarkTypeList, self.parent(node, root))
                parent.remove(node)
            self.render(root, **kwargs)

    def move(self, target: str, to: Optional[str] = None, **kwargs):
        with self.with_bookmarks(True) as bookmarks:
            node = self.lookup(target, bookmarks)
            if node is None:
                raise ValueError("Target not found")
            parent = cast(WebBookmarkTypeList, self.parent(node, bookmarks))
            if not to:
                raise ValueError("Missing destination")
            dest = self.lookup(to, bookmarks)
            if not isinstance(dest, WebBookmarkTypeList):
                raise ValueError("Invalid destination")
            parent.remove(node)
            dest.append(node)
            self.render(dest, **kwargs)

    def edit(
        self,
        target: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        **kwargs,
    ):
        with self.with_bookmarks(True) as bookmarks:
            node = self.lookup(target, bookmarks)
            if node is None:
                raise ValueError("Target not found")
            if title is not None:
                node.title = title
            if url is not None:
                if isinstance(node, WebBookmarkTypeLeaf):
                    node.url_string = url
                else:
                    raise ValueError("Cannot update target url")
            self.render(node, **kwargs)
