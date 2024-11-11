# tests/test_mutation_framework.py
import pytest
import os
import shutil
from app.framework import MutationFramework

@pytest.fixture
def terraform_project(tmp_path):
    """Create a sample Terraform project structure"""
    project_dir = tmp_path / "terraform_project"
    project_dir.mkdir()
    
    infra_dir = project_dir / "infrastructure"
    infra_dir.mkdir()
    
    provider_file = infra_dir / "provider.tf"
    provider_file.write_text('provider "aws" {\n  region = "us-east-1"\n}')
    
    instance_file = infra_dir / "instance.tf"
    instance_file.write_text('resource "aws_instance" "example" {\n  instance_type = "t2.micro"\n}')
    
    return str(project_dir)

@pytest.fixture
def framework(terraform_project):
    """Create framework instance with real project structure"""
    config_json = {
        "terraform_paths": {
            "root_folder": "infrastructure/",
            "infrastructure_folder": "infrastructure/",
            "test_folder": "test/"
        }
    }
    
    config_yaml = {
        "mutation_mode": "individual",
        "mutation_categories": ["POR"],
        "mutations": [{
            "category": "POR",
            "file_type": "provider",
            "mutation_type": "provider_aws_to_google",
            "file_path": "provider.tf",
            "patterns": [{"pattern": "aws", "replacement": "google"}],
            "id": "1_test_mutation"
        }]
    }
    
    framework = MutationFramework(terraform_project, config_json, config_yaml)
    yield framework
    if os.path.exists(framework.copy_path):
        shutil.rmtree(framework.copy_path)

def test_initialize_framework(framework):
    assert framework.original_path is not None
    assert framework.config_json["terraform_paths"]["root_folder"] == "infrastructure/"
    assert framework.mutation_mode == "individual"

@pytest.mark.parametrize("mutation_mode", ["individual", "categorized"])
def test_load_mutation(terraform_project, mutation_mode):
    config_json = {"terraform_paths": {"infrastructure_folder": "infrastructure/"}}
    config_yaml = {
        "mutation_mode": mutation_mode,
        "mutation_categories": ["POR"],
        "mutations": [{
            "category": "POR",
            "id": "1_test",
            "file_path": "provider.tf",
            "file_type": "provider",
            "patterns": [{"pattern": "aws", "replacement": "google"}]
        }
        ,
        {
            "category": "VOR",
            "id": "2_region_us_east_to_eu_west",
            "file_path": "provider.tf",
            "file_type": "provider",
            "patterns": [{"pattern": 'region = "us-east-1"', "replacement": 'region = "eu-west-1"'}]

        }        
        ]
    }
    
    framework = MutationFramework(terraform_project, config_json, config_yaml)
    mutations = framework.load_mutation()
    
    if mutation_mode == "individual":
        assert isinstance(mutations, list)
        for mutation in mutations:
            assert isinstance(mutation, dict)
            assert "id" in mutation
            assert "category" in mutation
            assert "patterns" in mutation
    else:
        assert isinstance(mutations, list)
        print(mutations)
        for category_dict in mutations:
            assert isinstance(category_dict, dict)
            for category, mutation_list in category_dict.items():
                assert category in ["POR", "VOR"]
                assert isinstance(mutation_list, list)
                for mutation in mutation_list:
                    assert "id" in mutation
                    assert "category" in mutation
                    assert "patterns" in mutation

def test_apply_mutation(framework):
    project_path = framework.create_copy()
    
    #create a fake provider file

    

    
    provider_file = os.path.join(project_path, "infrastructure", "provider.tf")
    
    if not os.path.exists(provider_file):
        with open(provider_file, "w") as f:
            f.write('provider "aws" { region = "us-east-1" }')

    mutation = framework.config_yaml["mutations"][0]

    framework.apply_mutation(mutation, project_path)
    
    with open(provider_file, "w") as f:
        content = f.read()
        assert 'provider "google"' in content
        assert 'provider "aws"' not in content

def test_mutation_results(framework):
    project_path = framework.create_copy()
    provider_file = os.path.join(project_path, "infrastructure", "provider.tf")
    
    if not os.path.exists(provider_file):
        with open(provider_file, "w") as f:
            f.write('provider "aws" { region = "us-east-1" }')
    
    framework.run()
    
    with open(provider_file) as f:
        content = f.read()
        assert 'provider "google"' in content