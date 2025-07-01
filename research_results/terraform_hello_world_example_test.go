package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestTerraformHelloWorldExample(t *testing.T) {
	// website::tag::2:: Construct the terraform options with default retryable errors to handle the most common
	// retryable errors in terraform testing.
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		// website::tag::1:: Set the path to the Terraform code that will be tested.
		TerraformDir: "..",
	})

	// website::tag::5:: Clean up resources with "terraform destroy" at the end of the test.
	defer terraform.Destroy(t, terraformOptions)

	// website::tag::3:: Run "terraform init" and "terraform apply". Fail the test if there are any errors.
	terraform.Init(t, terraformOptions)
	terraform.Plan(t, terraformOptions)
	terraform.Apply(t, terraformOptions)
	//terraform.InitAndPlan(t, terraformOptions)

	validateApiGateway(t, terraformOptions)
	validateDynamoDB(t, terraformOptions)
	validateIAMPoliciesAndRoles(t, terraformOptions)
	validateLambdaRequest(t, terraformOptions)
	validateLambdaReports(t, terraformOptions)
	//validateSqsToLambdaTrigger(t, terraformOptions)
	// website::tag::4:: Run `terraform output` to get the values of output variables and check they have the expected values.

}

func validateApiGateway(t *testing.T, terraformOptions *terraform.Options) {
	aws_api_gateway_http_method := terraform.Output(t, terraformOptions, "aws_api_gateway_http_method")
	assert.Equal(t, "ANY", aws_api_gateway_http_method)

	aws_api_gateway_http_authorization := terraform.Output(t, terraformOptions, "aws_api_gateway_http_authorization")
	assert.Equal(t, "NONE", aws_api_gateway_http_authorization)

	aws_api_gateway_integration_http_method := terraform.Output(t, terraformOptions, "aws_api_gateway_integration_http_method")
	assert.Equal(t, "POST", aws_api_gateway_integration_http_method)

	aws_api_gateway_integration_type := terraform.Output(t, terraformOptions, "aws_api_gateway_integration_type")
	assert.Equal(t, "AWS_PROXY", aws_api_gateway_integration_type)
}

func validateDynamoDB(t *testing.T, terraformOptions *terraform.Options) {
	aws_dynamodb_table_name := terraform.Output(t, terraformOptions, "aws_dynamodb_table_name")
	assert.Equal(t, "products-table", aws_dynamodb_table_name)

	aws_dynamodb_table_id := terraform.Output(t, terraformOptions, "aws_dynamodb_table_hash_key")
	assert.Equal(t, "id", aws_dynamodb_table_id)
}

func validateIAMPoliciesAndRoles(t *testing.T, terraformOptions *terraform.Options) {
	// Validate SQS Read Policy
	sqsPolicyArn := terraform.Output(t, terraformOptions, "aws_iam_policy_sqs_read_policy_arn")
	assert.Contains(t, sqsPolicyArn, "arn:aws:iam")

	// Validate Lambda Role
	lambdaRoleArn := terraform.Output(t, terraformOptions, "aws_iam_role_lambda_report_role_arn")
	assert.Contains(t, lambdaRoleArn, "arn:aws:iam")

	// Validate Lambda Role Policy Attachments
	sqsPolicyAttachment := terraform.Output(t, terraformOptions, "aws_iam_role_policy_attachment_attach_sqs_to_lambda_report_role_id")
	assert.NotEmpty(t, sqsPolicyAttachment)

	s3PolicyAttachment := terraform.Output(t, terraformOptions, "aws_iam_role_policy_attachment_attach_s3_policy_to_lambda_report_role_id")
	assert.NotEmpty(t, s3PolicyAttachment)

	// Validate SNS Publish Policy
	snsPublishPolicyArn := terraform.Output(t, terraformOptions, "aws_iam_policy_sns_publish_policy_arn")
	assert.Contains(t, snsPublishPolicyArn, "arn:aws:iam")

	// Validate Lambda Request Role
	lambdaRequestRoleArn := terraform.Output(t, terraformOptions, "aws_iam_role_lambda_request_role_arn")
	assert.Contains(t, lambdaRequestRoleArn, "arn:aws:iam")

	// Validate SNS Policy Attachment for Lambda Request Role
	snsPolicyAttachment := terraform.Output(t, terraformOptions, "aws_iam_role_policy_attachment_attach_sns_policy_to_lambda_request_role_id")
	assert.NotEmpty(t, snsPolicyAttachment)

	// Validate S3 Policy Attachment for Lambda Request Role
	s3ReportPolicyAttachment := terraform.Output(t, terraformOptions, "aws_iam_role_policy_attachment_attach_s3_policy_to_lambda_request_role_id")
	assert.NotEmpty(t, s3ReportPolicyAttachment)
}

func validateLambdaReports(t *testing.T, terraformOptions *terraform.Options) {
	// Validate Lambda function name
	lambdaReportsName := terraform.Output(t, terraformOptions, "aws_lambda_function_lambda_reports_function_name")
	assert.Equal(t, "lambda-reports", lambdaReportsName)

	// Validate Lambda role
	lambdaReportsRole := terraform.Output(t, terraformOptions, "aws_lambda_function_lambda_reports_role")
	assert.Contains(t, lambdaReportsRole, "arn:aws:iam")

}

func validateLambdaRequest(t *testing.T, terraformOptions *terraform.Options) {
	// Validate Lambda function name
	lambdaRequestName := terraform.Output(t, terraformOptions, "aws_lambda_function_lambda_request_function_name")
	assert.Equal(t, "lambda-request", lambdaRequestName)

	// Validate Lambda role
	lambdaRequestRole := terraform.Output(t, terraformOptions, "aws_lambda_function_lambda_request_role")
	assert.Contains(t, lambdaRequestRole, "arn:aws:iam")

}
