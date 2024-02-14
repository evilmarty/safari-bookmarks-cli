from contextlib import contextmanager
import plistlib
from typing import Generator, IO, Optional
import uuid
from .helpers import load, dump
from .models import (
    WebBookmarkType,
    WebBookmarkTypeList,
    WebBookmarkTypeLeaf,
    WebBookmarkTypeProxy,
)

DEFAULT_LIST_FORMAT = "{prefix: <{depth}}{title: <50}{type: <6}{id: <38}{url}"


class CLI:
    def __init__(self, path: str, out: IO) -> None:
        self.path = path
        self.output = out

    def run(self, command, args) -> None:
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

    def lookup(self, title: str, root: WebBookmarkType) -> Optional[WebBookmarkType]:
        if title.lower() == str(root.web_bookmark_uuid).lower():
            return root
        elif isinstance(root, WebBookmarkTypeLeaf):
            if root.uri_dictionary.get("title") == title:
                return root
        elif root.title == title:
            return root
        elif isinstance(root, WebBookmarkTypeList):
            for child in root:
                if result := self.lookup(title, child):
                    return result
        return None

    def parent(
        self, target: WebBookmarkType, root: WebBookmarkType
    ) -> Optional[WebBookmarkTypeList]:
        if target == root:
            return root
        elif isinstance(root, WebBookmarkTypeList):
            if target in root:
                return root
            for child in root:
                if result := self.parent(target, child):
                    return result
        return None

    def get_info(self, item: WebBookmarkType) -> tuple[str, str, str]:
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

    def render_item(self, item: WebBookmarkType, format: str, depth: int = 0):
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

    def render_children(self, item: WebBookmarkType, format: str, depth: int = 0):
        for child in item.children:
            self.render_item(child, format, depth=depth)

    def render(self, root: WebBookmarkType, args, only_children=False):
        if args.json:
            self.output.write(root.model_dump_json(by_alias=True))
        else:
            format = args.format if args.format else DEFAULT_LIST_FORMAT
            if only_children:
                self.render_children(root, format=format)
            else:
                self.render_item(root, format=format)

    def list(self, args):
        with self.with_bookmarks("rb") as target:
            if args.target:
                target = self.lookup(args.target, target)
            if target is None:
                raise ValueError("Target not found")
            self.render(target, args, True)

    def add(self, args):
        uuid_ = str(args.uuid or uuid.uuid4()).upper()
        if args.list:
            if not args.title:
                raise ValueError("Title is required")
            web_bookmark = WebBookmarkTypeList(
                web_bookmark_uuid=uuid_,
                title=args.title,
            )
            if args.url:
                raise ValueError("URL is not supported by lists")
        else:
            web_bookmark = WebBookmarkTypeLeaf(
                web_bookmark_uuid=uuid_,
                url_string=args.url,
            )
            if args.title:
                web_bookmark.uri_dictionary["title"] = args.title
        with self.with_bookmarks(True) as target:
            if args.to:
                target = self.lookup(args.to, target)
                if not isinstance(target, WebBookmarkTypeList):
                    raise ValueError("Invalid destination")
            target.children.append(web_bookmark)
            self.render(web_bookmark, args)

    def remove(self, args):
        with self.with_bookmarks(True) as root:
            for target in args.targets:
                target = self.lookup(target, root)
                if target is None:
                    raise ValueError("Target not found")
                parent = self.parent(target, root)
                parent.remove(target)
            self.render(root, args)

    def move(self, args):
        with self.with_bookmarks(True) as bookmarks:
            target = self.lookup(args.target, bookmarks)
            if target is None:
                raise ValueError("Target not found")
            parent = self.parent(target, bookmarks)
            if args.to:
                dest = self.lookup(args.to, bookmarks)
            if not isinstance(dest, WebBookmarkTypeList):
                raise ValueError("Invalid destination")
            parent.remove(target)
            dest.append(target)
            self.render(dest, args)

    def edit(self, args):
        with self.with_bookmarks(True) as bookmarks:
            target = self.lookup(args.target, bookmarks)
            if target is None:
                raise ValueError("Target not found")
            if title := args.title:
                if isinstance(target, WebBookmarkTypeList):
                    target.title = title
                elif isinstance(target, WebBookmarkTypeLeaf):
                    target.uri_dictionary["title"] = title
                else:
                    raise ValueError("Cannot update target title")
            if url := args.url:
                if isinstance(target, WebBookmarkTypeLeaf):
                    target.url_string = url
                else:
                    raise ValueError("Cannot update target url")
            self.render(target, args)
