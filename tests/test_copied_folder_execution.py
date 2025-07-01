import os
import subprocess
import shutil
import pytest
from app.framework import MutationFramework


def _create_sample_terraform_project(tmp_path):
    """Helper that creates a minimal Terraform project structure under *tmp_path*."""
    project_dir = tmp_path / "terraform_project"
    infra_dir = project_dir / "infrastructure"
    test_dir = infra_dir / "test"

    # Build folder hierarchy
    test_dir.mkdir(parents=True)

    # Populate with a minimal .tf file so MutationFramework can copy it
    (infra_dir / "versions.tf").write_text(
        'terraform { required_providers { aws = { version = "= 4.0" } } }',
        encoding="utf-8",
    )
    return project_dir


@pytest.fixture()
def sample_framework(tmp_path):
    """Return a MutationFramework instance backed by the temporary project."""
    project_dir = _create_sample_terraform_project(tmp_path)

    config_json = {
        "terraform_paths": {
            "root_folder": "infrastructure/",
            "infrastructure_folder": "infrastructure/",
            "test_folder": "test/",
        }
    }
    config_yaml = {
        "mutation_mode": "individual",
        "mutations": [
            {
                "id": "dummy",
                "category": "VCR",
                "file_type": "version_constraint",
                "mutation_type": "VCR_1_eq_to_tilde_gt",
                "file_path": "versions.tf",
                "patterns": [{"pattern": "= ", "replacement": "~> "}],
            }
        ],
    }

    framework = MutationFramework(str(project_dir), config_json, config_yaml)
    yield framework

    # Cleanup sandbox copy after the test finishes
    if os.path.exists(framework.copy_path):
        shutil.rmtree(framework.copy_path, ignore_errors=True)


def test_go_tests_are_executed_inside_copied_workspace(sample_framework, monkeypatch):
    """Ensure *test_mutation* runs Go tests inside `terraform_mutated_copy` folder."""

    # Prepare copied workspace (required before calling *test_mutation*)
    sample_framework.create_copy()

    captured = {}

    def fake_run(cmd, cwd=None, stdout=None, stderr=None, check=False):  # noqa: D401
        """Stub for subprocess.run capturing the *cwd* argument."""
        captured["cwd"] = cwd
        # Simulate successful `go test`
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    # Monkey-patch subprocess.run so we don't actually invoke `go`
    monkeypatch.setattr(subprocess, "run", fake_run)

    mutation_dict = {"id": "dummy", "category": "VCR"}
    sample_framework.test_mutation(mutation_dict, category="VCR", categorized=False)

    assert "terraform_mutated_copy" in captured["cwd"], "Go tests did not run inside the copied workspace."  # noqa: E501
    # The cwd should start with the framework's *copy_path*
    assert captured["cwd"].startswith(sample_framework.copy_path) 