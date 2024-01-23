import pytest
from redirect.server import server_app as server_app_orig, redirect_service


@pytest.fixture
def server_app(event_loop):
    return event_loop.run_until_complete(server_app_orig())


@pytest.fixture
def settings(server_app):
    return server_app[redirect_service].settings


@pytest.fixture
def client(aiohttp_client, server_app, event_loop):
    return event_loop.run_until_complete(aiohttp_client(server_app))
