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

###Get update status for particular mobile app version:

```
GET /v1/<platform>/<version>/status

200 OK
{
    "status": "UP_TO_DATE"|"UPDATE_REQUIRED"
}
```

###Check assets updates available:

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

For example. Check updates availability for mainnet and ropsten assets.json
```
POST /v1/check_assets_updates
[
    {
        "id": "mainnet",
        "version": "123abc"
    },
    {
        "id": "ropsten",
        "version": "122caa"
    }
]

200 OK
[
    "mainnet",
    "ropsten"
]
```

#### Get asset file (with its version):

```
GET /v1/assets/<asset_id>

200 OK
Content-Type: image/png
X-ASSET-VERSION: 119ac6
...file contents...
```
actually it is easy to calculate asset version at client side: `sha1('blob {file_size}\0{file_content}')`

For example. Get latest version of mainnet assets.json
```
GET /v1/assets/mainnet

200 OK
X-ASSET-VERSION: 324b1c
Content-Type: application/json
[
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
      "isDefaultForcedDisplay": true,
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
```

Get latest version of ropsten assets.json

```
GET /v1/assets/ropsten

200 OK
X-ASSET-VERSION: 80914e
Content-Type: application/json
[
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
      "isDefaultForcedDisplay": true,
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
```


## Assets management

1. Add or change asset files at assets repo (`jibrelnetwork/jwallet-assets`)
2. Update assets index file (`jibrelnetwork/jwallet-assets:assets_index.json`)
3. push assets changes at `master` branch
4. update submodule `assets` at (`jibrelnetwork/jwallet-backend-updates-manager`) repo


## Versions management

1. Update `jibrelnetwork/jwallet-backend-updates-manager:actual_versions.json` file - it should contain actual versions (no update required) of mobile apps for each platform
2. commit and push