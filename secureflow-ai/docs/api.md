# SecureFlow AI API

## POST /analyze
Request:
```json
{
  "input_type": "iac",
  "language": "terraform",
  "content": "....",
  "context": { "app_name": "demo", "environment": "dev" }
}
```

Response:
```json
{
  "request_id": "uuid",
  "result": {
    "overall_severity": "HIGH",
    "findings": [],
    "summary": "..."
  }
}
```

## GET /history?app_name=demo&limit=10
Response:
```json
{
  "app_name": "demo",
  "count": 2,
  "items": [
    {
      "pk": "APP#demo",
      "sk": "TS#...",
      "overall_severity": "MEDIUM",
      "summary": "..."
    }
  ]
}
```
