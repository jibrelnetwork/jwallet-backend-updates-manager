import os
import json
import mimetypes

from git import Repo
import asyncio
from aiohttp import web
import semver

from jwallet_updates import settings
# from aiohttp_swagger import setup_swagger

STATUS_UPDATE_REQUIRED = 'UPDATE_REQUIRED'
STATUS_UP_TO_DATE = 'UP_TO_DATE'


def get_actual_assets():
    repo = Repo(settings.ASSETS_REPO_PATH)
    assets = {}
    for obj in repo.heads.master.commit.tree.traverse():
        assets[obj.path] = obj.hexsha[:6]
    return assets


def make_assets_index():
    repo_state = get_actual_assets()
    ids_map = json.load(open(settings.ASSETS_IDS_FILE, 'rb'))
    index = {}
    for id_, path in ids_map.items():
        if path not in repo_state:
            raise ValueError('Asset path {} does not exist!')
        index[id_] = {'version': repo_state[path], 'path': path}
    return index


def load_versions_info():
    data = json.load(open(settings.ACTUAL_VERSIONS_FILE, 'rb'))
    processed = {}
    for platform, versions_info in data.items():
        processed[platform] = {
            'minimal_actual_version': semver.VersionInfo.parse(versions_info['minimal_actual_version']),
            'force_update': [semver.VersionInfo.parse(v) for v in versions_info['force_update']]
        }
    return processed


routes = web.RouteTableDef()
# routes.static('/v1/assets/', settings.ASSETS_REPO_PATH)


@routes.get('/v1/assets/{asset_id}')
async def get_asset(request):
    asset_id = request.match_info['asset_id']
    assets_index = request.app['assets_index']
    asset_info = assets_index.get(asset_id)
    if asset_info is None:
        return web.Response(status=404)
    asset_abs_path = os.path.join(settings.ASSETS_REPO_PATH, asset_info['path'])
    resp = web.Response(body=open(asset_abs_path, 'rb').read(), headers={'X-ASSET-VERSION': asset_info['version']})
    mime_type = mimetypes.guess_type(asset_abs_path)
    if mime_type:
        resp.content_type = mime_type[0]
    return resp


@routes.get('/v1/{platform}/{version}/status')
async def get_version_status(request):
    """
    Checks moblie app version status: up to date, update available or update required
    """
    version = request.match_info['version']
    try:
        version = semver.VersionInfo.parse(version)
    except ValueError as e:
        return web.Response(body=str(e), status=400)
    platform = request.match_info['platform']
    versions_info = request.app['versions']
    if platform not in versions_info:
        return web.Response(status=404)
    if version < versions_info[platform]['minimal_actual_version']:
        status = {
            'status': STATUS_UPDATE_REQUIRED,
        }
    elif version in versions_info[platform]['force_update']:
        status = {
            'status': STATUS_UPDATE_REQUIRED,
        }
    else:
        status = {
            'status': STATUS_UP_TO_DATE,
        }
    return web.json_response(status)


@routes.post('/v1/check_assets_updates')
async def check_assests_updates(request):
    """
    Checks assets versions and returns assets IDs that needds updates
    """
    app_assets = await request.json()
    assets_index = request.app['assets_index']
    result = []
    for asset in app_assets:
        asset_info = assets_index.get(asset['id'])
        if asset_info is not None:
            if asset_info['version'] != asset['version']:
                result.append(asset['id'])
    return web.json_response(result)


async def make_app():
    """
    Create and initialize the application instance.
    """
    app = web.Application()
    app['versions'] = load_versions_info()
    app['assets_index'] = make_assets_index()
    app.add_routes(routes)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = make_app()
    web.run_app(app)
