# tests/test_loader.py
import pytest
import os
import json
import yaml
from app.config.loader import load_config_json, load_config_yaml

@pytest.fixture
def sample_config_json(tmp_path):
    config = {
        "terraform_paths": {
            "root_folder": "iac-tests/",
            "infrastructure_folder": "infrastructure/",
            "test_folder": "test/"
        },
        "file_paths": {
            "instance_file": "instance.tf",
            "provider_file": "provider.tf"
        }
    }
    config_path = tmp_path / "config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    return str(config_path)

@pytest.fixture
def sample_config_yaml(tmp_path):
    config = {
        "mutation_mode": "individual",
        "mutation_categories": ["VCR"],
        "mutations": [
            {
                "category": "VCR",
                "file_type": "version_constraint",
                "mutation_type": "VCR_1_eq_to_tilde_gt",
                "file_path": "versions.tf",
                "patterns": [{"pattern": "= ", "replacement": "~> "}],
                "id": "vcr_example"
            }
        ]
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return str(config_path)

def test_load_config_json_success(sample_config_json):
    config = load_config_json(sample_config_json)
    assert "terraform_paths" in config
    assert "file_paths" in config
    assert config["terraform_paths"]["root_folder"] == "iac-tests/"

def test_load_config_json_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config_json("nonexistent.json")

def test_load_config_yaml_success(sample_config_yaml):
    config = load_config_yaml(sample_config_yaml)
    assert "mutation_mode" in config
    assert "mutations" in config
    assert len(config["mutation_categories"]) == 1

def test_load_config_yaml_invalid_format(tmp_path):
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("invalid: :")
    with pytest.raises(yaml.YAMLError):
        load_config_yaml(str(invalid_yaml))