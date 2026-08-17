from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

CLONE_TIMEOUT_SECONDS = 300


class CloneError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepoTarget:
    clone_url: str
    branch: str | None
    subdirectory: str


def is_remote(target: str) -> bool:
    return target.startswith("http")


def parse_repo_url(url: str) -> RepoTarget:
    """Split a GitHub web URL into clone URL, branch and subdirectory to scan."""
    clean = url.rstrip("/")
    if "/tree/" not in clean:
        return RepoTarget(clone_url=clean, branch=None, subdirectory="")
    base, rest = clean.split("/tree/", 1)
    parts = rest.split("/")
    return RepoTarget(clone_url=base, branch=parts[0], subdirectory="/".join(parts[1:]))


def clone(target: RepoTarget, destination: Path) -> Path:
    command = ["git", "clone", "--depth", "1"]
    if target.branch:
        command += ["--branch", target.branch]
    command += [target.clone_url, str(destination)]

    # Without this git blocks forever on a password prompt for a private repository.
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo"}
    try:
        completed = subprocess.run(
            command,
            env=environment,
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise CloneError(
            f"клонирование не уложилось в {CLONE_TIMEOUT_SECONDS} с: {target.clone_url}"
        ) from None
    if completed.returncode != 0:
        raise CloneError(completed.stderr.strip() or f"git clone failed: {target.clone_url}")

    scan_root = destination / target.subdirectory if target.subdirectory else destination
    if not scan_root.exists():
        raise CloneError(f"путь {target.subdirectory!r} отсутствует в репозитории")
    return scan_root
