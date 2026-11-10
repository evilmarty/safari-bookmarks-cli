"""Moving a folder into itself (or its own descendant) must not create a cycle."""

import pytest

from safaribookmarks.models import WebBookmarkTypeList
from safaribookmarks.safaribookmarks import SafariBookmarks


@pytest.fixture
def tree():
    root = SafariBookmarks(
        WebBookmarkTypeList(
            **{"Title": "root", "Children": []},
        )
    )
    folder_a = root.add_folder("A")
    folder_b = folder_a.add_folder("B")
    return root, folder_a, folder_b


def test_append_folder_into_itself_is_rejected(tree):
    _, folder_a, _ = tree
    with pytest.raises(RuntimeError):
        folder_a.append(folder_a)
    # tree left untouched
    assert [c.title for c in folder_a.children] == ["B"]


def test_append_folder_into_descendant_is_rejected(tree):
    root, folder_a, folder_b = tree
    with pytest.raises(RuntimeError):
        folder_b.append(folder_a)
    # nothing detached, nothing duplicated
    assert [c.title for c in root.children] == ["A"]
    assert [c.title for c in folder_a.children] == ["B"]
    assert folder_b.children == []


def test_valid_move_still_works(tree):
    root, folder_a, folder_b = tree
    folder_c = root.add_folder("C")
    folder_c.append(folder_b)
    assert [c.title for c in folder_a.children] == []
    assert [c.title for c in folder_c.children] == ["B"]
