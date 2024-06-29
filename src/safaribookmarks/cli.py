from contextlib import contextmanager
import plistlib
from typing import cast, Generator, IO, Optional
import uuid
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

    def render(self, root: ChildrenType, args, only_children=False):
        if args.json:
            self.output.write(root.model_dump_json(by_alias=True))
        else:
            format = args.format if args.format else DEFAULT_LIST_FORMAT
            if only_children:
                self.render_children(root, format=format)
            else:
                self.render_item(root, format=format)

    def list(self, args):
        with self.with_bookmarks() as target:
            if args.target:
                target = self.lookup(args.target, target)
            if target is None:
                raise ValueError("Target not found")
            self.render(target, args, isinstance(target, WebBookmarkTypeList))

    def add(self, args):
        uuid_ = str(args.uuid or uuid.uuid4()).upper()
        if args.list:
            if not args.title:
                raise ValueError("Title is required")
            web_bookmark = WebBookmarkTypeList(
                WebBookmarkUUID=uuid_,
                Title=args.title,
            )
            if args.url:
                raise ValueError("URL is not supported by lists")
        else:
            web_bookmark = WebBookmarkTypeLeaf(
                WebBookmarkUUID=uuid_,
                URLString=args.url,
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
                parent = cast(WebBookmarkTypeList, self.parent(target, root))
                parent.remove(target)
            self.render(root, args)

    def move(self, args):
        with self.with_bookmarks(True) as bookmarks:
            target = self.lookup(args.target, bookmarks)
            if target is None:
                raise ValueError("Target not found")
            parent = cast(WebBookmarkTypeList, self.parent(target, bookmarks))
            if not args.to:
                raise ValueError("Missing destination")
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
                target.title = title
            if url := args.url:
                if isinstance(target, WebBookmarkTypeLeaf):
                    target.url_string = url
                else:
                    raise ValueError("Cannot update target url")
            self.render(target, args)
