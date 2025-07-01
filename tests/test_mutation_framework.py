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
    
    provider_file = infra_dir / "versions.tf"
    provider_file.write_text('terraform {\n  required_providers {\n    aws = {\n      version = "= 4.0"\n    }\n  }\n}')
    
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
        "mutation_categories": ["VCR"],
        "mutations": [{
            "category": "VCR",
            "file_type": "version_constraint",
            "mutation_type": "VCR_1_eq_to_tilde_gt",
            "file_path": "versions.tf",
            "patterns": [{"pattern": "= ", "replacement": "~> "}],
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
        "mutation_categories": ["VCR"],
        "mutations": [{
            "category": "VCR",
            "id": "1_test",
            "file_path": "versions.tf",
            "file_type": "version_constraint",
            "patterns": [{"pattern": "= ", "replacement": "~> "}]
        }
        ,
        {
            "category": "CMR",
            "id": "2_cmr_big_up",
            "file_path": "main.tf",
            "file_type": "meta_argument",
            "patterns": [{"pattern": "count = 1", "replacement": "count = 10000"}]

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
                assert category in ["VCR", "CMR"]
                assert isinstance(mutation_list, list)
                for mutation in mutation_list:
                    assert "id" in mutation
                    assert "category" in mutation
                    assert "patterns" in mutation

def test_apply_mutation(framework):
    project_path = framework.create_copy()
    provider_file = os.path.join(project_path, "versions.tf")
    
    if not os.path.exists(provider_file):
        with open(provider_file, "w") as f:
            f.write('terraform { required_providers { aws = { version = "= 4.0" } } }')

    mutation = framework.config_yaml["mutations"][0]

    framework.apply_mutation(mutation, project_path)
    
    # After applying the mutation once, the version delimiter should have been
    # replaced inside the copied infrastructure file.
    with open(provider_file, "r") as f:
        content = f.read()
        assert 'version ~>' in content
        assert 'version =' not in content

def test_mutation_results(framework):
    project_path = framework.create_copy()
    provider_file = os.path.join(project_path, "versions.tf")
    
    if not os.path.exists(provider_file):
        with open(provider_file, "w") as f:
            f.write('terraform { required_providers { aws = { version = "= 4.0" } } }')
    
    framework.run()

    # After running in *individual* mode every per-occurrence mutant is
    # reverted, so the original version delimiter must be restored and the
    # replacement should NOT persist.
    with open(provider_file, "r") as f:
        content = f.read()
        assert 'version =' in content
        assert 'version ~>' not in content