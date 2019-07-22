import os
import shutil
from unittest import mock
import json

import git
import pytest

from jwallet_updates.app import make_app


repo_path = os.path.abspath('/tmp/jwallet_assets_test_repo/assets')
os.environ['JWALLET_ASSETS_REPO_PATH'] = repo_path


@pytest.fixture
def assets_repo():
    versions = {
        "ios": {
            "minimal_actual_version": "0.1.0",
            "force_update": ["0.1.5"],
            "latest_version": "0.2.1",
            "force_off": ["0.1.4"]
        },
        "android": {
            "minimal_actual_version": "1.0.0",
            "force_update": []
        }
    }

    assets_index = {
        "mainnet": {
            "assets": "mainnet/assets.json",
            "node": "https://main-node.jwallet.network/"
        },
        "ropsten": {
            "assets": "ropsten/assets.json",
            "node": "https://ropsten-node.jwallet.network/"
        },
        "F1": {
            "assets": "file1.txt"
        },
        "F2": {
            "assets": "file2.txt"
        },
        "F3": {
            "assets": "dir_one/file3.txt"
        },
        "F4": {
            "assets": "dir_one/file4.txt"
        }
    }

    assets = [
        {
            "name": "Jibrel Network Token",
            "symbol": "JNT",
            "blockchainParams": {
                "type": "erc-20",
                "features": [
                    "mintable"
                ],
                "address": "0xa5fd1a791c4dfcaacc963d4f73c6ae5824149ea7",
                "decimals": 18,
                "staticGasAmount": 85000,
                "deploymentBlockNumber": 4736154
            },
            "display": {
                "isDefaultForcedDisplay": True,
                "digitalAssetsListPriority": 980
            },
            "priceFeed": {
                "currencyID": 2498,
                "currencyIDType": "coinmarketcap"
            },
            "assetPage": {
                "description": "Jibrel provides currencies, equities, commodities and other financial assets as standard ERC-20 tokens on the Ethereum blockchain",
                "urls": [
                    {
                        "type": "site",
                        "url": "https://jibrel.network/"
                    },
                    {
                        "type": "binance",
                        "url": "https://info.binance.com/en/currencies/jibrel-network-token"
                    },
                    {
                        "type": "coinmarketcap",
                        "url": "https://coinmarketcap.com/currencies/jibrel-network"
                    }
                ]
            }
        }
    ]

    with open('/tmp/jwallet_updates_test_versions.json', 'w') as f:
        json.dump(versions, f)

    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    repo = git.Repo.init(repo_path)

    with open(os.path.join(repo_path, 'file1.txt'), 'w') as f:
        f.write('1\n2\n')
    repo.git.add('file1.txt')
    with open(os.path.join(repo_path, 'file2.txt'), 'w') as f:
        f.write('3\n4\n')
    repo.git.add('file2.txt')
    os.mkdir(os.path.join(repo_path, 'dir_one'))
    with open(os.path.join(repo_path, 'dir_one', 'file3.txt'), 'w') as f:
        f.write('5\n6\n')
    repo.git.add('dir_one/file3.txt')
    with open(os.path.join(repo_path, 'dir_one', 'file4.txt'), 'w') as f:
        f.write('7\n8\n')
    repo.git.add('dir_one/file4.txt')

    os.mkdir(os.path.join(repo_path, 'mainnet'))
    with open(os.path.join(repo_path, 'mainnet', 'assets.json'), 'w') as f:
        json.dump(assets, f)
    repo.git.add('mainnet/assets.json')

    os.mkdir(os.path.join(repo_path, 'ropsten'))
    with open(os.path.join(repo_path, 'ropsten', 'assets.json'), 'w') as f:
        json.dump(assets, f)
    repo.git.add('ropsten/assets.json')

    with open(os.path.join(repo_path, 'assets_index.json'), 'w') as f:
        json.dump(assets_index, f)
    repo.git.add('assets_index.json')

    repo.index.commit('start')
    yield repo
    shutil.rmtree(os.path.abspath(repo_path))


async def _mkapp(aiohttp_client):
    cli = await aiohttp_client(await make_app())
    return cli


