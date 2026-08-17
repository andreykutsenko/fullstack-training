from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from .models import LinkResult, Status

STATUS_STYLES = {Status.OK: "green", Status.BROKEN: "red", Status.SKIPPED: "yellow"}


def build_console() -> Console:
    # Colors are meaningless in a pipe or a file, so drop them when stdout is not a tty.
    return Console(no_color=not sys.stdout.isatty())


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def build_table(results: list[LinkResult], root: Path) -> Table:
    table = Table(title="Проверка ссылок", header_style="bold")
    table.add_column("Файл")
    table.add_column("Строка", justify="right")
    table.add_column("Ссылка", overflow="fold")
    table.add_column("Статус")
    table.add_column("HTTP")
    table.add_column("Примечание", overflow="fold")

    for result in results:
        style = STATUS_STYLES[result.status]
        # Paths, URLs and notes are data, not markup: a "[" in a filename
        # would otherwise be parsed as a rich tag and crash rendering.
        table.add_row(
            escape(_display_path(result.link.source_file, root)),
            str(result.link.line),
            escape(result.link.url),
            f"[{style}]{result.status.value}[/{style}]",
            str(result.http_code) if result.http_code is not None else "",
            escape(result.note),
        )
    return table


def count_checked(results: list[LinkResult]) -> int:
    return sum(1 for result in results if result.is_counted)


def count_broken(results: list[LinkResult]) -> int:
    return sum(1 for result in results if result.is_broken)


def build_verdict(results: list[LinkResult]) -> str:
    total = count_checked(results)
    broken = count_broken(results)
    if broken:
        return f"Сломанных ссылок: {broken} из {total}"
    return f"Все ссылки рабочие: {total} из {total}"


def render(results: list[LinkResult], root: Path, console: Console, broken_only: bool) -> None:
    shown = [result for result in results if result.is_broken] if broken_only else results
    if shown:
        console.print(build_table(shown, root))
    elif broken_only:
        console.print("Сломанных ссылок нет.")
    else:
        console.print("Ссылок не найдено.")

    verdict = build_verdict(results)
    console.print(f"[red]{verdict}[/red]" if count_broken(results) else f"[green]{verdict}[/green]")


def write_report(results: list[LinkResult], report_path: Path, root: Path) -> None:
    """Write the broken-link report; the file is created even when nothing is broken."""
    broken = [result for result in results if result.is_broken]
    lines = ["# Отчёт о проверке ссылок", "", build_verdict(results), ""]

    if broken:
        lines += ["| Файл | Строка | Ссылка | HTTP | Примечание |", "| --- | --- | --- | --- | --- |"]
        for result in broken:
            lines.append(
                "| {file} | {line} | {url} | {code} | {note} |".format(
                    file=_display_path(result.link.source_file, root),
                    line=result.link.line,
                    url=result.link.url,
                    code=result.http_code if result.http_code is not None else "",
                    note=result.note.replace("|", "\\|"),
                )
            )
    else:
        lines.append("Сломанных ссылок не найдено.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
