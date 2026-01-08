SecureFlow AI (AWS SAM)
SecureFlow AI is an AI-powered DevSecOps assistant that analyzes code snippets or IaC/config files for security and compliance risks using Amazon Bedrock. It returns structured findings and stores results for history.

Recommended Region + Model (Nigeria / EMEA-friendly)
Region: Africa (Cape Town) af-south-1 (closest Bedrock-supported region to Nigeria)
Model: anthropic.claude-sonnet-4-5-20250929-v1:0 (available in af-south-1)
You must enable Model Access in the Amazon Bedrock console for the Anthropic model.

Architecture (High Level)
User/Web UI -> API Gateway -> Lambda -> Amazon Bedrock -> DynamoDB (history) + S3 (logs) -> Response
CloudWatch captures logs and metrics.

Features (MVP)
POST /analyze: analyze code/config text using Amazon Bedrock (Claude Sonnet 4.5)
Returns: severity, findings, recommended fixes (JSON)
Stores: analysis history in DynamoDB and logs in S3
GET /history?app_name=demo&limit=10: fetch recent analysis history for an app
Prerequisites
AWS CLI configured (aws configure)
AWS SAM CLI installed
Python 3.11+
Deploy (SAM)
sam build
sam deploy --guided
Suggested guided deploy inputs
Region: af-south-1
Model ID: keep default unless you change it
Run Locally (no Bedrock call)
sam build
sam local start-api
Test API
After deploy, SAM prints an ApiUrl. Example:

export API_URL="https://xxxx.execute-api.af-south-1.amazonaws.com/prod"

curl -s -X POST "$API_URL/analyze" \
  -H "Content-Type: application/json" \
  -d @events/analyze.json | jq

curl -s "$API_URL/history?app_name=demo&limit=10" | jq
Notes
Keep usage Free Tier friendly (low Lambda memory, minimal logs).
This repo is designed for competition MVP. Extend later with auth (Cognito), UI, and policy packs.
