# config/loader.py

import json
import yaml

def load_config_json(path):
    """Loads JSON configuration from a specified path."""
    with open(path, 'r') as f:
        return json.load(f)

def load_config_yaml(path):
    """Loads YAML configuration from a specified path."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)
