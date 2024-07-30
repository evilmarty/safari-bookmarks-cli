from contextlib import nullcontext
from datetime import datetime
from hashlib import sha1
from io import BytesIO
from pathlib import Path
import plistlib
import pytest

from safaribookmarks.models import (
    WebBookmarkType,
    WebBookmarkTypeList,
    WebBookmarkTypeLeaf,
    WebBookmarkTypeProxy,
)
from safaribookmarks.safaribookmarks import (
    SafariBookmarkItem,
    SafariBookmarks,
)

BOOKMARKS_BINARY_PATH = Path(__file__).parent.joinpath(
    "support", "fixtures", "Bookmarks.bin"
)
BOOKMARKS_XML_PATH = Path(__file__).parent.joinpath(
    "support", "fixtures", "Bookmarks.xml"
)


@pytest.fixture
def webbookmark_type():
    return WebBookmarkType(
        WebBookmarkUUID="ffd5477c-0df6-404c-b0db-0fa0d62cfff4",
    )


@pytest.fixture
def webbookmark_leaf():
    return WebBookmarkTypeLeaf(
        WebBookmarkUUID="40ebd9a6-c962-4a05-b382-c796c5127732",
        URLString="http://example.com",
        URIDictionary={"title": "Example Leaf"},
    )


@pytest.fixture
def webbookmark_list(webbookmark_leaf):
    return WebBookmarkTypeList(
        WebBookmarkUUID="ddea80d2-e7dd-4ec9-805f-90a2ba4242de",
        Title="Example List",
        Children=[webbookmark_leaf],
    )


@pytest.fixture
def webbookmark_proxy():
    return WebBookmarkTypeProxy(
        WebBookmarkUUID="9d55309e-d318-4a34-a911-33cacaf1d6d2",
        Title="Example Proxy",
    )


