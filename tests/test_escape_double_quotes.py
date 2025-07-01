from app.mutations.base_mutation import BaseMutation


def test_double_quote_replacement(tmp_path):
    """Ensure replacements containing double quotes are preserved after mutation.

    Historically, patterns whose *replacement* strings embed double quotes (e.g.,
    `#checkov:skip=CKV_PLACEHOLDER "injected by mutation"`) have been error-prone
    due to escaping issues either in YAML loading or during the `re.sub` call.

    This regression test verifies that the exact replacement with the inner
    quotes is written to the target file.
    """

    # Create a minimal Terraform file to mutate.
    file_name = "main.tf"
    file_path = tmp_path / file_name
    file_path.write_text(
        'resource "aws_s3_bucket" "logs" {\n  bucket = "my-bucket"\n}'
    )

    # Define the mutation that injects a Skip comment containing quotes.
    mutation_dict = {
        "id": "test_double_quote_escape",
        "category": "SAR",
        "file_path": file_name,
        "patterns": [
            {
                "pattern": "resource ",
                "replacement": '#checkov:skip=CKV_PLACEHOLDER "injected by mutation"\nresource ',
            }
        ],
    }

    mut = BaseMutation(mutation_dict, project_path=tmp_path)

    # Apply the mutation.
    mut.apply_mutation()

    # Assert the replacement (including double quotes) is present in the file.
    with open(file_path) as f:
        mutated_content = f.read()

    assert '#checkov:skip=CKV_PLACEHOLDER "injected by mutation"' in mutated_content 