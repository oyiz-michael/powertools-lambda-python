"""Test WebKit boundary handling in multipart form data parsing."""

import base64
from typing import Annotated

import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File


def test_webkit_boundary_parsing():
    """Test that WebKit form boundaries are correctly parsed in multipart data."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File(description="File to upload")]):
        return {"file_size": len(file), "success": True}

    # Simulate a WebKit multipart form data request
    webkit_boundary = "WebKitFormBoundary7MA4YWxkTrZu0gW"
    test_content = b"test file content"

    multipart_body = (
        (
            f"--{webkit_boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            f"Content-Type: text/plain\r\n"
            f"\r\n"
        ).encode("utf-8")
        + test_content
        + f"\r\n--{webkit_boundary}--\r\n".encode("utf-8")
    )

    # Test standard WebKit boundary format
    event = {
        "resource": "/upload",
        "path": "/upload",
        "httpMethod": "POST",
        "headers": {"content-type": f"multipart/form-data; boundary={webkit_boundary}"},
        "multiValueHeaders": {},
        "queryStringParameters": None,
        "multiValueQueryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "path": "/stage/upload",
            "accountId": "123456789012",
            "resourceId": "abcdef",
            "stage": "stage",
            "requestId": "test-request-id",
            "identity": {
                "sourceIp": "127.0.0.1",
                "userAgent": "Test-Agent",
            },
            "httpMethod": "POST",
            "apiId": "test-api-id",
        },
        "body": base64.b64encode(multipart_body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    # Process the event
    response = app(event, {})
    assert response["statusCode"] == 200

    import json

    response_body = json.loads(response["body"])
    assert response_body["success"] is True
    assert response_body["file_size"] == len(test_content)


def test_webkit_boundary_with_prefix():
    """Test WebKit boundaries with prefixes like ----WebKitFormBoundary."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File(description="File to upload")]):
        return {"file_size": len(file), "success": True}

    # Simulate a WebKit boundary with prefix (common in older browsers)
    webkit_boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    test_content = b"test file content with prefix"

    multipart_body = (
        (
            f"--{webkit_boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            f"Content-Type: text/plain\r\n"
            f"\r\n"
        ).encode("utf-8")
        + test_content
        + f"\r\n--{webkit_boundary}--\r\n".encode("utf-8")
    )

    event = {
        "resource": "/upload",
        "path": "/upload",
        "httpMethod": "POST",
        "headers": {"content-type": f"multipart/form-data; boundary={webkit_boundary}"},
        "multiValueHeaders": {},
        "queryStringParameters": None,
        "multiValueQueryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "path": "/stage/upload",
            "accountId": "123456789012",
            "resourceId": "abcdef",
            "stage": "stage",
            "requestId": "test-request-id",
            "identity": {
                "sourceIp": "127.0.0.1",
                "userAgent": "Test-Agent",
            },
            "httpMethod": "POST",
            "apiId": "test-api-id",
        },
        "body": base64.b64encode(multipart_body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    # Process the event
    response = app(event, {})
    assert response["statusCode"] == 200

    import json

    response_body = json.loads(response["body"])
    assert response_body["success"] is True
    assert response_body["file_size"] == len(test_content)


def test_webkit_boundary_in_content_type_without_boundary_param():
    """Test when WebKit boundary appears in content-type but not as boundary= parameter."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File(description="File to upload")]):
        return {"file_size": len(file), "success": True}

    # Simulate a malformed content-type that contains WebKit boundary but no boundary= param
    webkit_boundary = "WebKitFormBoundary7MA4YWxkTrZu0gW"
    test_content = b"test content no boundary param"

    multipart_body = (
        (
            f"--{webkit_boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            f"Content-Type: text/plain\r\n"
            f"\r\n"
        ).encode("utf-8")
        + test_content
        + f"\r\n--{webkit_boundary}--\r\n".encode("utf-8")
    )

    event = {
        "resource": "/upload",
        "path": "/upload",
        "httpMethod": "POST",
        "headers": {
            # Content-type with WebKit boundary but no boundary= parameter
            "content-type": f"multipart/form-data; {webkit_boundary}"
        },
        "multiValueHeaders": {},
        "queryStringParameters": None,
        "multiValueQueryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "path": "/stage/upload",
            "accountId": "123456789012",
            "resourceId": "abcdef",
            "stage": "stage",
            "requestId": "test-request-id",
            "identity": {
                "sourceIp": "127.0.0.1",
                "userAgent": "Test-Agent",
            },
            "httpMethod": "POST",
            "apiId": "test-api-id",
        },
        "body": base64.b64encode(multipart_body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    # Process the event
    response = app(event, {})
    assert response["statusCode"] == 200

    import json

    response_body = json.loads(response["body"])
    assert response_body["success"] is True
    assert response_body["file_size"] == len(test_content)
