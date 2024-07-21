from io import StringIO
import pytest
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from typing import Any, Generator, List, Optional

from safaribookmarks.cli import CLI

FIXTURE_PATH = Path(__file__).parent.joinpath("support", "fixtures")
BOOKMARKS_BINARY_PATH = FIXTURE_PATH.joinpath("Bookmarks.bin")


class TestCLI:
    @pytest.fixture()
    def bookmarks_path(self) -> Generator[Path, Any, Any]:
        with TemporaryDirectory() as dir:
            dest = Path(dir).joinpath("Bookmarks.plist")
            copyfile(BOOKMARKS_BINARY_PATH, dest)
            yield dest

    @pytest.fixture()
    def cli(self, bookmarks_path) -> CLI:
        return CLI(bookmarks_path, StringIO())

    @pytest.mark.parametrize(
        ("command", "error"),
        [
            pytest.param(
                "nope",
                ValueError("Invalid command"),
                id="non-existent-command",
            ),
            pytest.param(
                "path",
                ValueError("Invalid command"),
                id="invalid-command",
            ),
            pytest.param(
                "_get",
                ValueError("Invalid command"),
                id="invalid-command",
            ),
            pytest.param(
                None,
                ValueError("No command specified"),
                id="no-command",
            ),
        ],
    )
    def test_run(self, cli: CLI, command: str, error: BaseException):
        with pytest.raises(type(error), match=str(error)):
            cli.run(command)

    @pytest.mark.parametrize(
        ("json", "format", "path", "fixture_path"),
        [
            pytest.param(
                False,
                None,
                [],
                FIXTURE_PATH.joinpath("list.txt"),
                id="list-text",
            ),
            pytest.param(
                True,
                None,
                [],
                FIXTURE_PATH.joinpath("list.json"),
                id="list-json",
            ),
            pytest.param(
                False,
                "{id} {title} {url}",
                [],
                FIXTURE_PATH.joinpath("list-format.txt"),
                id="list-custom-format",
            ),
            pytest.param(
                False,
                None,
                ["BookmarksBar"],
                FIXTURE_PATH.joinpath("list-target.txt"),
                id="list-target",
            ),
            pytest.param(
                False,
                None,
                ["BookmarksBar", "Safari Bookmarks CLI"],
                FIXTURE_PATH.joinpath("list-leaf.txt"),
                id="list-leaf",
            ),
            pytest.param(
                False,
                None,
                ["B441CA58-1880-4151-929E-743090B66587"],
                FIXTURE_PATH.joinpath("list-leaf.txt"),
                id="list-uuid",
            ),
        ],
    )
    def test_list(
        self,
        cli: CLI,
        json: bool,
        format: str,
        path: List[str],
        fixture_path: Path,
    ):
        with fixture_path.open("r") as file:
            cli.list(json=json, format=format, path=path)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("uuid", "list", "title", "url", "fixture_path"),
        [
            pytest.param(
                None,
                False,
                None,
                "http://example.com",
                FIXTURE_PATH.joinpath("add-fixed-uuid-no-title-leaf.txt"),
                id="leaf-url",
            ),
            pytest.param(
                "38691E76-D8F0-4946-B68D-370213EFEB9E",
                False,
                None,
                "http://example.com",
                FIXTURE_PATH.joinpath("add-no-title-leaf.txt"),
                id="leaf-uuid-url",
            ),
            pytest.param(
                None,
                False,
                "Example",
                "http://example.com",
                FIXTURE_PATH.joinpath("add-fixed-uuid-leaf.txt"),
                id="leaf-title-url",
            ),
            pytest.param(
                "38691E76-D8F0-4946-B68D-370213EFEB9E",
                False,
                "Example",
                "http://example.com",
                FIXTURE_PATH.joinpath("add-leaf.txt"),
                id="leaf-uuid-title-url",
            ),
            pytest.param(
                "38691E76-D8F0-4946-B68D-370213EFEB9E",
                True,
                "Example",
                None,
                FIXTURE_PATH.joinpath("add-list.txt"),
                id="list-uuid-title",
            ),
            pytest.param(
                None,
                True,
                "Example",
                None,
                FIXTURE_PATH.joinpath("add-fixed-uuid-list.txt"),
                id="list-title",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "path", [["3B5180DB-831D-4F1A-AE4A-6482D28D66D5"], ["BookmarksMenu"]]
    )
    def test_add__valid(
        self,
        cli: CLI,
        uuid: Optional[str],
        list: bool,
        title: Optional[str],
        url: Optional[str],
        path: List[str],
        fixture_path: Path,
        monkeypatch,
    ):
        with (
            fixture_path.open("r") as file,
            monkeypatch.context() as m,
        ):
            m.setattr("uuid.uuid4", lambda: "8693E85C-83FC-4F42-AFB2-40B9CFACAAA0")
            cli.add(uuid=uuid, list=list, title=title, url=url, path=path)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("list", "uuid", "title", "url", "path", "error"),
        [
            pytest.param(
                True,
                None,
                None,
                None,
                [],
                "Title is required",
                id="missing-title",
            ),
            pytest.param(
                True,
                None,
                "Example",
                "http://example.com",
                [],
                "URL is not supported by lists",
                id="with-url",
            ),
            pytest.param(
                False,
                None,
                "Example",
                "http://example.com",
                ["AB38D373-1266-495A-8CAC-422A771CF70A"],
                "Invalid destination",
                id="leaf-target",
            ),
            pytest.param(
                False,
                None,
                "Example",
                "http://example.com",
                ["F1DF1813-B60B-461A-B497-51AF24AD2925"],
                "Invalid destination",
                id="nonexistent-uuid",
            ),
            pytest.param(
                False,
                None,
                "Example",
                "http://example.com",
                ["Unknown"],
                "Invalid destination",
                id="nonexistent-title",
            ),
        ],
    )
    def test_add__invalid(
        self,
        cli: CLI,
        list: bool,
        uuid: Optional[str],
        title: Optional[str],
        url: Optional[str],
        path: List[str],
        error: str,
    ):
        with pytest.raises(ValueError, match=error):
            cli.add(list=list, uuid=uuid, title=title, url=url, path=path)

    @pytest.mark.parametrize(
        ("path", "fixture_path"),
        [
            pytest.param(
                ["B441CA58-1880-4151-929E-743090B66587"],
                FIXTURE_PATH.joinpath("remove-leaf.txt"),
                id="remove-leaf-by-uuid",
            ),
            pytest.param(
                ["BookmarksBar", "Safari Bookmarks CLI"],
                FIXTURE_PATH.joinpath("remove-leaf.txt"),
                id="remove-leaf-by-title",
            ),
            pytest.param(
                ["3B5180DB-831D-4F1A-AE4A-6482D28D66D5"],
                FIXTURE_PATH.joinpath("remove-list.txt"),
                id="remove-list-by-uuid",
            ),
            pytest.param(
                ["BookmarksBar"],
                FIXTURE_PATH.joinpath("remove-list.txt"),
                id="remove-list-by-title",
            ),
        ],
    )
    def test_remove__valid(self, cli: CLI, path: List[str], fixture_path: Path):
        with fixture_path.open("r") as file:
            cli.remove(path=path)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("path", "error"),
        [
            pytest.param(
                ["BF7BB6D9-AF1D-4B5C-A95A-7765E9C5B199"],
                "Target not found",
                id="uuid",
            ),
            pytest.param(
                ["Unknown"],
                "Target not found",
                id="title",
            ),
        ],
    )
    def test_remove__invalid(self, cli: CLI, path: List[str], error: str):
        with pytest.raises(ValueError, match=error):
            cli.remove(path=path)

    @pytest.mark.parametrize(
        ("path", "to", "fixture_path"),
        [
            pytest.param(
                ["AB38D373-1266-495A-8CAC-422A771CF70A"],
                ["20ABDC16-B491-47F4-B252-2A3065CFB895"],
                FIXTURE_PATH.joinpath("move-leaf.txt"),
                id="leaf-by-uuid",
            ),
            pytest.param(
                ["BookmarksBar", "Safari"],
                ["BookmarksMenu"],
                FIXTURE_PATH.joinpath("move-leaf.txt"),
                id="leaf-by-title",
            ),
            pytest.param(
                ["3B5180DB-831D-4F1A-AE4A-6482D28D66D5"],
                ["20ABDC16-B491-47F4-B252-2A3065CFB895"],
                FIXTURE_PATH.joinpath("move-list.txt"),
                id="list-by-uuid",
            ),
            pytest.param(
                ["BookmarksBar"],
                ["BookmarksMenu"],
                FIXTURE_PATH.joinpath("move-list.txt"),
                id="list-by-title",
            ),
        ],
    )
    def test_move__valid(
        self, cli: CLI, path: List[str], to: List[str], fixture_path: Path
    ):
        with fixture_path.open("r") as file:
            cli.move(path=path, to=to)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("path", "to", "error"),
        [
            pytest.param(
                ["BF7BB6D9-AF1D-4B5C-A95A-7765E9C5B199"],
                ["BookmarksMenu"],
                "Target not found",
                id="nonexistent-target-by-uuid",
            ),
            pytest.param(
                ["Unknown"],
                ["BookmarksMenu"],
                "Target not found",
                id="nonexistent-target-by-title",
            ),
            pytest.param(
                ["AB38D373-1266-495A-8CAC-422A771CF70A"],
                ["41BA6DB5-4D97-4921-ADC6-4418D1824DF4"],
                "Invalid destination",
                id="nonexistent-destination-by-uuid",
            ),
            pytest.param(
                ["AB38D373-1266-495A-8CAC-422A771CF70A"],
                ["Unknown"],
                "Invalid destination",
                id="nonexistent-destination-by-title",
            ),
            pytest.param(
                ["AB38D373-1266-495A-8CAC-422A771CF70A"],
                [],
                "Missing destination",
                id="missing-destination",
            ),
        ],
    )
    def test_move__invalid(self, cli: CLI, path: List[str], to: List[str], error: str):
        with pytest.raises(ValueError, match=error):
            cli.move(path=path, to=to)

    @pytest.mark.parametrize(
        ("path", "title", "url", "fixture_path"),
        [
            pytest.param(
                ["AB38D373-1266-495A-8CAC-422A771CF70A"],
                "Updated example",
                None,
                FIXTURE_PATH.joinpath("edit-title-leaf.txt"),
                id="leaf-title",
            ),
            pytest.param(
                ["AB38D373-1266-495A-8CAC-422A771CF70A"],
                None,
                "http://example.com",
                FIXTURE_PATH.joinpath("edit-url-leaf.txt"),
                id="leaf-url",
            ),
            pytest.param(
                ["AB38D373-1266-495A-8CAC-422A771CF70A"],
                "Updated example",
                "http://example.com",
                FIXTURE_PATH.joinpath("edit-title-url-leaf.txt"),
                id="leaf-title-and-url",
            ),
            pytest.param(
                ["3B5180DB-831D-4F1A-AE4A-6482D28D66D5"],
                "Updated example",
                None,
                FIXTURE_PATH.joinpath("edit-title-list.txt"),
                id="list-title",
            ),
        ],
    )
    def test_edit__valid(
        self,
        cli: CLI,
        path: List[str],
        title: Optional[str],
        url: Optional[str],
        fixture_path: Path,
    ):
        with fixture_path.open("r") as file:
            cli.edit(path=path, title=title, url=url)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("path", "title", "url", "error"),
        [
            pytest.param(
                ["F04ABC44-9C55-437E-A19D-B63ED24FC185"],
                "Example",
                "http://example.com",
                "Target not found",
                id="nonexistent-uuid",
            ),
            pytest.param(
                ["Unknown"],
                "Example",
                "http://example.com",
                "Target not found",
                id="nonexistent-title",
            ),
            pytest.param(
                ["3B5180DB-831D-4F1A-AE4A-6482D28D66D5"],
                None,
                "http://example.com",
                "Cannot update target url",
                id="list-url",
            ),
        ],
    )
    def test_edit__invalid(
        self,
        cli: CLI,
        path: List[str],
        title: Optional[str],
        url: Optional[str],
        error: str,
    ):
        with pytest.raises(ValueError, match=error):
            cli.edit(path=path, title=title, url=url)

    @pytest.mark.parametrize(
        ("path", "fixture_path"),
        [
            pytest.param(
                ["BookmarksBar"], FIXTURE_PATH.joinpath("empty.txt"), id="list-title"
            ),
            pytest.param(
                ["3B5180DB-831D-4F1A-AE4A-6482D28D66D5"],
                FIXTURE_PATH.joinpath("empty.txt"),
                id="list-uuid",
            ),
        ],
    )
    def test_empty__valid(self, cli: CLI, path: List[str], fixture_path: Path):
        with fixture_path.open("r") as file:
            cli.empty(path=path)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("path", "error"),
        [
            pytest.param(
                ["F04ABC44-9C55-437E-A19D-B63ED24FC185"],
                "Target not found",
                id="nonexistent-uuid",
            ),
            pytest.param(
                ["Unknown"],
                "Target not found",
                id="nonexistent-title",
            ),
            pytest.param(
                ["1E830274-3DB6-42F2-BE8E-14E2BA75418C"],
                "Target is not a list",
                id="leaf",
            ),
        ],
    )
    def test_empty__invalid(self, cli: CLI, path: List[str], error: str):
        with pytest.raises(ValueError, match=error):
            cli.empty(path=path)
