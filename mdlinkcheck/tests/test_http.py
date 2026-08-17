from pathlib import Path

import httpx
import pytest
import respx

from mdlinkcheck.checker import BROWSER_USER_AGENT, check_links
from mdlinkcheck.models import Link, Status

URL = "https://example.com/page"


def link(url: str = URL) -> Link:
    return Link(source_file=Path("doc.md"), line=1, url=url)


@respx.mock
def test_head_405_falls_back_to_get():
    respx.head(URL).mock(return_value=httpx.Response(405))
    respx.get(URL).mock(return_value=httpx.Response(200))

    (result,) = check_links([link()])

    assert result.status is Status.OK
    assert result.http_code == 200
    assert len(respx.calls) == 2


@respx.mock
def test_head_404_is_broken_without_retry():
    respx.head(URL).mock(return_value=httpx.Response(404))
    respx.get(URL).mock(return_value=httpx.Response(404))

    (result,) = check_links([link()])

    assert result.status is Status.BROKEN
    assert result.http_code == 404


@respx.mock
def test_timeout_is_broken():
    respx.head(URL).mock(side_effect=httpx.ConnectTimeout("too slow"))

    (result,) = check_links([link()], timeout=0.1)

    assert result.status is Status.BROKEN
    assert result.note == "timeout"


@respx.mock
def test_network_error_is_broken():
    respx.head(URL).mock(side_effect=httpx.ConnectError("no route"))

    (result,) = check_links([link()])

    assert result.status is Status.BROKEN


@respx.mock
def test_same_url_is_requested_once():
    route = respx.head(URL).mock(return_value=httpx.Response(200))

    results = check_links([link(), link(), link()])

    assert route.call_count == 1
    assert [result.status for result in results] == [Status.OK] * 3


@respx.mock
def test_browser_user_agent_is_sent():
    route = respx.head(URL).mock(return_value=httpx.Response(200))

    check_links([link()])

    assert route.calls.last.request.headers["User-Agent"] == BROWSER_USER_AGENT


@respx.mock
def test_skipped_schemes_do_not_hit_the_network():
    results = check_links([link("mailto:a@example.com"), link("#anchor"), link("tel:+7000")])

    assert [result.status for result in results] == [Status.SKIPPED] * 3
    assert len(respx.calls) == 0


@pytest.mark.parametrize("code", [200, 204, 301, 399])
@respx.mock
def test_2xx_and_3xx_are_ok(code):
    respx.head(URL).mock(return_value=httpx.Response(code))

    (result,) = check_links([link()])

    assert result.status is Status.OK
