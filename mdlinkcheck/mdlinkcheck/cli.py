from __future__ import annotations

import argparse
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .checker import DEFAULT_TIMEOUT_SECONDS, check_links
from .extractor import extract_links_from_file
from .models import Link
from .report import build_console, count_broken, render, write_report
from .repo import CloneError, clone, is_remote, parse_repo_url
from .scanner import find_markdown_files

EXIT_OK = 0
EXIT_BROKEN = 1
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdlinkcheck",
        description="Проверка ссылок в markdown-файлах папки или GitHub-репозитория.",
    )
    parser.add_argument("target", help="путь к папке или URL GitHub-репозитория")
    parser.add_argument("--broken-only", action="store_true", help="показывать только сломанные")
    parser.add_argument("--report", metavar="FILE", help="markdown-отчёт о сломанных ссылках")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="N",
        help=f"таймаут HTTP-запроса в секундах (по умолчанию {DEFAULT_TIMEOUT_SECONDS:g})",
    )
    return parser


@contextmanager
def resolve_root(target: str) -> Iterator[Path]:
    """Yield the directory to scan, cloning and cleaning up a remote repository if needed."""
    if not is_remote(target):
        yield Path(target)
        return

    temporary_dir = Path(tempfile.mkdtemp(prefix="mdlinkcheck-"))
    try:
        yield clone(parse_repo_url(target), temporary_dir / "repo")
    finally:
        shutil.rmtree(temporary_dir, ignore_errors=True)


def collect_links(root: Path) -> list[Link]:
    links: list[Link] = []
    for markdown_file in find_markdown_files(root):
        links.extend(extract_links_from_file(markdown_file))
    return links


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = build_console()

    try:
        with resolve_root(args.target) as root:
            if not root.exists():
                console.print(f"[red]Путь не найден: {root}[/red]")
                return EXIT_ERROR

            results = check_links(collect_links(root), timeout=args.timeout)
            render(results, root, console, broken_only=args.broken_only)
            if args.report:
                write_report(results, Path(args.report), root)
    except CloneError as error:
        console.print(f"[red]Не удалось клонировать репозиторий: {error}[/red]")
        return EXIT_ERROR
    except OSError as error:
        console.print(f"[red]Ошибка доступа: {error}[/red]")
        return EXIT_ERROR

    return EXIT_BROKEN if count_broken(results) else EXIT_OK
