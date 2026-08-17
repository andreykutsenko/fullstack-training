from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(autouse=True)
def wide_console(monkeypatch) -> None:
    """Keep rich from wrapping table cells so output assertions stay stable."""
    monkeypatch.setenv("COLUMNS", "240")
