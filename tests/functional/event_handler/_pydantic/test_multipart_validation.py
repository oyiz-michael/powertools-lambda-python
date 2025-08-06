"""
Test multipart/form-data validation functionality for File parameters.
"""

import base64
import json
from typing import Annotated

import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form


def make_request_event(method="GET", path="/", body="", headers=None, query_params=None):
    """Create a minimal API Gateway request event for testing."""
    return {
        "resource": path,
        "path": path,
        "httpMethod": method,
        "headers": headers or {},
        "multiValueHeaders": {},
        "queryStringParameters": query_params,
        "multiValueQueryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "path": f"/stage{path}",
            "accountId": "123456789012",
            "resourceId": "abcdef",
            "stage": "test",
            "requestId": "test-request-id",
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "apiKey": None,
                "sourceIp": "127.0.0.1",
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "Custom User Agent String",
                "user": None,
            },
            "resourcePath": path,
            "httpMethod": method,
            "apiId": "abcdefghij",
        },
        "body": body,
        "isBase64Encoded": False,
    }


def test_multipart_file_upload_validation():
    """Test successful multipart file upload validation."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File(description="File to upload")]):
        return {"file_size": len(file), "message": "File uploaded successfully"}

    # Create multipart request with file content
    file_content = b"test file content"
    encoded_content = base64.b64encode(file_content).decode("utf-8")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        "Content-Type: text/plain\r\n"
        "\r\n"
        f"{encoded_content}\r\n"
        f"--{boundary}--\r\n"
    )

    event = make_request_event(
        method="POST", path="/upload", body=body, headers={"content-type": f"multipart/form-data; boundary={boundary}"}
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200


def test_multipart_mixed_file_and_form_validation():
    """Test multipart request with both file and form fields."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_with_metadata(
        file: Annotated[bytes, File(description="File to upload")],
        title: Annotated[str, Form(description="File title")],
        category: Annotated[str, Form(description="File category")],
    ):
        return {"file_size": len(file), "title": title, "category": category}

    file_content = b"test file content"
    encoded_content = base64.b64encode(file_content).decode("utf-8")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        "Content-Type: text/plain\r\n"
        "\r\n"
        f"{encoded_content}\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="title"\r\n'
        "\r\n"
        "My Test File\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="category"\r\n'
        "\r\n"
        "documents\r\n"
        f"--{boundary}--\r\n"
    )

    event = make_request_event(
        method="POST", path="/upload", body=body, headers={"content-type": f"multipart/form-data; boundary={boundary}"}
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    import json

    response_body = json.loads(response["body"])
    assert response_body["title"] == "My Test File"
    assert response_body["category"] == "documents"
    assert response_body["file_size"] == len(file_content)


def test_multipart_missing_required_file_validation_error():
    """Test validation error when required file is missing."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File(description="Required file")]):
        return {"file_size": len(file)}


def test_multipart_file_size_constraint_validation():
    """Test file size constraint validation."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(
        file: Annotated[
            bytes,
            File(
                description="Small file only",
                max_length=10,  # Very small limit for testing
            ),
        ],
    ):
        return {"file_size": len(file)}


def test_multipart_optional_file_validation():
    """Test optional file parameter validation."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_optional(
        message: Annotated[str, Form(description="Required message")],
        file: Annotated[bytes | None, File(description="Optional file")] = None,
    ):
        return {"has_file": file is not None, "file_size": len(file) if file else 0, "message": message}


def test_multipart_boundary_parsing_edge_cases():
    """Test edge cases in boundary parsing."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"file_size": len(file)}


def test_invalid_multipart_format():
    """Test handling of invalid multipart format."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"file_size": len(file)}


def test_missing_content_type_boundary():
    """Test handling of multipart request without boundary."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"file_size": len(file)}

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    # Body with only form fields, no file
    body = f'--{boundary}\r\nContent-Disposition: form-data; name="other_field"\r\n\r\nsome value\r\n--{boundary}--\r\n'

    event = make_request_event(
        method="POST", path="/upload", body=body, headers={"content-type": f"multipart/form-data; boundary={boundary}"}
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 422


def test_multipart_file_size_constraint_validation():
    """Test file size constraint validation."""
    app = APIGatewayRestResolver()
    app.use([OpenAPIValidationMiddleware()])

    @app.post("/upload")
    def upload_file(
        file: Annotated[
            bytes,
            File(
                description="Small file only",
                max_length=10,  # Very small limit for testing
            ),
        ],
    ):
        return {"file_size": len(file)}

    # File content larger than allowed
    file_content = b"this content is definitely longer than 10 bytes"
    encoded_content = base64.b64encode(file_content).decode("utf-8")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="large.txt"\r\n'
        "Content-Type: text/plain\r\n"
        "\r\n"
        f"{encoded_content}\r\n"
        f"--{boundary}--\r\n"
    )

    event = make_request_event(
        method="POST", path="/upload", body=body, headers={"content-type": f"multipart/form-data; boundary={boundary}"}
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 422


def test_multipart_optional_file_validation():
    """Test optional file parameter validation."""
    app = APIGatewayRestResolver()
    app.use([OpenAPIValidationMiddleware()])

    @app.post("/upload")
    def upload_optional(
        message: Annotated[str, Form(description="Required message")],
        file: Annotated[bytes | None, File(description="Optional file")] = None,
    ):
        return {"has_file": file is not None, "file_size": len(file) if file else 0, "message": message}

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    # Body with only required form field, no file
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="message"\r\n'
        "\r\n"
        "Hello without file\r\n"
        f"--{boundary}--\r\n"
    )

    event = make_request_event(
        method="POST", path="/upload", body=body, headers={"content-type": f"multipart/form-data; boundary={boundary}"}
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    import json

    response_body = json.loads(response["body"])
    assert response_body["has_file"] is False
    assert response_body["message"] == "Hello without file"


def test_multipart_boundary_parsing_edge_cases():
    """Test edge cases in boundary parsing."""
    app = APIGatewayRestResolver()
    app.use([OpenAPIValidationMiddleware()])

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"file_size": len(file)}

    # Test with quotes around boundary
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    file_content = b"test"
    encoded_content = base64.b64encode(file_content).decode("utf-8")

    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        "Content-Type: text/plain\r\n"
        "\r\n"
        f"{encoded_content}\r\n"
        f"--{boundary}--\r\n"
    )

    # Test with quoted boundary in content-type
    event = make_request_event(
        method="POST",
        path="/upload",
        body=body,
        headers={"content-type": f'multipart/form-data; boundary="{boundary}"'},
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200


def test_invalid_multipart_format():
    """Test handling of invalid multipart format."""
    app = APIGatewayRestResolver()
    app.use([OpenAPIValidationMiddleware()])

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"file_size": len(file)}

    # Invalid multipart body (missing boundary markers)
    body = "invalid multipart content"

    event = make_request_event(
        method="POST", path="/upload", body=body, headers={"content-type": "multipart/form-data; boundary=test"}
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 422


def test_missing_content_type_boundary():
    """Test handling of multipart request without boundary."""
    app = APIGatewayRestResolver()
    app.use([OpenAPIValidationMiddleware()])

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"file_size": len(file)}

    body = '--boundary\r\nContent-Disposition: form-data; name="file"\r\n\r\ntest\r\n--boundary--'

    event = make_request_event(
        method="POST",
        path="/upload",
        body=body,
        headers={"content-type": "multipart/form-data"},  # Missing boundary
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 422