@pytest.fixture()
def cli(aiohttp_client, loop, assets_repo):
    with mock.patch('jwallet_updates.app.settings') as m:
        m.ASSETS_REPO_PATH = repo_path
        m.ACTUAL_VERSIONS_FILE = '/tmp/jwallet_updates_test_versions.json'
        m.ASSETS_IDS_FILE = os.path.abspath(repo_path) + '/assets_index.json'
        yield loop.run_until_complete(_mkapp(aiohttp_client))


async def test_get_updates_blank(cli, assets_repo):
    res = await cli.post('/v1/check_assets_updates', json=[{'id': 'no_such_file.txt', 'version': 'abc'}])
    assert res.status == 200
    assert await res.json() == []


async def test_get_updates(cli, assets_repo):
    repo_items = list(assets_repo.head.commit.tree.traverse())
    res = await cli.post('/v1/check_assets_updates',
                         json=[
                            {'id': 'F4', 'version': repo_items[7].hexsha[:6]},
                            {'id': 'F3', 'version': 'bca'},
                            {'id': 'F1', 'version': 'abc'},
                          ]
                        )
    assert res.status == 200
    assert await res.json() == ['F3', 'F1']


async def test_get_updates_change_files(cli, assets_repo, loop, aiohttp_client):
    repo_items = list(assets_repo.head.commit.tree.traverse())

    current_versions = [
                            {'id': 'F4', 'version': repo_items[7].hexsha[:6]},
                            {'id': 'F3', 'version': repo_items[6].hexsha[:6]},
                            {'id': 'F1', 'version': repo_items[2].hexsha[:6]},
                          ]
    res = await cli.post('/v1/check_assets_updates', json=current_versions)
    assert res.status == 200
    assert await res.json() == []

    fname = os.path.join(assets_repo.working_tree_dir, 'file1.txt')
    with open(fname, 'a') as f:
        f.write('z')

    res = await cli.post('/v1/check_assets_updates', json=current_versions)
    assert res.status == 200
    assert await res.json() == []

    assets_repo.git.add('file1.txt')
    assets_repo.index.commit('chage file1.txt')

    cli = await aiohttp_client(await make_app())

    res = await cli.post('/v1/check_assets_updates', json=current_versions)
    assert res.status == 200
    assert await res.json() == ['F1']


async def test_get_version_status_not_ok(cli, assets_repo):
    res = await cli.get('/v2/ios/0.0.1/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UPDATE_REQUIRED', 'update_available': True}

    res = await cli.get('/v2/ios/0.1.4/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UPDATE_REQUIRED', 'update_available': False}

    res = await cli.get('/v2/ios/0.1.5/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UPDATE_REQUIRED', 'update_available': True}


async def test_get_version_status_ok(cli, assets_repo):
    res = await cli.get('/v1/android/2.0.3.892-04ac940/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UP_TO_DATE'}

    res = await cli.get('/v1/android/1.0.5.8/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UP_TO_DATE'}

    res = await cli.get('/v1/android/1.0.5.5.483-64a9ae4/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UP_TO_DATE'}

    res = await cli.get('/v1/android/1.0.0.373-628918f/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UP_TO_DATE'}


async def test_get_version_status_404(cli, assets_repo):
    res = await cli.get('/v1/windows/33/status')
    assert res.status == 404


async def test_get_version_status_400(cli, assets_repo):
    res = await cli.get('/v1/android/11/status')
    assert res.status == 400
    res = await cli.get('/v1/android/0.3/status')
    assert res.status == 400
    res = await cli.get('/v1/android/0.3-123/status')
    assert res.status == 400


async def test_get_asset_ok(cli, assets_repo):
    res = await cli.get('/v1/assets/F1')
    repo_items = list(assets_repo.head.commit.tree.traverse())
    assert res.status == 200
    assert res.content_type == 'text/plain'
    assert res.headers['X-ASSET-VERSION'] == repo_items[2].hexsha[:6]


async def test_get_asset_404(cli):
    res = await cli.get('/v1/assets/ZERO')
    assert res.status == 404