class TestSafariBookmarkItem:
    @pytest.fixture
    def type_item(self, webbookmark_type):
        return SafariBookmarkItem(webbookmark_type)

    @pytest.fixture
    def leaf_item(self, webbookmark_leaf):
        return SafariBookmarkItem(webbookmark_leaf)

    @pytest.fixture
    def list_item(self, webbookmark_list):
        return SafariBookmarkItem(webbookmark_list)

    @pytest.fixture
    def proxy_item(self, webbookmark_proxy):
        return SafariBookmarkItem(webbookmark_proxy)

    @pytest.fixture
    def safaribookmarks(self):
        return SafariBookmarks(WebBookmarkTypeList(Title=""))

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", ""),
            ("leaf_item", "Example Leaf"),
            ("list_item", "Example List"),
            ("proxy_item", "Example Proxy"),
        ],
    )
    def test_str(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        actual = str(subject)
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", 0),
            ("leaf_item", 0),
            ("list_item", 1),
            ("proxy_item", 0),
        ],
    )
    def test_len(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        actual = len(subject)
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture"),
        [
            "type_item",
            "leaf_item",
            "list_item",
            "proxy_item",
        ],
    )
    def test_hash(self, request, fixture):
        subject = request.getfixturevalue(fixture)
        expected = hash(subject._node)
        actual = hash(subject)
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "key", "expected"),
        [
            ("type_item", "Unknown", KeyError("Unknown")),
            ("leaf_item", "Unknown", KeyError("Unknown")),
            ("proxy_item", "Unknown", KeyError("Unknown")),
            ("list_item", 1, TypeError("int")),
            ("list_item", "Unknown", KeyError("Unknown")),
            ("list_item", "Example Leaf", "leaf_item"),
            ("list_item", tuple(["Example Leaf"]), "leaf_item"),
            ("list_item", "40ebd9a6-c962-4a05-b382-c796c5127732", "leaf_item"),
            ("list_item", tuple(["40ebd9a6-c962-4a05-b382-c796c5127732"]), "leaf_item"),
        ],
    )
    def test_getitem(self, request, fixture, key, expected):
        subject = request.getfixturevalue(fixture)
        with maybe_raises(expected):
            actual = subject[key]
            expected = request.getfixturevalue(expected)
            assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", False),
            ("leaf_item", False),
            ("list_item", True),
            ("proxy_item", False),
        ],
    )
    def test_contains(self, request, fixture, expected, leaf_item):
        subject = request.getfixturevalue(fixture)
        actual = leaf_item in subject
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", False),
            ("leaf_item", True),
            ("list_item", True),
            ("proxy_item", False),
            ("safaribookmarks", False),
        ],
    )
    def test_movable(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        actual = subject.movable
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", "ffd5477c-0df6-404c-b0db-0fa0d62cfff4"),
            ("leaf_item", "40ebd9a6-c962-4a05-b382-c796c5127732"),
            ("list_item", "ddea80d2-e7dd-4ec9-805f-90a2ba4242de"),
            ("proxy_item", "9d55309e-d318-4a34-a911-33cacaf1d6d2"),
        ],
    )
    def test_id(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        actual = subject.id
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", ""),
            ("leaf_item", "Example Leaf"),
            ("list_item", "Example List"),
            ("proxy_item", "Example Proxy"),
        ],
    )
    def test_title(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        actual = subject.title
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "attr", "expected"),
        [
            ("type_item", "title", None),
            ("leaf_item", "uri_dictionary", {"title": "Updated title"}),
            ("list_item", "title", "Updated title"),
            ("proxy_item", "title", "Updated title"),
        ],
    )
    def test_set_title(self, request, fixture, attr, expected):
        subject = request.getfixturevalue(fixture)
        subject.title = "Updated title"
        actual = getattr(subject._node, attr, None)
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", ""),
            ("leaf_item", "http://example.com"),
            ("list_item", ""),
            ("proxy_item", ""),
        ],
    )
    def test_url(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        actual = subject.url
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", None),
            ("leaf_item", "http://example.com/updated"),
            ("list_item", None),
            ("proxy_item", None),
        ],
    )
    def test_set_url(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        subject.url = "http://example.com/updated"
        actual = getattr(subject._node, "url_string", None)
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", False),
            ("leaf_item", False),
            ("list_item", True),
            ("proxy_item", False),
        ],
    )
    def test_is_folder(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        actual = subject.is_folder
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "expected"),
        [
            ("type_item", False),
            ("leaf_item", True),
            ("list_item", False),
            ("proxy_item", False),
        ],
    )
    def test_is_bookmark(self, request, fixture, expected):
        subject = request.getfixturevalue(fixture)
        actual = subject.is_bookmark
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "error"),
        [
            ("type_item", True),
            ("leaf_item", True),
            ("list_item", False),
            ("proxy_item", True),
        ],
    )
    def test_parent(self, request, fixture, error, leaf_item):
        item = request.getfixturevalue(fixture)
        if error:
            context = pytest.raises(ValueError, match="Parent must be a folder")
        else:
            context = nullcontext()
        with context:
            subject = SafariBookmarkItem(node=leaf_item, parent=item)
            assert subject.parent == item

    @pytest.mark.parametrize(
        ("id", "expected"),
        [
            ("ddea80d2-e7dd-4ec9-805f-90a2ba4242de", "list_item"),
            ("40ebd9a6-c962-4a05-b382-c796c5127732", "leaf_item"),
            ("e87c8d46-a0e6-410c-9ec3-03c9d4bf68ba", None),
        ],
    )
    def test_get(self, request, list_item, id, expected):
        if expected is not None:
            expected = request.getfixturevalue(expected)
        actual = list_item.get(id)
        assert actual == expected

    @pytest.mark.parametrize(
        ("titles", "expected"),
        [
            ([], "list_item"),
            (["Example List"], None),
            (["Example Leaf"], "leaf_item"),
            (["Example Leaf", "Unknown"], None),
        ],
    )
    def test_walk(self, request, list_item, titles, expected):
        if expected is not None:
            expected = request.getfixturevalue(expected)
        actual = list_item.walk(*titles)
        assert actual == expected

    @pytest.mark.parametrize(
        ("fixture", "error"),
        [
            ("type_item", RuntimeError("Not a child")),
            ("leaf_item", RuntimeError("Not a child")),
            ("list_item", None),
            ("proxy_item", RuntimeError("Not a child")),
        ],
    )
    def test_remove(self, request, fixture, error, leaf_item):
        subject = request.getfixturevalue(fixture)
        with maybe_raises(error):
            leaf_item._parent = subject  # Slight hack to pretend we're a child
            subject.remove(leaf_item)
            assert leaf_item not in subject
            assert leaf_item.parent is None

    @pytest.mark.parametrize(
        ("fixture"),
        [
            "type_item",
            "proxy_item",
        ],
    )
    def test_remove_error(self, request, list_item, fixture):
        item = request.getfixturevalue(fixture)
        list_item._node.children.append(item._node)  # Force make us a child
        with pytest.raises(RuntimeError, match="Invalid item"):
            list_item.remove(item)

    def test_empty(self, list_item):
        assert len(list_item) > 0
        list_item.empty()
        assert len(list_item) == 0

    @pytest.mark.parametrize(
        ("fixture", "error"),
        [
            ("type_item", RuntimeError("Not a folder")),
            ("leaf_item", RuntimeError("Not a folder")),
            ("list_item", None),
            ("proxy_item", RuntimeError("Not a folder")),
        ],
    )
    def test_append(self, request, fixture, error):
        item = SafariBookmarkItem(WebBookmarkTypeLeaf(URLString="http://foobar.com"))
        subject = request.getfixturevalue(fixture)
        with maybe_raises(error):
            subject.append(item)
            assert item in subject
            assert item.parent == subject

    @pytest.mark.parametrize(
        ("fixture"),
        [
            "type_item",
            "proxy_item",
            "safaribookmarks",
        ],
    )
    def test_append_error(self, request, list_item, fixture):
        item = request.getfixturevalue(fixture)
        with pytest.raises(RuntimeError, match="Invalid item"):
            list_item.append(item)

    @pytest.mark.parametrize(
        ("fixture", "kwargs", "expected"),
        [
            (
                "type_item",
                {
                    "url": "http://foobar.com",
                    "title": "Foobar",
                    "id": "9fa833bb-e4e3-4d4a-9007-3cdbe7873540",
                },
                RuntimeError("Not a folder"),
            ),
            (
                "leaf_item",
                {
                    "url": "http://foobar.com",
                    "title": "Foobar",
                    "id": "9fa833bb-e4e3-4d4a-9007-3cdbe7873540",
                },
                RuntimeError("Not a folder"),
            ),
            (
                "list_item",
                {
                    "url": "http://foobar.com",
                    "title": "Foobar",
                    "id": "9fa833bb-e4e3-4d4a-9007-3cdbe7873540",
                },
                SafariBookmarkItem(
                    WebBookmarkTypeLeaf(
                        URLString="http://foobar.com",
                        URIDictionary={"title": "Foobar"},
                        WebBookmarkUUID="9fa833bb-e4e3-4d4a-9007-3cdbe7873540",
                    )
                ),
            ),
            (
                "proxy_item",
                {
                    "url": "http://foobar.com",
                    "title": "Foobar",
                    "id": "9fa833bb-e4e3-4d4a-9007-3cdbe7873540",
                },
                RuntimeError("Not a folder"),
            ),
        ],
    )
    def test_add_bookmark(self, request, fixture, kwargs, expected):
        subject = request.getfixturevalue(fixture)
        with maybe_raises(expected):
            actual = subject.add_bookmark(**kwargs)
            assert actual == expected
            assert actual in subject
            assert actual.parent == subject

    @pytest.mark.parametrize(
        ("fixture", "kwargs", "expected"),
        [
            (
                "type_item",
                {
                    "title": "Foobar",
                    "id": "4f9881bf-0ab4-4187-a736-9694873aa655",
                },
                RuntimeError("Not a folder"),
            ),
            (
                "leaf_item",
                {
                    "title": "Foobar",
                    "id": "4f9881bf-0ab4-4187-a736-9694873aa655",
                },
                RuntimeError("Not a folder"),
            ),
            (
                "list_item",
                {
                    "title": "Foobar",
                    "id": "4f9881bf-0ab4-4187-a736-9694873aa655",
                },
                SafariBookmarkItem(
                    WebBookmarkTypeList(
                        Title="Foobar",
                        WebBookmarkUUID="4f9881bf-0ab4-4187-a736-9694873aa655",
                    )
                ),
            ),
            (
                "proxy_item",
                {
                    "title": "Foobar",
                    "id": "4f9881bf-0ab4-4187-a736-9694873aa655",
                },
                RuntimeError("Not a folder"),
            ),
        ],
    )
    def test_add_folder(self, request, fixture, kwargs, expected):
        subject = request.getfixturevalue(fixture)
        with maybe_raises(expected):
            actual = subject.add_folder(**kwargs)
            assert actual == expected
            assert actual in subject
            assert actual.parent == subject


