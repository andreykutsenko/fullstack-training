from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

import httpx

from .models import CheckOutcome, Link, LinkKind, LinkResult, Status

DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_CONCURRENT_REQUESTS = 10
# Default httpx User-Agent is rejected with 403 by Cloudflare and GitHub.
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
SKIPPED_SCHEMES = frozenset({"mailto", "tel"})
EXTERNAL_SCHEMES = frozenset({"http", "https"})


def classify(url: str) -> LinkKind:
    stripped = url.strip()
    if not stripped or stripped.startswith("#"):
        return LinkKind.SKIPPED
    scheme = urlsplit(stripped).scheme.lower()
    if not scheme or scheme == "file":
        return LinkKind.LOCAL
    if scheme in EXTERNAL_SCHEMES:
        return LinkKind.EXTERNAL
    return LinkKind.SKIPPED


def resolve_local_target(url: str, source_file: Path) -> Path:
    """Resolve a local link to a filesystem path relative to the file that contains it."""
    parts = urlsplit(url.strip())
    if parts.scheme.lower() == "file":
        return Path(url2pathname(parts.path))
    return (source_file.parent / unquote(parts.path)).resolve()


def check_local(link: Link) -> CheckOutcome:
    parts = urlsplit(link.url.strip())
    if not parts.path:
        return CheckOutcome(Status.SKIPPED, note="anchor only")
    # A link is untrusted input: a NUL byte in the path or a self-referencing
    # symlink makes resolve()/exists() raise instead of returning False.
    try:
        target = resolve_local_target(link.url, link.source_file)
        exists = target.exists()
    except (ValueError, RuntimeError, OSError) as error:
        return CheckOutcome(Status.BROKEN, note=f"invalid path: {type(error).__name__}")
    if exists:
        return CheckOutcome(Status.OK)
    return CheckOutcome(Status.BROKEN, note=f"no such path: {target}")


async def _check_one_url(url: str, client: httpx.AsyncClient) -> CheckOutcome:
    try:
        response = await client.head(url)
        # 405/403 on HEAD is a normal answer from many servers, so retry with GET by code.
        if response.status_code >= 400:
            response = await client.get(url)
    except httpx.TimeoutException:
        return CheckOutcome(Status.BROKEN, note="timeout")
    except httpx.HTTPError as error:
        return CheckOutcome(Status.BROKEN, note=f"{type(error).__name__}: {error}")
    except httpx.InvalidURL as error:
        return CheckOutcome(Status.BROKEN, note=f"invalid URL: {error}")
    except Exception as error:  # noqa: BLE001
        # Fault isolation boundary: one malformed link must not abort the run.
        # A bad port raises OverflowError from the transport, wrapped in an
        # ExceptionGroup, which would otherwise propagate through asyncio.gather.
        return CheckOutcome(Status.BROKEN, note=f"request failed: {type(error).__name__}")

    code = response.status_code
    if code < 400:
        return CheckOutcome(Status.OK, http_code=code)
    return CheckOutcome(Status.BROKEN, http_code=code, note=f"HTTP {code}")


async def check_urls(urls: list[str], timeout: float) -> dict[str, CheckOutcome]:
    """Check every unique URL once, at most MAX_CONCURRENT_REQUESTS at a time."""
    unique_urls = list(dict.fromkeys(urls))
    if not unique_urls:
        return {}

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": BROWSER_USER_AGENT},
    ) as client:

        async def guarded(url: str) -> CheckOutcome:
            async with semaphore:
                return await _check_one_url(url, client)

        outcomes = await asyncio.gather(*(guarded(url) for url in unique_urls))

    return dict(zip(unique_urls, outcomes))


def check_links(links: list[Link], timeout: float = DEFAULT_TIMEOUT_SECONDS) -> list[LinkResult]:
    kinds = {link: classify(link.url) for link in links}
    external_urls = [link.url for link in links if kinds[link] is LinkKind.EXTERNAL]
    external_outcomes = asyncio.run(check_urls(external_urls, timeout))

    results: list[LinkResult] = []
    for link in links:
        kind = kinds[link]
        if kind is LinkKind.LOCAL:
            outcome = check_local(link)
        elif kind is LinkKind.EXTERNAL:
            outcome = external_outcomes[link.url]
        else:
            outcome = CheckOutcome(Status.SKIPPED, note="not checkable")
        results.append(
            LinkResult(
                link=link,
                status=outcome.status,
                http_code=outcome.http_code,
                note=outcome.note,
            )
        )
    return results
