"""Test module for helper functions for request validation."""
import hashlib
from unittest.mock import patch

import fastapi
import pytest
import requests
from webhook_helpers import (check_if_ip_in_cidr_range,
                             compute_sha256_hmac_digest, create_main_checksum,
                             validate_if_sender_is_github,
                             validate_payload_signature)

TEST_KEY = "key"
TEST_BODY = "lorem ipsum"
SIGNATURE_EXPECTED_OUTPUT = '5c79c03ad01749b1f7056b1d2ac008a5c5a52fc456565b71674267a3c8f3d8c3'
TEST_NON_GITHUB_IP = "14.197.102.222"
TEST_GITHUB_IP = "192.30.252.0"
TEST_GITHUB_IP_RANGE = "192.30.252.0/22"


def test_create_main_checksum():
    """Test that the main checksum behaves as expected."""
    with open('main.py', 'r') as reader:
        content = reader.read()
    assert hashlib.md5(content.encode('utf-8')
                       ).hexdigest() == create_main_checksum()


def test_compute_sha256_hmac_digest():
    """Test sha256 hmac digest against a pre-computed value set"""

    assert compute_sha256_hmac_digest(
        TEST_KEY,
        TEST_BODY
    ) == SIGNATURE_EXPECTED_OUTPUT


def test_validate_payload_signature_valid():
    """Test that signature validation succeeds when all details are correct"""
    assert validate_payload_signature(
        TEST_BODY,
        TEST_KEY,
        "sha256="+SIGNATURE_EXPECTED_OUTPUT
    ) is True


def test_validate_payload_signature_invalid_incorrect_key():
    """Test that signature validation fails if the key is wrong"""
    assert validate_payload_signature(
        TEST_BODY,
        "incorrect key!",
        "sha256="+SIGNATURE_EXPECTED_OUTPUT
    ) is False


def test_validate_payload_signature_invalid_incorrect_body():
    """Test that signature validation fails if the body is wrong"""
    assert validate_payload_signature(
        "incorrect body!",
        TEST_KEY,
        "sha256="+SIGNATURE_EXPECTED_OUTPUT
    ) is False


def test_validate_payload_signature_invalid_incorrect_signature():
    """Test that signature validation fails if signature is wrong"""
    assert validate_payload_signature(
        TEST_BODY,
        TEST_KEY,
        "sha256="+SIGNATURE_EXPECTED_OUTPUT+"this is now wrong!"
    ) is False


def test_validate_if_sender_is_github_invalid():
    """Test that a known non-Github IP is identified as invalid"""
    assert validate_if_sender_is_github(
        TEST_NON_GITHUB_IP,
        TEST_NON_GITHUB_IP,
        [TEST_GITHUB_IP]) is False


def test_validate_if_sender_is_github_valid():
    """Test that a known Github IP is identified as invalid, by first fetching an IP from
    Github's meta api. Replacing the query with a static value to avoid rate limits."""
    github_hook_ip = TEST_GITHUB_IP

    # The commented out section below uses actual Github APIs to check the latest endpoints.
    # github_hook_ip = github_ips = requests.get(
    #     "https://api.github.com/meta").json()["hooks"][0]
    # if "/" in github_hook_ip:
    #     github_hook_ip = str(github_hook_ip).split("/", maxsplit=1)[0]

    # FIND A WAY TO MOCK THIS!
    assert validate_if_sender_is_github(
        TEST_NON_GITHUB_IP, github_hook_ip,
        [github_hook_ip]
    ) is True


def test_validate_if_sender_is_github_request_fail():
    """Test that a HTTP exception is raised if the API query doesn't work."""
    with pytest.raises(fastapi.HTTPException):
        validate_if_sender_is_github(
            TEST_NON_GITHUB_IP,
            TEST_NON_GITHUB_IP,
            [],
            "https://apifwafwa.githdwaifhaugheuaghoagea.com/meta")


ip_range_test_data = [
    {
        "ip": TEST_GITHUB_IP,
        "range": [TEST_GITHUB_IP_RANGE],
        "result": True
    },
    {
        "ip": TEST_NON_GITHUB_IP,
        "range": [TEST_GITHUB_IP_RANGE],
        "result": False
    }
]


@pytest.mark.parametrize("test_data", ip_range_test_data)
def test_if_ip_in_cidr_range(test_data):
    """Tests with known inputs that the ip-in-cidr-range checker works as expected."""
    assert check_if_ip_in_cidr_range(
        test_data["ip"],
        test_data["range"]
    ) is test_data["result"]


def test_check_if_ip_in_cidr_range_none():
    """Tests that False is returned with a None/missing input to the IP range checker."""
    assert check_if_ip_in_cidr_range(
        None,
        [None, None]
    ) is False


def test_error_raised_for_failed_api_query():
    """Checks that HTTPexception 500 is raised if query to Github API fails. Internally, this is
    a Requests exception, but we want to reraise it as fastaAPI HTTP exception."""

    with patch('requests.get', side_effect=requests.exceptions.ConnectionError):
        with pytest.raises(fastapi.HTTPException):
            validate_if_sender_is_github(None, None)
