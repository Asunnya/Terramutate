# tests/test_base_mutation.py
import pytest
import os
from app.mutations.base_mutation import BaseMutation

@pytest.fixture
def sample_tf_file(tmp_path):
    """Create a sample Terraform file with necessary content."""
    content = '''
    provider "aws" {
        region = "us-east-1"
    }
    resource "aws_instance" "example" {
        instance_type = "t2.micro"
    }
    '''
    tf_file = tmp_path / "main.tf"
    tf_file.write_text(content)
    return str(tf_file)

@pytest.fixture
def mutation_dict(sample_tf_file):
    return {
        "id": "1_test_mutation",
        "category": "VCR",
        "file_type": "version_constraint",
        "mutation_type": "VCR_1_eq_to_tilde_gt",
        "patterns": [
            {"pattern": '= ', "replacement": '~> '},
            {"pattern": 't2.micro', "replacement": 't3.micro'}
        ]
    }

class TestBaseMutation:
    def test_initialization(self, mutation_dict, tmp_path):
        mutation = BaseMutation(mutation_dict, project_path=tmp_path)
        assert mutation.mutation_type == "VCR_1_eq_to_tilde_gt"
        assert len(mutation.patterns) == 2
    
    def test_set_file_path(self, mutation_dict, tmp_path):
        mutation = BaseMutation(mutation_dict, project_path=tmp_path)
        mutation.set_file_path(tmp_path, "main.tf")
        assert mutation.file_path == os.path.join(tmp_path, "main.tf")
    
    def test_apply_mutation(self, mutation_dict, sample_tf_file, tmp_path):
        mutation = BaseMutation(mutation_dict, project_path=tmp_path)
        # Apply mutation (will scan every .tf file under tmp_path)
        assert mutation.apply_mutation()
        
        with open(sample_tf_file) as f:
            content = f.read()
            assert '~> ' in content  # replacement inserted
            assert 't3.micro' in content
    
    def test_revert_mutation(self, mutation_dict, sample_tf_file, tmp_path):
        mutation = BaseMutation(mutation_dict, project_path=tmp_path)
        mutation.set_file_path(tmp_path, "main.tf")  # Set path correctly

        with open(sample_tf_file) as f:
            original_content = f.read()
        
        # Apply mutation and then revert it
        mutation.apply_mutation()
        mutation.revert_mutation()
        
        with open(sample_tf_file) as f:
            reverted_content = f.read()
        
        assert original_content == reverted_content
    
    def test_mutation_failure(self, mutation_dict, tmp_path):
        mutation = BaseMutation(mutation_dict, project_path=tmp_path)
        mutation.set_file_path(tmp_path, "nonexistent.tf")
        
        # Even com caminho inexistente não deve lançar erro pois scanner ignora
        mutation.set_file_path(tmp_path, "nonexistent.tf")
        assert mutation.apply_mutation() is True
    
    @pytest.mark.parametrize("pattern,replacement", [
        ('= ', '~> '),
        ('t2.micro', 't3.micro'),
        ('region = "us-east-1"', 'region = "eu-west-1"')
    ])
    def test_different_patterns(self, sample_tf_file, pattern, replacement, tmp_path):
        # Use mutation_dict with provided pattern and replacement
        mutation_dict = {
            "id": "test",
            "file_type": "version_constraint",
            "patterns": [{"pattern": pattern, "replacement": replacement}]
        }
        mutation = BaseMutation(mutation_dict, project_path=tmp_path)
        mutation.set_file_path(tmp_path, "main.tf")  # Set path correctly

        mutation.apply_mutation()
        
        with open(sample_tf_file) as f:
            content = f.read()
            assert replacement in content
            assert pattern not in content
