import pytest
from app.mutations.base_mutation import BaseMutation
from pathlib import Path

# Helper to write a TF file and get path

def _write_tf(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content)
    return str(p)

@pytest.mark.parametrize(
    "variant_id,pattern,replacement,content_before,expected_after,file_name",
    [
        (
            "VCR_1_eq_to_tilde_gt",
            "= ",
            "~> ",
            'terraform {\n  required_providers {\n    aws = { version = "= 4.0" }\n  }\n}',
            "~> ",
            "versions.tf",
        ),
        (
            "SAR_INS",
            "resource ",
            "#checkov:skip=CKV_PLACEHOLDER \"injected by mutation\"\nresource ",
            'resource "aws_s3_bucket" "logs" {\n  bucket = "my-bucket"\n}',
            "#checkov:skip",
            "main.tf",
        ),
        (
            "IPR_ACT_DEL",
            "Action = \\[.*?\\]",
            "Action = []",
            'data "aws_iam_policy_document" "example" {\n  statement {\n    Action = ["s3:GetObject"]\n  }\n}',
            "Action = []",
            "iam.tf",
        ),
        (
            "IVR_VAL_DEL",
            "default = .*",
            "# default removed",
            'variable "env" {\n  type = string\n  default = "prod"\n}',
            "# default removed",
            "variables.tf",
        ),
        (
            "PDR_CFG",
            "region = \"us-east-1\"",
            "region = \"eu-central-1\"",
            'provider "aws" {\n  region = "us-east-1"\n}',
            "eu-central-1",
            "providers.tf",
        ),
        (
            "PVCR_VER_DEL",
            "version = .*",
            "# version removed",
            'terraform {\n  required_providers {\n    aws = { version = "~> 5.40" }\n  }\n}',
            "# version removed",
            "providers.tf",
        ),
    ],
)

def test_variant_mutation(tmp_path, variant_id, pattern, replacement, content_before, expected_after, file_name):
    """For each variant ensure replacement is applied once and revert returns original."""
    file_path_str = _write_tf(tmp_path, file_name, content_before)

    mutation_dict = {
        "id": f"test_{variant_id}",
        "category": variant_id.split("_")[0],
        "file_path": file_name,
        "mutation_type": variant_id,
        "patterns": [{"pattern": pattern, "replacement": replacement}],
    }

    mut = BaseMutation(mutation_dict, project_path=tmp_path)

    # Apply mutation
    mut.apply_mutation()
    with open(file_path_str) as f:
        mutated = f.read()
    assert expected_after in mutated

    # Revert and check original restored
    mut.revert_mutation()
    with open(file_path_str) as f:
        reverted = f.read()
    assert reverted == content_before 