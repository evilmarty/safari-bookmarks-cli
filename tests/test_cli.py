from argparse import Namespace
from io import StringIO
import pytest
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from safaribookmarks.cli import CLI

FIXTURE_PATH = Path(__file__).parent.joinpath("support", "fixtures")
BOOKMARKS_BINARY_PATH = FIXTURE_PATH.joinpath("Bookmarks.bin")


class TestCLI:
    @pytest.fixture()
    def bookmarks_path(self) -> None:
        with TemporaryDirectory() as dir:
            dest = Path(dir).joinpath("Bookmarks.plist")
            copyfile(BOOKMARKS_BINARY_PATH, dest)
            yield dest

    @pytest.fixture()
    def cli(self, bookmarks_path) -> CLI:
        return CLI(bookmarks_path, StringIO())

    @pytest.mark.parametrize(
        ("args", "fixture_path"),
        [
            pytest.param(
                Namespace(json=False, format=None, target=None),
                FIXTURE_PATH.joinpath("list.txt"),
                id="list-text",
            ),
            pytest.param(
                Namespace(json=True, format=None, target=None),
                FIXTURE_PATH.joinpath("list.json"),
                id="list-json",
            ),
            pytest.param(
                Namespace(json=False, format="{id} {title} {url}", target=None),
                FIXTURE_PATH.joinpath("list-format.txt"),
                id="list-custom-format",
            ),
            pytest.param(
                Namespace(json=False, format=None, target="BookmarksBar"),
                FIXTURE_PATH.joinpath("list-target.txt"),
                id="list-target",
            ),
        ],
    )
    def test_list(self, cli: CLI, args: Namespace, fixture_path: Path):
        with fixture_path.open("r") as file:
            cli.list(args)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("args", "fixture_path"),
        [
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    uuid=None,
                    list=False,
                    title=None,
                    url="http://example.com",
                ),
                FIXTURE_PATH.joinpath("add-fixed-uuid-no-title-leaf.txt"),
                id="leaf-url",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    uuid="38691E76-D8F0-4946-B68D-370213EFEB9E",
                    list=False,
                    title=None,
                    url="http://example.com",
                ),
                FIXTURE_PATH.joinpath("add-no-title-leaf.txt"),
                id="leaf-uuid-url",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    uuid=None,
                    list=False,
                    title="Example",
                    url="http://example.com",
                ),
                FIXTURE_PATH.joinpath("add-fixed-uuid-leaf.txt"),
                id="leaf-title-url",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    uuid="38691E76-D8F0-4946-B68D-370213EFEB9E",
                    list=False,
                    title="Example",
                    url="http://example.com",
                ),
                FIXTURE_PATH.joinpath("add-leaf.txt"),
                id="leaf-uuid-title-url",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    uuid="38691E76-D8F0-4946-B68D-370213EFEB9E",
                    list=True,
                    title="Example",
                    url=None,
                ),
                FIXTURE_PATH.joinpath("add-list.txt"),
                id="list-uuid-title",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    uuid=None,
                    list=True,
                    title="Example",
                    url=None,
                ),
                FIXTURE_PATH.joinpath("add-fixed-uuid-list.txt"),
                id="list-title",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "to", [None, "3B5180DB-831D-4F1A-AE4A-6482D28D66D5", "BookmarksMenu"]
    )
    def test_add__valid(
        self, cli: CLI, args: Namespace, fixture_path: Path, to: str, monkeypatch
    ):
        with (
            fixture_path.open("r") as file,
            monkeypatch.context() as m,
        ):
            m.setattr("uuid.uuid4", lambda: "8693E85C-83FC-4F42-AFB2-40B9CFACAAA0")
            args.to = to
            cli.add(args)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("args", "error"),
        [
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    list=True,
                    uuid=None,
                    title=None,
                    url=None,
                    to=None,
                ),
                "Title is required",
                id="missing-title",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    list=True,
                    uuid=None,
                    title="Example",
                    url="http://example.com",
                    to=None,
                ),
                "URL is not supported by lists",
                id="with-url",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    list=False,
                    uuid=None,
                    title="Example",
                    url="http://example.com",
                    to="AB38D373-1266-495A-8CAC-422A771CF70A",
                ),
                "Invalid destination",
                id="leaf-target",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    list=False,
                    uuid=None,
                    title="Example",
                    url="http://example.com",
                    to="F1DF1813-B60B-461A-B497-51AF24AD2925",
                ),
                "Invalid destination",
                id="nonexistent-uuid",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    list=False,
                    uuid=None,
                    title="Example",
                    url="http://example.com",
                    to="Unknown",
                ),
                "Invalid destination",
                id="nonexistent-title",
            ),
        ],
    )
    def test_add__invalid(self, cli: CLI, args: Namespace, error: str):
        with pytest.raises(ValueError, match=error):
            cli.add(args)

    @pytest.mark.parametrize(
        ("args", "fixture_path"),
        [
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    targets=["B441CA58-1880-4151-929E-743090B66587"],
                ),
                FIXTURE_PATH.joinpath("remove-leaf.txt"),
                id="remove-leaf-by-uuid",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    targets=["Safari Bookmarks CLI"],
                ),
                FIXTURE_PATH.joinpath("remove-leaf.txt"),
                id="remove-leaf-by-title",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    targets=["3B5180DB-831D-4F1A-AE4A-6482D28D66D5"],
                ),
                FIXTURE_PATH.joinpath("remove-list.txt"),
                id="remove-list-by-uuid",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    targets=["BookmarksBar"],
                ),
                FIXTURE_PATH.joinpath("remove-list.txt"),
                id="remove-list-by-title",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    targets=["Python", "Safari"],
                ),
                FIXTURE_PATH.joinpath("remove-multiple.txt"),
                id="remove-multiple",
            ),
        ],
    )
    def test_remove__valid(self, cli: CLI, args: Namespace, fixture_path: Path):
        with fixture_path.open("r") as file:
            cli.remove(args)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("args", "error"),
        [
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    targets=["BF7BB6D9-AF1D-4B5C-A95A-7765E9C5B199"],
                ),
                "Target not found",
                id="uuid",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    targets=["Unknown"],
                ),
                "Target not found",
                id="title",
            ),
        ],
    )
    def test_remove__invalid(self, cli: CLI, args: Namespace, error: str):
        with pytest.raises(ValueError, match=error):
            cli.remove(args)

    @pytest.mark.parametrize(
        ("args", "fixture_path"),
        [
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="AB38D373-1266-495A-8CAC-422A771CF70A",
                    to="20ABDC16-B491-47F4-B252-2A3065CFB895",
                ),
                FIXTURE_PATH.joinpath("move-leaf.txt"),
                id="leaf-by-uuid",
            ),
            pytest.param(
                Namespace(json=False, format=None, target="Safari", to="BookmarksMenu"),
                FIXTURE_PATH.joinpath("move-leaf.txt"),
                id="leaf-by-title",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="3B5180DB-831D-4F1A-AE4A-6482D28D66D5",
                    to="20ABDC16-B491-47F4-B252-2A3065CFB895",
                ),
                FIXTURE_PATH.joinpath("move-list.txt"),
                id="list-by-uuid",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="BookmarksBar",
                    to="BookmarksMenu",
                ),
                FIXTURE_PATH.joinpath("move-list.txt"),
                id="list-by-title",
            ),
        ],
    )
    def test_move__valid(self, cli: CLI, args: Namespace, fixture_path: Path):
        with fixture_path.open("r") as file:
            cli.move(args)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("args", "error"),
        [
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="BF7BB6D9-AF1D-4B5C-A95A-7765E9C5B199",
                    to="BookmarksMenu",
                ),
                "Target not found",
                id="nonexistent-target-by-uuid",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="Unknown",
                    to="BookmarksMenu",
                ),
                "Target not found",
                id="nonexistent-target-by-title",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="AB38D373-1266-495A-8CAC-422A771CF70A",
                    to="41BA6DB5-4D97-4921-ADC6-4418D1824DF4",
                ),
                "Invalid destination",
                id="nonexistent-destination-by-uuid",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="AB38D373-1266-495A-8CAC-422A771CF70A",
                    to="Unknown",
                ),
                "Invalid destination",
                id="nonexistent-destination-by-title",
            ),
        ],
    )
    def test_move__invalid(self, cli: CLI, args: Namespace, error: str):
        with pytest.raises(ValueError, match=error):
            cli.move(args)

    @pytest.mark.parametrize(
        ("args", "fixture_path"),
        [
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="AB38D373-1266-495A-8CAC-422A771CF70A",
                    title="Updated example",
                    url=None,
                ),
                FIXTURE_PATH.joinpath("edit-title-leaf.txt"),
                id="leaf-title",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="AB38D373-1266-495A-8CAC-422A771CF70A",
                    title=None,
                    url="http://example.com",
                ),
                FIXTURE_PATH.joinpath("edit-url-leaf.txt"),
                id="leaf-url",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="AB38D373-1266-495A-8CAC-422A771CF70A",
                    title="Updated example",
                    url="http://example.com",
                ),
                FIXTURE_PATH.joinpath("edit-title-url-leaf.txt"),
                id="leaf-title-and-url",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="3B5180DB-831D-4F1A-AE4A-6482D28D66D5",
                    title="Updated example",
                    url=None,
                ),
                FIXTURE_PATH.joinpath("edit-title-list.txt"),
                id="list-title",
            ),
        ],
    )
    def test_edit__valid(self, cli: CLI, args: Namespace, fixture_path: Path):
        with fixture_path.open("r") as file:
            cli.edit(args)
            cli.output.seek(0)
            assert file.read() == cli.output.read()

    @pytest.mark.parametrize(
        ("args", "error"),
        [
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="F04ABC44-9C55-437E-A19D-B63ED24FC185",
                    title="Example",
                    url="http://example.com",
                ),
                "Target not found",
                id="nonexistent-uuid",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="Unknown",
                    title="Example",
                    url="http://example.com",
                ),
                "Target not found",
                id="nonexistent-title",
            ),
            pytest.param(
                Namespace(
                    json=False,
                    format=None,
                    target="3B5180DB-831D-4F1A-AE4A-6482D28D66D5",
                    title=None,
                    url="http://example.com",
                ),
                "Cannot update target url",
                id="list-url",
            ),
        ],
    )
    def test_edit__invalid(self, cli: CLI, args: Namespace, error: str):
        with pytest.raises(ValueError, match=error):
            cli.edit(args)