class TestSafariBookmarks:
    @pytest.fixture()
    def root(self) -> WebBookmarkTypeList:
        return WebBookmarkTypeList(
            WebBookmarkUUID="A7E466BC-FB29-41AE-880C-D21E3CAEBA5A",
            WebBookmarkType="WebBookmarkTypeList",
            Title="",
            Children=[
                WebBookmarkTypeProxy(
                    WebBookmarkUUID="7551D1F4-38C1-4DB3-88AC-90C15F10338D",
                    WebBookmarkType="WebBookmarkTypeProxy",
                    Title="History",
                    WebBookmarkIdentifier="History",
                ),
                WebBookmarkTypeList(
                    WebBookmarkUUID="3B5180DB-831D-4F1A-AE4A-6482D28D66D5",
                    WebBookmarkType="WebBookmarkTypeList",
                    Title="BookmarksBar",
                    Children=[
                        WebBookmarkTypeLeaf(
                            WebBookmarkUUID="B441CA58-1880-4151-929E-743090B66587",
                            WebBookmarkType="WebBookmarkTypeLeaf",
                            URLString="https://github.com/evilmarty/safari-bookmarks-cli",
                            URIDictionary={"title": "Safari Bookmarks CLI"},
                            ReadingListNonSync={"neverFetchMetadata": False},
                        ),
                        WebBookmarkTypeLeaf(
                            WebBookmarkUUID="1E830274-3DB6-42F2-BE8E-14E2BA75418C",
                            WebBookmarkType="WebBookmarkTypeLeaf",
                            URLString="https://www.python.org",
                            URIDictionary={"title": "Python"},
                            ReadingListNonSync={"neverFetchMetadata": False},
                        ),
                        WebBookmarkTypeLeaf(
                            WebBookmarkUUID="AB38D373-1266-495A-8CAC-422A771CF70A",
                            WebBookmarkType="WebBookmarkTypeLeaf",
                            URLString="http://apple.com/safari",
                            URIDictionary={"title": "Safari"},
                            ReadingListNonSync={"neverFetchMetadata": False},
                        ),
                    ],
                ),
                WebBookmarkTypeList(
                    WebBookmarkUUID="20ABDC16-B491-47F4-B252-2A3065CFB895",
                    WebBookmarkType="WebBookmarkTypeList",
                    Title="BookmarksMenu",
                    Children=[],
                ),
                WebBookmarkTypeList(
                    WebBookmarkUUID="E3B5B464-B6D2-457C-9F62-7B2316F7EF20",
                    WebBookmarkType="WebBookmarkTypeList",
                    Title="com.apple.ReadingList",
                    Children=[
                        WebBookmarkTypeLeaf(
                            WebBookmarkUUID="F32FEDBB-7653-48FE-95C3-458B01EF2A4F",
                            WebBookmarkType="WebBookmarkTypeLeaf",
                            URLString="https://linuxfromscratch.org/lfs/view/development/",
                            URIDictionary={"title": "Linux From Scratch"},
                            ReadingListNonSync={
                                "didAttemptToFetchIconFromImageUrlKey": True,
                                "neverFetchMetadata": False,
                            },
                            ReadingList={
                                "DateAdded": datetime(2022, 3, 2, 2, 30, 51),
                                "PreviewText": (
                                    "Linux From Scratch Version r11.0-199 Published February 26th, 2022 Created by Gerard "
                                    "Beekmans Managing Editor: Bruce Dubbs Copyright © 1999-2022 Gerard Beekmans Table of "
                                    "Contents Preface Foreword Audience LFS Target A"
                                ),
                            },
                            imageURL="",
                        ),
                        WebBookmarkTypeLeaf(
                            WebBookmarkUUID="74B28EA6-2E11-4F73-848B-5439B9802822",
                            WebBookmarkType="WebBookmarkTypeLeaf",
                            URLString="https://frontend.horse/articles/generative-grids/",
                            URIDictionary={"title": "Creating Generative SVG Grids"},
                            ReadingListNonSync={
                                "AddedLocally": True,
                                "DateLastFetched": datetime(2022, 2, 9, 21, 9, 27),
                                "FetchResult": 1,
                                "didAttemptToFetchIconFromImageUrlKey": True,
                                "neverFetchMetadata": False,
                                "siteName": "Frontend Horse",
                            },
                            ReadingList={
                                "DateAdded": datetime(2022, 2, 9, 21, 9, 26),
                                "PreviewText": (
                                    "Learn how to create colorful, generative grid designs with JavaScript and SVG!"
                                ),
                            },
                            imageURL="https://frontend.horse/static/d70d16675d20860a230a6b1e76dfba62/share.png",
                        ),
                    ],
                    ShouldOmitFromUI=True,
                ),
            ],
            WebBookmarkFileVersion=1,
            Sync={
                "CloudKitDeviceIdentifier": "06E15A3A03BD93165AE80C02E19C86CD1E52B84F8DA8BE82B889CD2DCE0B2279",
                "CloudKitMigrationState": 0,
            },
        )

    @pytest.fixture
    def subject(self, root):
        return SafariBookmarks(root)

    @pytest.mark.parametrize(
        ("path", "binary"),
        [
            (BOOKMARKS_BINARY_PATH, True),
            (BOOKMARKS_XML_PATH, False),
        ],
    )
    def test_load(self, path: Path, binary: bool, subject):
        with path.open("rb") as file:
            assert subject == SafariBookmarks.load(file, binary=binary)

    @pytest.mark.parametrize(
        ("path", "binary"),
        [
            (BOOKMARKS_BINARY_PATH, True),
            (BOOKMARKS_XML_PATH, False),
        ],
    )
    def test_load__error(self, path: Path, binary: bool):
        with (
            pytest.raises(IOError, match="Must be in binary mode"),
            path.open("r") as file,
        ):
            SafariBookmarks.load(file, binary=binary)

    @pytest.mark.parametrize(
        ("digest", "binary"),
        [
            ("ac34fa864fc62a2decf219cf3df78fd1da7ec25d", True),
            ("1b7a31279c90fe6775f8d93fa2e2c202d4e8bca8", False),
        ],
    )
    def test_dump(self, digest: str, binary: bool, subject):
        with BytesIO() as buf:
            subject.dump(buf, binary=binary)
            buf.seek(0)
            assert digest == sha1(buf.read()).hexdigest()

    @pytest.mark.parametrize(
        ("binary"),
        [True, False],
    )
    def test_dump__error(self, tmp_path: Path, binary: bool, subject):
        with (
            pytest.raises(IOError, match="Must be in binary mode"),
            tmp_path.joinpath("bookmarks").open("w") as file,
        ):
            subject.dump(file, binary=binary)


def maybe_raises(error, **kwargs):
    if isinstance(error, BaseException):
        return pytest.raises(type(error), match=str(error), **kwargs)
    elif error == type and issubclass(error, BaseException):
        return pytest.raises(error, **kwargs)
    else:
        return nullcontext()
