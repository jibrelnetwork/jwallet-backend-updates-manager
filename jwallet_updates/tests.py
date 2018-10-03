import os
import shutil

import git
import pytest


repo_path = '/tmp/jwallet_assets_test_repo'
os.environ['JWALLET_ASSETS_REPO_PATH'] = repo_path


from jwallet_assets.app import make_app


@pytest.fixture
def assets_repo():
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
    repo.index.commit('start')
    yield repo
    shutil.rmtree(repo_path)


async def test_get_updates_blank(aiohttp_client, loop, assets_repo):
    cli = await aiohttp_client(make_app())
    res = await cli.post('/v1/check_updates', json=[{'id': 'no_such_file.txt', 'version': 'abc'}])
    assert res.status == 200
    assert await res.json() == []


async def test_get_updates(aiohttp_client, loop, assets_repo):
    cli = await aiohttp_client(make_app())
    repo_items = list(assets_repo.head.commit.tree.traverse())
    res = await cli.post('/v1/check_updates',
                         json=[
                            {'id': 'dir_one/file4.txt', 'version': repo_items[-1].hexsha[:6]},
                            {'id': 'dir_one/file3.txt', 'version': 'bca'},
                            {'id': 'file1.txt', 'version': 'abc'},
                          ]
                        )
    assert res.status == 200
    assert await res.json() == ['dir_one/file3.txt', 'file1.txt']


async def test_get_updates_change_files(aiohttp_client, loop, assets_repo):
    cli = await aiohttp_client(make_app())
    repo_items = list(assets_repo.head.commit.tree.traverse())
    current_versions = [
                            {'id': 'dir_one/file4.txt', 'version': repo_items[-1].hexsha[:6]},
                            {'id': 'dir_one/file3.txt', 'version': repo_items[-2].hexsha[:6]},
                            {'id': 'file1.txt', 'version': repo_items[1].hexsha[:6]},
                          ]
    res = await cli.post('/v1/check_updates', json=current_versions)
    assert res.status == 200
    assert await res.json() == []
    fname = os.path.join(assets_repo.working_tree_dir, 'file1.txt')
    with open(fname, 'a') as f:
        f.write('z')
    
    res = await cli.post('/v1/check_updates', json=current_versions)
    assert res.status == 200
    assert await res.json() == []
    
    assets_repo.git.add('file1.txt')
    assets_repo.index.commit('chage file1.txt')

    res = await cli.post('/v1/check_updates', json=current_versions)
    assert res.status == 200
    assert await res.json() == ['file1.txt']

