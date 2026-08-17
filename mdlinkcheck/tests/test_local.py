import os

from mdlinkcheck.checker import check_local, classify
from mdlinkcheck.models import Link, LinkKind, Status


def test_sibling_link_resolves_from_the_source_file_not_cwd(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    (tmp_path / "sibling.md").write_text("ok", encoding="utf-8")
    source = tmp_path / "docs" / "page.md"
    source.write_text("[a](../sibling.md)", encoding="utf-8")

    monkeypatch.chdir(os.path.expanduser("~"))
    outcome = check_local(Link(source_file=source, line=1, url="../sibling.md"))

    assert outcome.status is Status.OK


def test_missing_file_is_broken(tmp_path):
    source = tmp_path / "page.md"
    source.write_text("[a](./missing.md)", encoding="utf-8")

    outcome = check_local(Link(source_file=source, line=1, url="./missing.md"))

    assert outcome.status is Status.BROKEN


def test_anchor_and_query_are_stripped(tmp_path):
    (tmp_path / "target file.md").write_text("ok", encoding="utf-8")
    source = tmp_path / "page.md"

    outcome = check_local(Link(source_file=source, line=1, url="./target%20file.md?v=1#head"))

    assert outcome.status is Status.OK


def test_file_scheme_is_an_absolute_os_path(tmp_path):
    target = tmp_path / "abs.md"
    target.write_text("ok", encoding="utf-8")
    source = tmp_path / "docs" / "page.md"

    outcome = check_local(Link(source_file=source, line=1, url=f"file://{target}"))

    assert outcome.status is Status.OK


def test_classification_of_schemes():
    assert classify("mailto:user@example.com") is LinkKind.SKIPPED
    assert classify("tel:+7000") is LinkKind.SKIPPED
    assert classify("#anchor") is LinkKind.SKIPPED
    assert classify("https://example.com") is LinkKind.EXTERNAL
    assert classify("./a.md") is LinkKind.LOCAL
    assert classify("file:///tmp/a.md") is LinkKind.LOCAL
