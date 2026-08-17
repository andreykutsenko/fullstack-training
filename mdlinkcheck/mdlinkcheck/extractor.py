from __future__ import annotations

from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from .models import Link


def _build_parser() -> MarkdownIt:
    md = MarkdownIt("commonmark")
    # Default validateLink drops file:// links silently, so every URL is accepted here.
    md.validateLink = lambda url: True
    return md


_PARSER = _build_parser()


def _collect(tokens: list[Token], source_file: Path, line: int, links: list[Link]) -> None:
    for token in tokens:
        if token.map is not None:
            line = token.map[0] + 1
        if token.type == "link_open":
            href = token.attrGet("href")
            if href:
                links.append(Link(source_file=source_file, line=line, url=href))
        elif token.type == "image":
            src = token.attrGet("src")
            if src:
                links.append(Link(source_file=source_file, line=line, url=src))
        if token.children:
            _collect(token.children, source_file, line, links)


def extract_links_from_text(text: str, source_file: Path) -> list[Link]:
    links: list[Link] = []
    _collect(_PARSER.parse(text), source_file, 1, links)
    return links


def extract_links_from_file(path: Path) -> list[Link]:
    return extract_links_from_text(path.read_text(encoding="utf-8", errors="replace"), path)
