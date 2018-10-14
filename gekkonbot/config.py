import os
import json

CONFIG_DIR = os.getcwd()

with open(os.path.join(CONFIG_DIR, 'config.json'), 'r', encoding='utf-8') as config_file:
    config = json.loads(config_file.read())

config['google-credentials-path'] = os.path.join(CONFIG_DIR, 'google_service.json')
