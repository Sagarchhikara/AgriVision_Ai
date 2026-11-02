"""
tests/test_upload_limits.py

Server-side upload validation on POST /predict: each rejection reaches the
client with its own error code and status, so a frontend can say "too large"
or "wrong file type" without parsing the message.
"""

from __future__ import annotations

from tests.conftest import image_upload


def test_accepted_types_pass(make_api_client):
    client = make_api_client()

    for image_format, content_type in (("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")):
        response = client.post("/predict", files=image_upload(image_format, content_type))
        assert response.status_code == 200, content_type


def test_unsupported_content_type_is_415(make_api_client):
    response = make_api_client().post("/predict", files=image_upload(content_type="application/pdf"))

    assert response.status_code == 415
    assert response.json()["error"] == "unsupported_image_type"


def test_spoofed_content_type_is_caught_after_decoding(make_api_client):
    """A GIF declared as PNG decodes fine but is still not an accepted format."""
    response = make_api_client().post("/predict", files=image_upload("GIF", "image/png"))

    assert response.status_code == 415
    assert response.json()["error"] == "unsupported_image_type"


def test_oversized_upload_is_413(make_api_client):
    client = make_api_client(max_upload_bytes=1024)

    response = client.post("/predict", files=image_upload(data=b"\x00" * 2048))

    assert response.status_code == 413
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "image_too_large"


def test_upload_exactly_at_the_limit_is_not_rejected_for_size(make_api_client):
    upload = image_upload()
    size = len(upload["image"][1])
    client = make_api_client(max_upload_bytes=size)

    assert client.post("/predict", files=upload).status_code == 200


def test_corrupt_image_is_400(make_api_client):
    response = make_api_client().post("/predict", files=image_upload(data=b"not an image at all"))

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_image"


def test_empty_upload_is_400(make_api_client):
    response = make_api_client().post("/predict", files=image_upload(data=b""))

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_image"
