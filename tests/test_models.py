import pytest
from uuid import uuid4

from safaribookmarks.models import (
    WebBookmarkTypeList,
    WebBookmarkTypeLeaf,
    WebBookmarkTypeProxy,
    WebBookmarkType,
)


class TestWebBookmarkType:
    def test_hash(self):
        uuid = str(uuid4())
        subject = WebBookmarkType(
            WebBookmarkUUID=uuid,
        )
        assert hash(subject) == hash(uuid)


class TestWebBookmarkTypeProxy:
    @pytest.fixture()
    def subject(self):
        return WebBookmarkTypeProxy(
            WebBookmarkUUID=str(uuid4()),
            Title="Example",
        )


class TestWebBookmarkTypeList:
    @pytest.fixture()
    def subject(self):
        return WebBookmarkTypeList(
            WebBookmarkUUID=str(uuid4()),
            Title="Example",
            Children=[
                WebBookmarkTypeLeaf(
                    WebBookmarkUUID=str(uuid4()),
                    URLString="http://example.com",
                ),
            ],
        )

    def test_append(self, subject: WebBookmarkTypeList):
        new_child = WebBookmarkTypeLeaf(
            WebBookmarkUUID=str(uuid4()),
            URLString="http://example.com",
        )
        subject.append(new_child)
        assert new_child == subject.children[1]

    def test_insert(self, subject: WebBookmarkTypeList):
        new_child = WebBookmarkTypeLeaf(
            WebBookmarkUUID=str(uuid4()),
            URLString="http://example.com",
        )
        subject.insert(0, new_child)
        assert new_child == subject.children[0]

    def test_remove(self, subject: WebBookmarkTypeList):
        child, *_ = subject.children.copy()
        subject.remove(child)
        assert child not in subject.children

    def test_empty(self, subject: WebBookmarkTypeList):
        assert len(subject.children) != 0
        subject.empty()
        assert len(subject.children) == 0
