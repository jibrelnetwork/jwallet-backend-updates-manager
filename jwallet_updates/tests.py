import os
import shutil
from unittest import mock
import json

import git
import pytest

from jwallet_updates.app import make_app


repo_path = '/tmp/jwallet_assets_test_repo'
os.environ['JWALLET_ASSETS_REPO_PATH'] = repo_path


@pytest.fixture
def assets_repo():
    versions = {
        'ios': ['0.3', '0.2'],
        'android': ['22', '33'],
    }

    assets_index = {
        'F1': 'file1.txt',
        'F2': 'file2.txt',
        'F3': 'dir_one/file3.txt',
        'F4': 'dir_one/file4.txt',
    }
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

    with open(os.path.join(repo_path, 'assets_index.json'), 'w') as f:
        json.dump(assets_index, f)
    repo.git.add('assets_index.json')

    repo.index.commit('start')
    yield repo
    shutil.rmtree(repo_path)


async def test_get_updates_blank(aiohttp_client, loop, assets_repo):
    with mock.patch('jwallet_updates.app.settings') as m:
        m.ASSETS_REPO_PATH = repo_path
        m.ACTUAL_VERSIONS_FILE = '/tmp/jwallet_updates_test_versions.json'
        m.ASSETS_IDS_FILE = repo_path + '/assets_index.json'
        cli = await aiohttp_client(make_app())
    res = await cli.post('/v1/check_assets_updates', json=[{'id': 'no_such_file.txt', 'version': 'abc'}])
    assert res.status == 200
    assert await res.json() == []


async def test_get_updates(aiohttp_client, loop, assets_repo):
    with mock.patch('jwallet_updates.app.settings') as m:
        m.ASSETS_REPO_PATH = repo_path
        m.ACTUAL_VERSIONS_FILE = '/tmp/jwallet_updates_test_versions.json'
        m.ASSETS_IDS_FILE = repo_path + '/assets_index.json'
        cli = await aiohttp_client(make_app())
        repo_items = list(assets_repo.head.commit.tree.traverse())
    res = await cli.post('/v1/check_assets_updates',
                         json=[
                            {'id': 'F4', 'version': repo_items[-1].hexsha[:6]},
                            {'id': 'F3', 'version': 'bca'},
                            {'id': 'F1', 'version': 'abc'},
                          ]
                        )
    assert res.status == 200
    assert await res.json() == ['F3', 'F1']


async def test_get_updates_change_files(aiohttp_client, loop, assets_repo):
    with mock.patch('jwallet_updates.app.settings') as m:
        m.ASSETS_REPO_PATH = repo_path
        m.ACTUAL_VERSIONS_FILE = '/tmp/jwallet_updates_test_versions.json'
        m.ASSETS_IDS_FILE = repo_path + '/assets_index.json'
        cli = await aiohttp_client(make_app())
    repo_items = list(assets_repo.head.commit.tree.traverse())

    current_versions = [
                            {'id': 'F4', 'version': repo_items[-1].hexsha[:6]},
                            {'id': 'F3', 'version': repo_items[-2].hexsha[:6]},
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

    with mock.patch('jwallet_updates.app.settings') as m:
        m.ASSETS_REPO_PATH = repo_path
        m.ACTUAL_VERSIONS_FILE = '/tmp/jwallet_updates_test_versions.json'
        m.ASSETS_IDS_FILE = repo_path + '/assets_index.json'
        cli = await aiohttp_client(make_app())

    res = await cli.post('/v1/check_assets_updates', json=current_versions)
    assert res.status == 200
    assert await res.json() == ['F1']


async def test_get_version_status_not_ok(aiohttp_client, loop, assets_repo):
    with mock.patch('jwallet_updates.app.settings') as m:
        m.ASSETS_REPO_PATH = repo_path
        m.ACTUAL_VERSIONS_FILE = '/tmp/jwallet_updates_test_versions.json'
        m.ASSETS_IDS_FILE = repo_path + '/assets_index.json'
        cli = await aiohttp_client(make_app())
    res = await cli.get('/v1/ios/0.1/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UPDATE_REQUIRED'}


async def test_get_version_status_ok(aiohttp_client, loop, assets_repo):
    with mock.patch('jwallet_updates.app.settings') as m:
        m.ASSETS_REPO_PATH = repo_path
        m.ACTUAL_VERSIONS_FILE = '/tmp/jwallet_updates_test_versions.json'
        m.ASSETS_IDS_FILE = repo_path + '/assets_index.json'
        cli = await aiohttp_client(make_app())
    res = await cli.get('/v1/android/33/status')
    assert res.status == 200
    assert await res.json() == {'status': 'UP_TO_DATE'}


async def test_get_version_status_404(aiohttp_client, loop, assets_repo):
    with mock.patch('jwallet_updates.app.settings') as m:
        m.ASSETS_REPO_PATH = repo_path
        m.ACTUAL_VERSIONS_FILE = '/tmp/jwallet_updates_test_versions.json'
        m.ASSETS_IDS_FILE = repo_path + '/assets_index.json'
        cli = await aiohttp_client(make_app())
    res = await cli.get('/v1/windows/33/status')
    assert res.status == 404
