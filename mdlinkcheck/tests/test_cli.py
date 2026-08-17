from pathlib import Path

from mdlinkcheck.cli import EXIT_BROKEN, EXIT_ERROR, EXIT_OK, main
from mdlinkcheck.repo import parse_repo_url


def make_docs(root: Path, body: str) -> None:
    (root / "page.md").write_text(body, encoding="utf-8")


def test_exit_zero_when_everything_resolves(tmp_path, capsys):
    (tmp_path / "target.md").write_text("ok", encoding="utf-8")
    make_docs(tmp_path, "[a](./target.md)")

    assert main([str(tmp_path)]) == EXIT_OK
    assert "Все ссылки рабочие: 1 из 1" in capsys.readouterr().out


def test_exit_one_when_something_is_broken(tmp_path, capsys):
    make_docs(tmp_path, "[a](./missing.md)")

    assert main([str(tmp_path)]) == EXIT_BROKEN
    assert "Сломанных ссылок: 1 из 1" in capsys.readouterr().out


def test_skipped_links_are_out_of_the_denominator(tmp_path, capsys):
    (tmp_path / "target.md").write_text("ok", encoding="utf-8")
    make_docs(tmp_path, "[a](./target.md) [b](mailto:x@example.com) [c](#anchor)")

    assert main([str(tmp_path)]) == EXIT_OK
    assert "Все ссылки рабочие: 1 из 1" in capsys.readouterr().out


def test_missing_path_exits_with_error(tmp_path):
    assert main([str(tmp_path / "nowhere")]) == EXIT_ERROR


def test_report_lists_broken_links(tmp_path):
    make_docs(tmp_path, "[a](./missing.md)")
    report = tmp_path / "broken.md"

    assert main([str(tmp_path), "--report", str(report)]) == EXIT_BROKEN
    content = report.read_text(encoding="utf-8")
    assert "./missing.md" in content
    assert "Сломанных ссылок: 1 из 1" in content


def test_report_is_created_even_without_broken_links(tmp_path):
    (tmp_path / "target.md").write_text("ok", encoding="utf-8")
    make_docs(tmp_path, "[a](./target.md)")
    report = tmp_path / "broken.md"

    assert main([str(tmp_path), "--report", str(report)]) == EXIT_OK
    assert "Сломанных ссылок не найдено." in report.read_text(encoding="utf-8")


def test_broken_only_hides_working_links(tmp_path, capsys):
    (tmp_path / "target.md").write_text("ok", encoding="utf-8")
    make_docs(tmp_path, "[good](./target.md) [bad](./missing.md)")

    assert main([str(tmp_path), "--broken-only"]) == EXIT_BROKEN
    output = capsys.readouterr().out
    assert "missing.md" in output
    assert "good" not in output


def test_service_directories_are_skipped(tmp_path, capsys):
    for name in (".git", "node_modules", ".venv", "__pycache__"):
        service_dir = tmp_path / name
        service_dir.mkdir()
        (service_dir / "page.md").write_text("[a](./missing.md)", encoding="utf-8")

    assert main([str(tmp_path)]) == EXIT_OK
    assert "Все ссылки рабочие: 0 из 0" in capsys.readouterr().out


def test_repo_url_with_tree_branch_is_parsed():
    target = parse_repo_url("https://github.com/user/repo/tree/main/docs")

    assert target.clone_url == "https://github.com/user/repo"
    assert target.branch == "main"
    assert target.subdirectory == "docs"


def test_plain_repo_url_is_parsed():
    target = parse_repo_url("https://github.com/user/repo")

    assert target.clone_url == "https://github.com/user/repo"
    assert target.branch is None
    assert target.subdirectory == ""
