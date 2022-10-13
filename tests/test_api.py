"""Test module for the webhook forwarder."""
import pytest
import webhook_helpers
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_main():
    """Test status message endpoint"""
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
    assert response.json()[
        "checksum"] == webhook_helpers.create_main_checksum()


test_webhook_input_combinations = [
    {  # invalid sender and signature - sender is checked first
        "sender_is_valid": False,
        "signature_is_valid": False,
        "response_code": 403,
        "response_result": "Invalid sender IP"
    },
    {  # invalid sender, valid signature - sender is checked first
        "sender_is_valid": False,
        "signature_is_valid": True,
        "response_code": 403,
        "response_result": "Invalid sender IP"
    },
    {  # valid sender, invalid signature
        "sender_is_valid": True,
        "signature_is_valid": False,
        "response_code": 403,
        "response_result": "Invalid signature"
    },
    {  # valid sender, valid signature
        "sender_is_valid": True,
        "signature_is_valid": True,
        "response_code": 200,
        "response_result": "Webhook accepted"
    }
]


@pytest.mark.parametrize("test_data", test_webhook_input_combinations)
def test_forward_webhook(test_data, mocker):
    """Test webhook forwarding endpoint with various inputs to ensure expected
    messages are communicated back from different types of issues."""

    mocker.patch(
        "webhook_helpers.validate_if_sender_is_github",
        return_value=test_data["sender_is_valid"])

    mocker.patch(
        "webhook_helpers.validate_payload_signature",
        return_value=test_data["signature_is_valid"])

    mocker.patch(
        "requests.post",
        return_value=True)

    response = client.post(
        "/forward_webhook",
        json={}
    )
    assert response.status_code == test_data["response_code"]
    assert response.json()["detail"] == test_data["response_result"]


def test_print_webhook():
    """Test the debugging/receiving endpoint"""
    response = client.post(
        "/receive_webhook",
        json={'body': 'test'}
    )
    assert response.status_code == 200
