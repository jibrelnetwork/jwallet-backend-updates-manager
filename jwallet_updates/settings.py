import os

ASSETS_REPO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets')
ASSETS_IDS_FILE = os.path.join(ASSETS_REPO_PATH, 'assets_index.json')
ACTUAL_VERSIONS_FILE = os.path.join(os.path.dirname(__file__), 'versions_status.json')

RAVEN_DSN = os.getenv('RAVEN_DSN')

ANDROID = 'android'
IOS = 'ios'
PLATFORMS = (IOS, ANDROID)

CONFIG_SECRET = os.getenv('CONFIG_SECRET')
