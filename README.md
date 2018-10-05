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
Environment vars required:
```
JWALLET_ASSETS_REPO_PATH - absolute filesystem path to git repository with jWallet updates
```

## Running tests
```
pip install -r test-requirements.txt
pytest jwallet_updates/tests.py
```

## Running app
```
python jwallet_updates/app.py
```

## API

Get update status for particular version:
```
GET /v1/<platform>/<locale>/<version>/status

200 OK
{
    "status": UP_TO_DATE|UPDATE_AVAILABLE|UPDATE_REQUIRED,
    "updateDescription": "some text",
}
```

