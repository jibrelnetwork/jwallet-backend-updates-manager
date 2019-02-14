import os
import hashlib
import json
import mimetypes

import asyncio
from aiohttp import web
import semver

from jwallet_updates import settings
# from aiohttp_swagger import setup_swagger
from jwallet_updates.healthcheck import healthcheck

STATUS_UPDATE_REQUIRED = 'UPDATE_REQUIRED'
STATUS_UP_TO_DATE = 'UP_TO_DATE'


def json_response(view):
    async def _wrapper(request):
        status, data = await view(request)
        return web.json_response(
            status=status,
            data=data
        )

    return _wrapper


def get_actual_assets():
    assets = {}

    for root, dirs, files in os.walk(settings.ASSETS_REPO_PATH, topdown=False):
        rel_dir = os.path.relpath(root, settings.ASSETS_REPO_PATH)

        for file in files:
            digest_file = hashlib.sha1()

            rel_path = os.path.join(rel_dir, file).replace('./', '')
            full_path = os.path.join(root, file)

            if os.path.isfile(full_path):
                with open(full_path, 'rb') as f_obj:
                    digest_file.update(b'blob ' + str(os.path.getsize(full_path)).encode() + b'\0')
                    while True:
                        buf = f_obj.read(64 * 1024)
                        if not buf:
                            break
                        digest_file.update(buf)

            assets[rel_path] = digest_file.hexdigest()[:6]

    return assets


def make_assets_index():
    repo_state = get_actual_assets()
    ids_map = json.load(open(settings.ASSETS_IDS_FILE, 'rb'))
    index = {}
    for id_, path in ids_map.items():
        if path['assets'] not in repo_state:
            raise ValueError('Asset path {} does not exist!')
        index[id_] = {'version': repo_state[path['assets']], 'path': path['assets']}
    return index


def load_versions_info():
    data = json.load(open(settings.ACTUAL_VERSIONS_FILE, 'rb'))
    processed = {}
    for platform, versions_info in data.items():
        processed[platform] = {
            'minimal_actual_version': semver.VersionInfo.parse(versions_info['minimal_actual_version']),
            'force_update': [semver.VersionInfo.parse(v) for v in versions_info['force_update']],
            'latest_version': semver.VersionInfo.parse(versions_info['latest_version']) \
                if versions_info.get('latest_version') else None,
            'force_off': [semver.VersionInfo.parse(v) for v in versions_info['force_off']] \
                if versions_info.get('force_off') else []
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
async def get_version_status_v1(request):
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


@routes.get('/v2/{platform}/{version}/status')
@json_response
async def get_version_status_v2(request):
    """
    Checks moblie app version status: up to date, update available or update required
    """
    version = request.match_info['version']

    try:
        version = semver.VersionInfo.parse(version)
    except ValueError as e:
        return 400, {
            'success': False,
            'errors': [
                {
                    'code': 'ValidationError',
                    'message': 'Bad semver value'
                }
            ]
        }

    platform = request.match_info['platform']

    if platform == 'android':
        return 400, {
            'success': False,
            'errors': [
                {
                    'code': 'ValidationError',
                    'message': 'This platform is not supported'
                }
            ]
        }

    versions_info = request.app['versions']
    if platform not in versions_info:
        return web.Response(status=404)
    if version < versions_info[platform]['minimal_actual_version'] and \
            version < versions_info[platform]['latest_version']:
        status = {
            'status': STATUS_UPDATE_REQUIRED,
            'update_available': True
        }
    elif version < versions_info[platform]['minimal_actual_version'] and \
            version >= versions_info[platform]['latest_version']:
        status = {
            'status': STATUS_UPDATE_REQUIRED,
            'update_available': False
        }
    elif version > versions_info[platform]['latest_version']:
        status = {
            'status': STATUS_UP_TO_DATE,
            'update_available': False
        }
    elif version in versions_info[platform]['force_update']:
        status = {
            'status': STATUS_UPDATE_REQUIRED,
            'update_available': True
        }
    elif version in versions_info[platform]['force_off']:
        status = {
            'status': STATUS_UPDATE_REQUIRED,
            'update_available': False
        }
    elif version < versions_info[platform]['latest_version']:
        status = {
            'status': STATUS_UP_TO_DATE,
            'update_available': True
        }
    else:
        status = {
            'status': STATUS_UP_TO_DATE,
            'update_available': False
        }
    return 200, status


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
    app.router.add_get('/healthcheck', healthcheck)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = make_app()
    web.run_app(app)
