from aiohttp import web

async def handle(_: web.Request):
    return web.Response(text="Hello, world!")


async def hello_app():
    app = web.Application()
    app.add_routes([web.route("*", "/{path:.*}", handle)])
    return app


if __name__ == "__main__":
    web.run_app(hello_app(), host="0.0.0.0", port=3000)
