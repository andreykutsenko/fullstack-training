from __future__ import annotations

import os
from pathlib import Path

SKIPPED_DIRECTORIES = frozenset({".git", "node_modules", ".venv", "__pycache__"})
MARKDOWN_SUFFIX = ".md"


def find_markdown_files(root: Path) -> list[Path]:
    """Return every markdown file under root, ignoring service directories."""
    if root.is_file():
        return [root] if root.name.lower().endswith(MARKDOWN_SUFFIX) else []

    def _abort(error: OSError) -> None:
        # Spec requires exit code 2 on a permission error; the default os.walk
        # behaviour is to skip the directory silently, which would report
        # "all links fine" for a tree that was never read.
        raise error

    found: list[Path] = []
    for current_dir, subdirs, filenames in os.walk(root, onerror=_abort):
        subdirs[:] = [name for name in subdirs if name not in SKIPPED_DIRECTORIES]
        for filename in sorted(filenames):
            if filename.lower().endswith(MARKDOWN_SUFFIX):
                found.append(Path(current_dir) / filename)
    return sorted(found)
