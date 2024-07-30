from contextlib import contextmanager
from typing import Generator, IO, List, Optional
from .safaribookmarks import SafariBookmarks, SafariBookmarkItem

DEFAULT_LIST_FORMAT = "{prefix: <{depth}}{title: <50}{type: <6}{id: <38}{url}"


class CLI:
    def __init__(self, path: str, out: IO) -> None:
        self.bookmarks = SafariBookmarks.open(path)
        self.output = out

    @property
    def path(self) -> str:
        return str(self.bookmarks.path)

    def run(self, command: str, **kwargs) -> None:
        if command is None:
            raise ValueError("No command specified")
        func = getattr(self, command, None)
        if command.startswith("_") or not callable(func):
            raise ValueError(f"Invalid command: {command}")
        func(**kwargs)

    def _get_or_walk(self, path: List[str]) -> Optional[SafariBookmarkItem]:
        if len(path) == 1:
            result = self.bookmarks.get(path[0])
            if result is not None:
                return result
        return self.bookmarks.walk(*path)

    def _save(self) -> None:
        self.bookmarks.save()

    def _render_item(self, item: SafariBookmarkItem, format: str, depth: int = 0):
        self.output.write(
            f"{format}\n".format(
                depth=depth,
                prefix="",
                suffix="",
                title=item.title.replace("\n", ""),
                type=item.type,
                url=item.url,
                id=item.id,
            )
        )
        if item.is_folder:
            self._render_children(item, format=format, depth=depth + 1)
            self.output.write("\n")

    def _render_children(self, item: SafariBookmarkItem, format: str, depth: int = 0):
        for child in iter(item):
            self._render_item(child, format, depth=depth)

    def _render(
        self,
        root: SafariBookmarkItem,
        format: Optional[str] = None,
        only_children=False,
        json=False,
    ):
        if json:
            self.output.write(root.json())
        else:
            if format is None:
                format = DEFAULT_LIST_FORMAT
            if only_children:
                self._render_children(root, format=format)
            else:
                self._render_item(root, format=format)

    def list(self, path: List[str] = [], **kwargs):
        target = self._get_or_walk(path)
        if target is None:
            raise ValueError("Target not found")
        self._render(target, only_children=target.is_folder, **kwargs)

    def add(
        self,
        title: Optional[str],
        uuid: Optional[str] = None,
        url: Optional[str] = None,
        path: List[str] = [],
        list=False,
    ):
        target = self._get_or_walk(path)
        if target is None or not target.is_folder:
            raise ValueError("Invalid destination")
        if list:
            if url:
                raise ValueError("URL is not supported by lists")
            if not title:
                raise ValueError("Title is required")
            target.add_folder(title=title, id=uuid)
        elif url is None:
            raise ValueError("URL is required")
        else:
            target.add_bookmark(url=url, id=uuid, title=title)
        self._save()

    def remove(self, path: List[str]):
        target = self._get_or_walk(path)
        if target is None:
            raise ValueError("Target not found")
        if parent := target.parent:
            parent.remove(target)
        self._save()

    def move(self, path: List[str], to: List[str] = []):
        target = self._get_or_walk(path)
        if target is None:
            raise ValueError("Target not found")
        if not to:
            raise ValueError("Missing destination")
        dest = self._get_or_walk(to)
        if dest is None or not dest.is_folder:
            raise ValueError("Invalid destination")
        dest.append(target)
        self._save()

    def edit(
        self,
        path: List[str],
        title: Optional[str] = None,
        url: Optional[str] = None,
    ):
        target = self._get_or_walk(path)
        if target is None:
            raise ValueError("Target not found")
        if title is not None:
            target.title = title
        if url is not None:
            target.url = url
            if target.is_bookmark:
                target.url = url
            else:
                raise ValueError("Cannot update target url")
        self._save()

    def empty(self, path: List[str]):
        target = self._get_or_walk(path)
        if target is None:
            raise ValueError("Target not found")
        if not target.is_folder:
            raise ValueError("Target is not a list")
        target.empty()
        self._save()
