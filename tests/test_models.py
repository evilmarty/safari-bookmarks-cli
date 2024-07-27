import pytest

from safaribookmarks.models import (
    WebBookmarkTypeList,
    WebBookmarkTypeLeaf,
    WebBookmarkTypeProxy,
    WebBookmarkType,
)


class TestWebBookmarkType:
    def test_hash(self):
        subject = WebBookmarkType()
        assert hash(subject) == hash(subject.web_bookmark_uuid)


class TestWebBookmarkTypeProxy:
    @pytest.fixture()
    def subject(self):
        return WebBookmarkTypeProxy(
            Title="Example",
        )


class TestWebBookmarkTypeList:
    @pytest.fixture()
    def subject(self):
        return WebBookmarkTypeList(
            Title="Example",
            Children=[
                WebBookmarkTypeLeaf(
                    URLString="http://example.com",
                ),
            ],
        )

    def test_append(self, subject: WebBookmarkTypeList):
        new_child = WebBookmarkTypeLeaf(
            URLString="http://example.com",
        )
        subject.append(new_child)
        assert new_child == subject.children[1]

    def test_insert(self, subject: WebBookmarkTypeList):
        new_child = WebBookmarkTypeLeaf(
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
