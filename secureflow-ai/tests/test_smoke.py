import json

def test_payload_shape():
    payload = {
        "input_type": "iac",
        "language": "terraform",
        "content": "resource \"aws_s3_bucket\" \"x\" { bucket = \"test\" }",
        "context": {"app_name": "demo", "environment": "dev"},
    }
    s = json.dumps(payload)
    assert "content" in s and "demo" in s
