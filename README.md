# jwallet-backend-updates-manager
jWallet backend app for mobile apps updates management

## Prerequisites
Ubuntu 16.04, Python3.7
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.7 python3-pip
```

## Installation
```
git clone git@github.com:jibrelnetwork/jwallet-backend-updates-manager.git
cd jwallet-backend-updates-manager
pip install -r requirements.txt
```

## Configuration
No configs needed

## Running tests
```
pip install -r test-requirements.txt
pytest jwallet_updates/tests.py
```

## Running app

development:
```
python jwallet_updates/app.py
```
production:
```
gunicorn --bind localhost:8000 jwallet_updates.app:make_app  --worker-class aiohttp.worker.GunicornWebWorker
```

## API

Get update status for particular mobile app version:
```
GET /v1/<platform>/<version>/status

200 OK
{
    "status": UP_TO_DATE|UPDATE_REQUIRED,
}
```

Check assets updates available:
```
POST /v1/check_assets_updates
[
    {"id": "ICON_1", "version": "123abc"},
    {"id": "SERVERS": "version": "122caa"},
    {"id": "ICON_2": "version": "aabb22"}
]

200 OK
[
    "SERVERS",
    "ICON_2",
]
```
In this example ICON_1 is up-to-date, SERVERS and ICON_2 has updates

Get asset file (with its version):
```
GET /v1/assets/<asset_id>

200 OK
Content-Type: image/png
X-ASSET-VERSION: 119ac6
...file contents...
```
actually it is easy to calculate asset version at client side: `sha1('blob {file_size}\0{file_content}')`


## Assets management

1. Add or change asset files at assets repo (`jibrelnetwork/jwallet-assets`)
2. Update assets index file (`jibrelnetwork/jwallet-assets:assets_index.json`)
3. push assets changes at `master` branch
4. update submodule `assets` at (`jibrelnetwork/jwallet-backend-updates-manager`) repo


## Versions management

1. Update `jibrelnetwork/jwallet-backend-updates-manager:actual_versions.json` file - it should contain actual versions (no update required) of mobile apps for each platform
2. commit and push