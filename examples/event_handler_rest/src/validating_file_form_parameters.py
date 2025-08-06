"""
Example demonstrating File and Form parameter usage with AWS Lambda Powertools
"""

from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form

app = APIGatewayRestResolver(enable_validation=True)


@app.post("/contact", summary="Submit contact form")
def contact_form(
    name: Annotated[str, Form(description="Your full name")],
    email: Annotated[str, Form(description="Your email address")],
    message: Annotated[str, Form(description="Your message")],
):
    """Submit a contact form."""
    return {
        "success": True,
        "message": f"Thank you {name}! We'll respond to {email} soon.",
        "received_at": "2024-01-01T12:00:00Z",
    }


@app.post("/upload", summary="Upload a file")
def upload_file(
    file: Annotated[
        bytes,
        File(
            description="File to upload",
            max_length=10 * 1024 * 1024,  # 10MB limit
        ),
    ],
    title: Annotated[str, Form(description="File title")],
    category: Annotated[str, Form(description="File category", examples=["document", "image", "video"])],
):
    """Upload a file with metadata."""
    return {"success": True, "file_size": len(file), "title": title, "category": category, "upload_id": "file_12345"}


@app.post("/profile-picture", summary="Upload profile picture")
def upload_profile_picture(
    image: Annotated[
        bytes,
        File(
            description="Profile image (JPEG or PNG)",
            min_length=1024,  # Minimum 1KB
            max_length=5 * 1024 * 1024,  # Maximum 5MB
        ),
    ],
    name: Annotated[str, Form(description="Display name")],
    bio: Annotated[str | None, Form(description="Short bio")] = None,
):
    """Upload a profile picture with user info."""
    return {
        "success": True,
        "image_size": len(image),
        "name": name,
        "bio": bio or "No bio provided",
        "profile_id": "profile_67890",
    }


@app.get("/docs", summary="OpenAPI Documentation")
def get_docs():
    """Get the OpenAPI documentation showing File and Form parameter support."""
    return app.get_openapi_schema().model_dump()


# Lambda handler
def lambda_handler(event, context):
    return app.resolve(event, context)


if __name__ == "__main__":
    # Print the OpenAPI schema to see File and Form parameter documentation
    import json

    schema = app.get_openapi_schema()
    print(json.dumps(schema.model_dump(), indent=2))
