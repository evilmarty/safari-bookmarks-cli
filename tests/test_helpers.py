from datetime import datetime
from io import BytesIO
from hashlib import sha1
import pytest
from pathlib import Path
from plistlib import PlistFormat, FMT_XML, FMT_BINARY
from tempfile import TemporaryFile

from safaribookmarks.helpers import load, dump
from safaribookmarks.models import WebBookmarkTypeList, WebBookmarkTypeProxy, WebBookmarkTypeLeaf

BOOKMARKS_BINARY_PATH = Path(__file__).parent.joinpath("support", "fixtures", "Bookmarks.bin")
BOOKMARKS_XML_PATH = Path(__file__).parent.joinpath("support", "fixtures", "Bookmarks.xml")


@pytest.fixture()
def subject() -> WebBookmarkTypeList:
    return WebBookmarkTypeList(
        web_bookmark_uuid='A7E466BC-FB29-41AE-880C-D21E3CAEBA5A',
        web_bookmark_type='WebBookmarkTypeList',
        title='',
        children=[
            WebBookmarkTypeProxy(
                web_bookmark_uuid='7551D1F4-38C1-4DB3-88AC-90C15F10338D',
                web_bookmark_type='WebBookmarkTypeProxy',
                title='History',
                WebBookmarkIdentifier='History',
            ),
            WebBookmarkTypeList(
                web_bookmark_uuid='3B5180DB-831D-4F1A-AE4A-6482D28D66D5',
                web_bookmark_type='WebBookmarkTypeList',
                title='BookmarksBar',
                children=[
                    WebBookmarkTypeLeaf(
                        web_bookmark_uuid='B441CA58-1880-4151-929E-743090B66587',
                        web_bookmark_type='WebBookmarkTypeLeaf',
                        url_string='https://github.com/evilmarty/safari-bookmarks-cli',
                        uri_dictionary={'title': 'Safari Bookmarks CLI'},
                        ReadingListNonSync={'neverFetchMetadata': False},
                    ),
                    WebBookmarkTypeLeaf(
                        web_bookmark_uuid='1E830274-3DB6-42F2-BE8E-14E2BA75418C',
                        web_bookmark_type='WebBookmarkTypeLeaf',
                        url_string='https://www.python.org',
                        uri_dictionary={'title': 'Python'},
                        ReadingListNonSync={'neverFetchMetadata': False},
                    ),
                    WebBookmarkTypeLeaf(
                        web_bookmark_uuid='AB38D373-1266-495A-8CAC-422A771CF70A',
                        web_bookmark_type='WebBookmarkTypeLeaf',
                        url_string='http://apple.com/safari',
                        uri_dictionary={'title': 'Safari'},
                        ReadingListNonSync={'neverFetchMetadata': False},
                    ),
                ],
            ),
            WebBookmarkTypeList(
                web_bookmark_uuid='20ABDC16-B491-47F4-B252-2A3065CFB895',
                web_bookmark_type='WebBookmarkTypeList',
                title='BookmarksMenu',
                children=[],
            ),
            WebBookmarkTypeList(
                web_bookmark_uuid='E3B5B464-B6D2-457C-9F62-7B2316F7EF20',
                web_bookmark_type='WebBookmarkTypeList',
                title='com.apple.ReadingList',
                children=[
                    WebBookmarkTypeLeaf(
                        web_bookmark_uuid='F32FEDBB-7653-48FE-95C3-458B01EF2A4F',
                        web_bookmark_type='WebBookmarkTypeLeaf',
                        url_string='https://linuxfromscratch.org/lfs/view/development/',
                        uri_dictionary={'title': 'Linux From Scratch'},
                        ReadingListNonSync={
                            'didAttemptToFetchIconFromImageUrlKey': True,
                            'neverFetchMetadata': False,
                        },
                        ReadingList={
                            'DateAdded': datetime(2022, 3, 2, 2, 30, 51),
                            'PreviewText': (
                                'Linux From Scratch Version r11.0-199 Published February 26th, 2022 Created by Gerard '
                                'Beekmans Managing Editor: Bruce Dubbs Copyright © 1999-2022 Gerard Beekmans Table of '
                                'Contents Preface Foreword Audience LFS Target A'
                            ),
                        },
                        imageURL='',
                    ),
                    WebBookmarkTypeLeaf(
                        web_bookmark_uuid='74B28EA6-2E11-4F73-848B-5439B9802822',
                        web_bookmark_type='WebBookmarkTypeLeaf',
                        url_string='https://frontend.horse/articles/generative-grids/',
                        uri_dictionary={'title': 'Creating Generative SVG Grids'},
                        ReadingListNonSync={
                            'AddedLocally': True,
                            'DateLastFetched': datetime(2022, 2, 9, 21, 9, 27),
                            'FetchResult': 1,
                            'didAttemptToFetchIconFromImageUrlKey': True,
                            'neverFetchMetadata': False,
                            'siteName': 'Frontend Horse',
                        },
                        ReadingList={
                            'DateAdded': datetime(2022, 2, 9, 21, 9, 26),
                            'PreviewText': (
                                'Learn how to create colorful, generative grid designs with JavaScript and SVG!'
                            ),
                        },
                        imageURL='https://frontend.horse/static/d70d16675d20860a230a6b1e76dfba62/share.png',
                    ),
                ],
                ShouldOmitFromUI=True,
            ),
        ],
        WebBookmarkFileVersion=1,
        Sync={
            'CloudKitDeviceIdentifier': '06E15A3A03BD93165AE80C02E19C86CD1E52B84F8DA8BE82B889CD2DCE0B2279',
            'CloudKitMigrationState': 0,
        },
    )


@pytest.mark.parametrize(
    ("path", "fmt"),
    [
        (BOOKMARKS_BINARY_PATH, FMT_BINARY),
        (BOOKMARKS_BINARY_PATH, None),
        (BOOKMARKS_XML_PATH, FMT_XML),
        (BOOKMARKS_XML_PATH, None),
    ]
)
def test_load__read_binary(path: Path, fmt: PlistFormat, subject):
    with path.open("rb") as file:
        assert subject == load(file, fmt)


@pytest.mark.parametrize(
    ("path", "fmt"),
    [
        (BOOKMARKS_BINARY_PATH, FMT_BINARY),
        (BOOKMARKS_BINARY_PATH, None),
        (BOOKMARKS_XML_PATH, FMT_XML),
        (BOOKMARKS_XML_PATH, None),
    ]
)
def test_load__read_text(path: Path, fmt: PlistFormat):
    with (
        pytest.raises(AssertionError),
        path.open("r") as file,
    ):
        load(file, fmt)


@pytest.mark.parametrize(
    ("digest", "fmt"),
    [
        ("ac34fa864fc62a2decf219cf3df78fd1da7ec25d", FMT_BINARY),
        ("1b7a31279c90fe6775f8d93fa2e2c202d4e8bca8", FMT_XML),
    ]
)
def test_dump__write_binary(subject, digest: str, fmt: PlistFormat):
    with BytesIO() as buf:
        dump(subject, buf, fmt)
        buf.seek(0)
        assert digest == sha1(buf.read()).hexdigest()


@pytest.mark.parametrize(
    "fmt",
    [
        FMT_BINARY,
        FMT_XML,
    ]
)
def test_dump__write_text(subject, fmt: PlistFormat):
    with (
        pytest.raises(AssertionError),
        TemporaryFile(mode="w") as file,
    ):
        dump(subject, file, fmt)
