from aiohttp import web

from redirect.dtos import RequestDataDTO
from redirect.service import RedirectService, RedirectLoopException
from redirect.strategy import WeightedRoundRobinRedirectStrategy


redirect_service = web.AppKey("redirect_service", RedirectService)


async def handle(request: web.Request):
    """
    Handles all incoming requests (regardless method) and redirects them to
    selected host of the specific redirect pool, preserving scheme, path
    and query string params of original request.

    Host is selected using weighted round robin (default strategy) load balancing algorithm.
    """
    request_data_dto = RequestDataDTO(
        request.headers, request.scheme, request.host, request.raw_path
    )
    try:
        redirect_to_location, redirect_to_status = request.app[
            redirect_service
        ].get_redirect_to(request_data_dto)
    except RedirectLoopException:
        raise web.HTTPUnprocessableEntity
    except Exception:
        raise web.HTTPInternalServerError

    return web.Response(
        status=redirect_to_status, headers={"Location": redirect_to_location}
    )


async def server_app():
    app = web.Application()
    # "Inject" concrete implementation of redirect service
    app[redirect_service] = RedirectService(
        redirect_strategy_impl=WeightedRoundRobinRedirectStrategy
    )
    app.add_routes([web.route("*", "/{path:.*}", handle)])
    return app


if __name__ == "__main__":
    web.run_app(server_app())
