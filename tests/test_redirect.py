from collections import Counter
from http import HTTPStatus
import operator
import random
from urllib import parse

import pytest


TEST_POOL_A_HOSTS = [("host-1", 2), ("host-2", 1)]
TEST_POOL_B_HOSTS = [("host-3", 1), ("host-4", 1)]


@pytest.fixture
def random_path_with_qs(faker):
    def factory():
        return f"/{faker.uri_path(random.randint(3, 5))}?{parse.urlencode({k: random.randint(100, 1000) for k in [faker.uri_page() for _ in range(5)]})}"

    return factory


def test_settings(settings):
    """
    Check overriden test configuration from tests/redirect_pools_config_tests.toml is used
    """

    assert len(settings.redirect_pools) == 2
    test_pool_a, test_pool_b = settings.redirect_pools

    assert test_pool_a.is_default
    assert test_pool_a.status == HTTPStatus.FOUND
    assert (
        sorted(
            map(operator.attrgetter("host", "weight"), test_pool_a.weighted_hosts),
            key=operator.itemgetter(1, 0),
            reverse=True,
        )
        == TEST_POOL_A_HOSTS
    )

    assert not test_pool_b.is_default
    assert test_pool_b.status == HTTPStatus.FOUND
    assert (
        sorted(
            map(operator.attrgetter("host", "weight"), test_pool_b.weighted_hosts),
            key=operator.itemgetter(1),
            reverse=True,
        )
        == TEST_POOL_B_HOSTS
    )


@pytest.mark.asyncio
async def test_redirect_missing_pool_id(client, random_path_with_qs):
    path_with_qs = random_path_with_qs()

    resp = await client.get(path_with_qs, allow_redirects=False)
    assert resp.status == HTTPStatus.FOUND
    assert "Location" in resp.headers
    parsed_url = parse.urlparse(resp.headers["Location"])

    # Ensure that pool a is used by default
    assert parsed_url.netloc in map(operator.itemgetter(0), TEST_POOL_A_HOSTS)
    assert [parsed_url.path, parsed_url.query] == path_with_qs.split("?")


@pytest.mark.asyncio
async def test_redirect_unknown_pool_id(client, random_path_with_qs, settings):
    path_with_qs = random_path_with_qs()

    resp = await client.get(
        path_with_qs,
        headers={settings.redirect_pool_id_header: "unknown-pool-id"},
        allow_redirects=False,
    )
    assert resp.status == HTTPStatus.FOUND
    assert "Location" in resp.headers
    parsed_url = parse.urlparse(resp.headers["Location"])

    # Ensure that default (pool a) is used if unknown pool id is provided
    assert parsed_url.netloc in map(operator.itemgetter(0), TEST_POOL_A_HOSTS)
    assert [parsed_url.path, parsed_url.query] == path_with_qs.split("?")


@pytest.mark.asyncio
async def test_redirect_redirect_loop(client, random_path_with_qs):
    path_with_qs = random_path_with_qs()

    resp = await client.get(
        path_with_qs,
        headers={"Host": "host-1", "X-Redirect-Pool-ID": "test-pool-a"},
        allow_redirects=False,
    )
    assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_redirect_internal_server_error(client, random_path_with_qs, mocker):
    # Lets break external dependency (roundrobin library)
    mocker.patch(
        "redirect.strategy.WeightedRoundRobinRedirectStrategy._weighted_round_robin",
        mocker.Mock(side_effect=SystemError("Oops")),
    )

    path_with_qs = random_path_with_qs()

    resp = await client.get(
        path_with_qs,
        headers={"X-Redirect-Pool-ID": "test-pool-a"},
        allow_redirects=False,
    )
    assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_redirect_pool_a(client, random_path_with_qs, settings):
    path_with_qs = random_path_with_qs()

    resp = await client.get(
        path_with_qs,
        headers={settings.redirect_pool_id_header: "test-pool-a"},
        allow_redirects=False,
    )
    assert resp.status == HTTPStatus.FOUND
    assert "Location" in resp.headers
    parsed_url = parse.urlparse(resp.headers["Location"])

    # Ensure that pool a is used by default
    assert parsed_url.netloc in map(operator.itemgetter(0), TEST_POOL_A_HOSTS)
    assert [parsed_url.path, parsed_url.query] == path_with_qs.split("?")


@pytest.mark.asyncio
async def test_redirect_pool_b(client, random_path_with_qs, settings):
    path_with_qs = random_path_with_qs()

    resp = await client.get(
        path_with_qs,
        headers={settings.redirect_pool_id_header: "test-pool-b"},
        allow_redirects=False,
    )
    assert resp.status == HTTPStatus.FOUND
    assert "Location" in resp.headers
    parsed_url = parse.urlparse(resp.headers["Location"])

    # Ensure that pool a is used by default
    assert parsed_url.netloc in map(operator.itemgetter(0), TEST_POOL_B_HOSTS)
    assert [parsed_url.path, parsed_url.query] == path_with_qs.split("?")


@pytest.mark.asyncio
async def test_redirect_different_http_methods(client, random_path_with_qs, settings):
    for method in ["GET", "POST", "PUT", "HEAD", "DELETE", "OPTIONS"]:
        path_with_qs = random_path_with_qs()
        resp = await client.request(
            method,
            path_with_qs,
            headers={settings.redirect_pool_id_header: "test-pool-a"},
            allow_redirects=False,
        )
        assert resp.status == HTTPStatus.FOUND
        assert "Location" in resp.headers
        parsed_url = parse.urlparse(resp.headers["Location"])

        assert parsed_url.netloc in map(operator.itemgetter(0), TEST_POOL_A_HOSTS)
        assert [parsed_url.path, parsed_url.query] == path_with_qs.split("?")


@pytest.mark.asyncio
async def test_weighted_round_robin_redirect_pool_a(
    client, random_path_with_qs, settings
):
    """
    We test that redirects are balanced properly for test pool a
    """
    path_with_qs = random_path_with_qs()
    counter = Counter()
    for _ in range(120):
        resp = await client.get(
            path_with_qs,
            headers={settings.redirect_pool_id_header: "test-pool-a"},
            allow_redirects=False,
        )
        assert resp.status == HTTPStatus.FOUND
        assert "Location" in resp.headers
        parsed_url = parse.urlparse(resp.headers["Location"])
        counter.update([parsed_url.netloc])

    # host-1 has weight 2 and host-1 has weight 1, we expect host-1 to be used twise as frequently
    assert counter["host-1"] == 80
    assert counter["host-2"] == 40


@pytest.mark.asyncio
async def test_weighted_round_robin_redirect_pool_b(
    client, random_path_with_qs, settings
):
    """
    We test that redirects are balanced properly for test pool a
    """
    path_with_qs = random_path_with_qs()
    counter = Counter()
    for _ in range(120):
        resp = await client.get(
            path_with_qs,
            headers={settings.redirect_pool_id_header: "test-pool-b"},
            allow_redirects=False,
        )
        assert resp.status == HTTPStatus.FOUND
        assert "Location" in resp.headers
        parsed_url = parse.urlparse(resp.headers["Location"])
        counter.update([parsed_url.netloc])

    # Since both hosts in pool be have weight 2 - we expect each to be used equally
    assert counter["host-3"] == 60
    assert counter["host-4"] == 60
