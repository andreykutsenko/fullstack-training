from pathlib import Path

from mdlinkcheck.extractor import extract_links_from_file, extract_links_from_text


def urls_of(text: str) -> list[str]:
    return [link.url for link in extract_links_from_text(text, Path("doc.md"))]


def test_all_link_forms_are_found():
    text = (
        "[a](./file.md)\n\n"
        "[a][ref]\n\n"
        "<https://x.com>\n\n"
        "![img](./p.png)\n\n"
        "[ref]: https://ref.example\n"
    )
    assert urls_of(text) == ["./file.md", "https://ref.example", "https://x.com", "./p.png"]


def test_link_inside_fenced_code_block_is_ignored():
    text = "```\n[a](./inside.md)\n```\n\n[b](./outside.md)\n"
    assert urls_of(text) == ["./outside.md"]


def test_file_scheme_link_is_found():
    assert urls_of("[a](file:///tmp/x.md)") == ["file:///tmp/x.md"]


def test_line_numbers_point_at_the_source_block():
    text = "# Title\n\nintro\n\n[a](./file.md)\n"
    (link,) = extract_links_from_text(text, Path("doc.md"))
    assert link.line == 5


def test_fixture_file_links_are_extracted(fixtures_dir):
    urls = [link.url for link in extract_links_from_file(fixtures_dir / "index.md")]
    assert "./exists.md" in urls
    assert "./inside-code-block.md" not in urls
    assert "file:///tmp/mdlinkcheck-absent.md" in urls
