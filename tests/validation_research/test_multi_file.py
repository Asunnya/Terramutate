import pytest
from app.mutations.base_mutation import BaseMutation


def _make_tf_files(tmp_path):
    f1 = tmp_path / "a1.tf"
    f2 = tmp_path / "a2.tf"
    content = 'terraform { required_providers { aws = { version = "= 4.0" } } }'
    f1.write_text(content)
    f2.write_text(content)
    return str(f1), str(f2)


def test_mutation_applies_to_multiple_files(tmp_path):
    file1, file2 = _make_tf_files(tmp_path)

    mutation_dict = {
        "id": "multi_vcr",
        "category": "VCR",
        "mutation_type": "VCR_1_eq_to_tilde_gt",
        # file_path deliberately omitted
        "patterns": [{"pattern": "= ", "replacement": "~> "}],
    }

    mut = BaseMutation(mutation_dict, project_path=tmp_path)
    mut.apply_mutation()  # all occurrences in all .tf files

    assert "~> " in open(file1).read()
    assert "~> " in open(file2).read()

    mut.revert_mutation()
    assert "= 4.0" in open(file1).read()
    assert "= 4.0" in open(file2).read() 