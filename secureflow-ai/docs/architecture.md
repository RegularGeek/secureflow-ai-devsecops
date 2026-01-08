# SecureFlow AI Architecture

## Request Flow
1. User submits code/config via UI or API.
2. API Gateway receives request and triggers **AnalyzeFunction** (Lambda).
3. AnalyzeFunction validates input and invokes **Amazon Bedrock** (Claude Sonnet 4.5) to generate findings.
4. AnalyzeFunction stores metadata in **DynamoDB** (history) and writes logs to **S3**.
5. API Gateway returns structured findings to the user.
6. **CloudWatch** captures logs and metrics.

## History Flow
- `GET /history` triggers **HistoryFunction** (Lambda) which queries DynamoDB and returns recent analysis items.

## Diagram
See `docs/images/architecture.png`.
