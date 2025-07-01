# tests/test_granular_mutation.py
import os
import re
import pytest
from app.mutations.base_mutation import BaseMutation


@pytest.fixture
def multi_occurrence_tf_file(tmp_path):
    """Create a TF file with multiple occurrences of the same pattern."""
    content = """
    variable "instances" {
      default = {
        instance1 = {
          count = 1
        }
        instance2 = {
          count = 1
        }
        instance3 = {
          count = 1
        }
      }
    }
    """
    tf_file = tmp_path / "vars.tf"
    tf_file.write_text(content)
    return str(tf_file)


@pytest.fixture
def granular_mutation_dict():
    return {
        "id": "cmr_big_up",
        "category": "CMR",
        "file_path": "vars.tf",
        "file_type": "configuration",
        "mutation_type": "CMR_BIG_UP",
        "patterns": [
            {"pattern": r"count = 1", "replacement": "count = 1000"},
        ],
    }


def test_find_occurrences(multi_occurrence_tf_file, granular_mutation_dict, tmp_path):
    mutation = BaseMutation(granular_mutation_dict, project_path=tmp_path)
    mutation.set_file_path(tmp_path, "vars.tf")
    assert mutation.find_occurrences() == 3


def test_apply_single_occurrence(multi_occurrence_tf_file, granular_mutation_dict, tmp_path):
    mutation = BaseMutation(granular_mutation_dict, project_path=tmp_path)
    mutation.set_file_path(tmp_path, "vars.tf")

    # Apply only the second occurrence (index 1)
    mutation.apply_mutation(only_idx=1)

    with open(multi_occurrence_tf_file) as f:
        content = f.read()

    # Exactly one replacement should exist
    assert len(re.findall(r"count = 1000", content)) == 1
    # Two original occurrences should remain. Use negative look-ahead so we don't
    # match the digit "1" inside the newly-created "1000" replacement.
    assert len(re.findall(r"count = 1(?!\d)", content)) == 2

    # Clean up
    mutation.revert_mutation()


def test_generate_granular_mutants(multi_occurrence_tf_file, granular_mutation_dict, tmp_path):
    mutation = BaseMutation(granular_mutation_dict, project_path=tmp_path)
    mutation.set_file_path(tmp_path, "vars.tf")

    indices = list(mutation.generate_granular_mutants())
    assert indices == [0, 1, 2]

    # After generator completes, file should be identical to original (no replacements)
    with open(multi_occurrence_tf_file) as f:
        final_content = f.read()

    assert "count = 1000" not in final_content
    assert len(re.findall(r"count = 1(?!\d)", final_content)) == 3 