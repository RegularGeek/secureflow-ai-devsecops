import json
import os
import time
import uuid
from typing import Any, Dict, Tuple

import boto3
from botocore.exceptions import ClientError

from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

bedrock = boto3.client("bedrock-runtime")
ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

HISTORY_TABLE = os.environ.get("HISTORY_TABLE", "")
LOG_BUCKET = os.environ.get("LOG_BUCKET", "")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "")


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


def _parse_body(event: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    body = event.get("body")
    if body is None:
        return {}, ""
    if isinstance(body, str):
        try:
            return json.loads(body), body
        except Exception:
            return {}, body
    return body, json.dumps(body)


def _safe_get(d: Dict[str, Any], key: str, default: Any = "") -> Any:
    val = d.get(key, default)
    return val if val is not None else default


def _invoke_anthropic_claude(prompt: str) -> Dict[str, Any]:
    # Anthropic on Bedrock commonly uses this schema:
    # https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_InvokeModel_AnthropicClaude_section.html
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 800,
        "temperature": 0.2,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
    }

    try:
        resp = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        raw = resp["body"].read().decode("utf-8")
        return json.loads(raw)
    except ClientError as e:
        raise RuntimeError(f"Bedrock invoke failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected Bedrock response: {e}")


def _extract_text_from_anthropic(resp: Dict[str, Any]) -> str:
    # Typical: {"content":[{"type":"text","text":"..."}], ...}
    content = resp.get("content", [])
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and "text" in first:
            return str(first["text"])
    # fallback
    return json.dumps(resp)


def _store_history(item: Dict[str, Any]) -> None:
    if not HISTORY_TABLE:
        return
    table = ddb.Table(HISTORY_TABLE)
    table.put_item(Item=item)


def _store_log(key: str, payload: Dict[str, Any]) -> None:
    if not LOG_BUCKET:
        return
    s3.put_object(
        Bucket=LOG_BUCKET,
        Key=key,
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",
    )


def lambda_handler(event, context):
    # CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return _response(200, {"ok": True})

    payload, raw_body = _parse_body(event)

    input_type = _safe_get(payload, "input_type", "iac")
    language = _safe_get(payload, "language", "text")
    content = _safe_get(payload, "content", "")
    ctx = _safe_get(payload, "context", {}) or {}
    app_name = _safe_get(ctx, "app_name", "unknown")
    environment = _safe_get(ctx, "environment", "unknown")

    if not isinstance(content, str) or len(content.strip()) < 10:
        return _response(400, {"error": "content is required (min 10 characters)"})

    request_id = str(uuid.uuid4())
    ts = int(time.time())

    prompt = USER_PROMPT_TEMPLATE.format(
        input_type=input_type,
        language=language,
        app_name=app_name,
        environment=environment,
        content=content[:12000],  # cost + latency control
    )

    try:
        br_resp = _invoke_anthropic_claude(prompt)
        model_text = _extract_text_from_anthropic(br_resp).strip()

        # Expect JSON-only output
        try:
            result = json.loads(model_text)
        except json.JSONDecodeError:
            result = {
                "overall_severity": "MEDIUM",
                "findings": [],
                "summary": "Model returned non-JSON output; please adjust prompt/model settings.",
                "raw_output": model_text[:4000],
            }

        history_item = {
            "pk": f"APP#{app_name}",
            "sk": f"TS#{ts}#{request_id}",
            "request_id": request_id,
            "ts": ts,
            "input_type": input_type,
            "language": language,
            "environment": environment,
            "overall_severity": result.get("overall_severity", "MEDIUM"),
            "summary": result.get("summary", ""),
        }
        _store_history(history_item)

        _store_log(
            f"analysis/{app_name}/{ts}-{request_id}.json",
            {
                "request": {
                    "request_id": request_id,
                    "input_type": input_type,
                    "language": language,
                    "environment": environment,
                    "content_preview": content[:500],
                },
                "response": result,
            },
        )

        return _response(200, {"request_id": request_id, "result": result})

    except Exception as e:
        _store_log(
            f"errors/{app_name}/{ts}-{request_id}.json",
            {"request_id": request_id, "error": str(e), "raw_body": raw_body[:2000]},
        )
        return _response(500, {"error": "Internal error", "request_id": request_id})
