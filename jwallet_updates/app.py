import os

from git import Repo
import asyncio
from aiohttp import web
# from aiohttp_swagger import setup_swagger


ASSETS_REPO_PATH = os.path.join(os.path.dirname(__file__, 'assets'))
ASSETS_IDS_FILE = os.path.join(ASSETS_REPO_PATH, 'assets_ids.json')
ACTUAL_VERSION_FILE = os.path.join(os.path.dirname(__file__, 'actual_versions.json'))


def get_actual_assets():
    repo = Repo(ASSETS_REPO_PATH)
    assets = {}
    for obj in repo.heads.master.commit.tree.traverse():
        assets[obj.path] = obj.hexsha[:6]
    return assets


routes = web.RouteTableDef()
routes.static('/v1/assets/', ASSETS_REPO_PATH)


@routes.get('/v1/{platform}/{version}/status')
async def get_version_status(request):
    """
    Checks moblie app version status: up to date, update available or update required
    """
    version = request.match_info['version']
    platform = request.match_info['platform']
    actual_versions = request.app['versions']
    if version not in actual_versions[platform]:  
        status = {
            'status': STATUS_UPDATE_REQUIRED,
        }
    else:
        status = {
            'status': STATUS_UP_TO_DATE,
        }
    return web.json_response(status)


@routes.post('/v1/check_updates')
async def check_assests_updates(request):
    """
    Checks assets versions and returns assets IDs that needds updates
    """
    app_assets = await request.json()
    actual_assets = get_actual_assets()
    result = []
    for asset in app_assets:
        actual_version = actual_assets.get(asset['id'])
        if actual_version is not None and actual_version != asset['version']:
            result.append(asset['id'])
    return web.json_response(result)


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
