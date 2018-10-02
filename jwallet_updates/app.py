import os

import asyncio
from aiohttp import web


SOMEVAR = os.getenv('JWALLET_UPDATES___')

STATUS_UP_TO_DATE = 'UP_TO_DATE'
STATUS_UPDATE_AVAILABLE = 'UPDATE_AVAILABLE'
STATUS_UPDATE_REQUIRED = 'UPDATE_REQUIRED'


def get_actual_assets():
    repo = Repo(ASSETS_REPO_PATH)
    assets = {}
    for obj in repo.heads.master.commit.tree.traverse():
        assets[obj.path] = obj.hexsha[:6]
    return assets


routes = web.RouteTableDef()


@routes.get('/v1/{platform}/{locale}/{version}/status')
async def get_version_status(request):
    """
    Checks moblie app version status: up to date, update available or update required
    """
    status = {
        'status': '',
        'updateDescription': '',
    }
    return web.json_response(status)


def make_app():
    """
    Create and initialize the application instance.
    """
    app = web.Application()
    app.add_routes(routes)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = make_app()
    web.run_app(app)
