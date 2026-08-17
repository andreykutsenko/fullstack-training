"""Регрессии на дефекты, найденные ревью после первой генерации.

Каждый тест воспроизводит краевой случай, на котором утилита раньше падала
трейсбеком или молча возвращала неверный вердикт.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from mdlinkcheck import repo
from mdlinkcheck.checker import check_local, check_links
from mdlinkcheck.models import Link, Status
from mdlinkcheck.report import build_table
from mdlinkcheck.scanner import find_markdown_files


def _link(url: str, source: Path) -> Link:
    return Link(url=url, source_file=source, line=1)


def test_malformed_url_does_not_abort_the_run(tmp_path):
    """Баг 1: httpx.InvalidURL ронял весь прогон через asyncio.gather."""
    page = tmp_path / "page.md"
    page.write_text("x", encoding="utf-8")
    results = check_links([_link("https://example.com:abc/", page)], timeout=1)
    assert results[0].status is Status.BROKEN


def test_nul_byte_in_path_is_broken_not_crash(tmp_path):
    """Баг 2а: Path.resolve() кидал ValueError на нулевом байте."""
    page = tmp_path / "page.md"
    page.write_text("x", encoding="utf-8")
    assert check_local(_link("./x%00y.md", page)).status is Status.BROKEN


def test_symlink_loop_is_broken_not_crash(tmp_path):
    """Баг 2б: самозацикленный симлинк давал RuntimeError."""
    (tmp_path / "loop").symlink_to("loop")
    page = tmp_path / "page.md"
    page.write_text("x", encoding="utf-8")
    assert check_local(_link("./loop", page)).status is Status.BROKEN


@pytest.mark.skipif(os.geteuid() == 0, reason="root игнорирует права доступа")
def test_unreadable_directory_raises_instead_of_reporting_success(tmp_path):
    """Баг 3: os.walk молча пропускал каталог → ложное «все ссылки рабочие»."""
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "a.md").write_text("[a](./nope.md)", encoding="utf-8")
    locked.chmod(0o000)
    try:
        with pytest.raises(OSError):
            find_markdown_files(locked)
    finally:
        locked.chmod(0o755)


def test_clone_timeout_becomes_clone_error(tmp_path, monkeypatch):
    """Баг 4: subprocess.TimeoutExpired всплывал мимо обработчика в cli."""
    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git clone", timeout=1)

    monkeypatch.setattr(repo.subprocess, "run", _timeout)
    target = repo.parse_repo_url("https://github.com/octocat/Hello-World")
    with pytest.raises(repo.CloneError):
        repo.clone(target, tmp_path / "dest")


def test_brackets_in_filename_do_not_break_the_table(tmp_path):
    """Баг 5: скобки в пути парсились rich как разметка и роняли вывод."""
    weird = tmp_path / "x[b].md"
    weird.write_text("x", encoding="utf-8")
    results = check_links([_link("./missing.md", weird)], timeout=1)
    table = build_table(results, tmp_path)  # раньше здесь падал MarkupError
    assert table.row_count == 1
