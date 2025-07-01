import pytest
from app.framework import MutationFramework


def _make_framework(tmp_path, include_cats=None, include_types=None):
    project_dir = tmp_path / "iac"
    project_dir.mkdir()
    infra_dir = project_dir / "infrastructure"
    infra_dir.mkdir()
    (infra_dir / "versions.tf").write_text('terraform { required_providers { aws = { version = "= 4.0" } } }')

    config_json = {"terraform_paths": {"infrastructure_folder": "infrastructure/"}}

    config_yaml = {
        "mutation_mode": "individual",
        "mutations": [
            {
                "id": "vcr1",
                "category": "VCR",
                "mutation_type": "VCR_1_eq_to_tilde_gt",
                "file_path": "versions.tf",
                "file_type": "version_constraint",
                "patterns": [{"pattern": "= ", "replacement": "~> "}]
            },
            {
                "id": "vcr3",
                "category": "VCR",
                "mutation_type": "VCR_3_tilde_gt_to_gte",
                "file_path": "versions.tf",
                "file_type": "version_constraint",
                "patterns": [{"pattern": "~> ", "replacement": ">= "}]
            },
            {
                "id": "cmr1",
                "category": "CMR",
                "mutation_type": "CMR_BIG_UP",
                "file_path": "main.tf",
                "file_type": "meta_argument",
                "patterns": [{"pattern": "count = 1", "replacement": "count = 10000"}]
            },
        ],
    }
    if include_cats:
        config_yaml["include_categories"] = include_cats
    if include_types:
        config_yaml["include_mutation_types"] = include_types

    return MutationFramework(str(project_dir), config_json, config_yaml)


def test_filter_by_category(tmp_path):
    fw = _make_framework(tmp_path, include_cats=["VCR"])
    muts = fw.load_mutation()
    assert all(m["category"] == "VCR" for m in muts)
    assert len(muts) >= 1


def test_filter_by_category_and_type(tmp_path):
    fw = _make_framework(tmp_path, include_cats=["VCR"], include_types=["VCR_1_eq_to_tilde_gt"])
    muts = fw.load_mutation()
    assert len(muts) == 1
    assert muts[0]["mutation_type"] == "VCR_1_eq_to_tilde_gt" 