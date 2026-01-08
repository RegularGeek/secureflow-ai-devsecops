import json
import os
from typing import Any, Dict

import boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource("dynamodb")
HISTORY_TABLE = os.environ.get("HISTORY_TABLE", "")


def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json",
            "access-control-allow-origin": "*",
            "access-control-allow-methods": "GET,POST,OPTIONS",
            "access-control-allow-headers": "content-type",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _response(200, {"ok": True})

    qs = event.get("queryStringParameters") or {}
    app_name = (qs.get("app_name") or "demo").strip()
    limit = int(qs.get("limit") or 10)

    if not HISTORY_TABLE:
        return _response(500, {"error": "HISTORY_TABLE not configured"})

    table = ddb.Table(HISTORY_TABLE)
    pk = f"APP#{app_name}"

    resp = table.query(
        KeyConditionExpression=Key("pk").eq(pk) & Key("sk").begins_with("TS#"),
        ScanIndexForward=False,  # latest first
        Limit=max(1, min(limit, 50)),
    )

    items = resp.get("Items", [])
    return _response(200, {"app_name": app_name, "count": len(items), "items": items})
