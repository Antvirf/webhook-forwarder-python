"""IP checker and SHA256 helper functions"""
import hashlib
import hmac
import ipaddress
import json
import logging

import requests
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def create_main_checksum():
    """MD5 checksum based on contents of main.py"""
    with open('main.py', 'r') as reader:
        content = reader.read()
    return hashlib.sha256(
        content.encode('utf-8')
    ).hexdigest()


def compute_sha256_hmac_digest(key, payload_body):
    """Returns HMAC hex digest using sha256, given a key (the token) and text to process (body)."""
    return hmac.new(
        bytes(key, 'utf-8'),
        payload_body.encode(),
        hashlib.sha256
    ).hexdigest()


def validate_payload_signature(request_body, token, payld_signature):
    """Given a payload body, a secret token, and the payload signature, validate the request."""
    local_signature = "sha256=" + \
        compute_sha256_hmac_digest(
            token, request_body)

    logger.info("payld_signature: %s", payld_signature)
    logger.info("local_signature: %s", local_signature)

    if payld_signature and local_signature:
        matched = hmac.compare_digest(payld_signature, local_signature)
        if matched:
            return True
    return False


def check_if_ip_in_cidr_range(test_ip, list_of_ip_ranges):
    """Given an IP and list of networks in CIDR notation, use the ipaddress library to check whether
    the given IP is within any of the given networks' range."""
    if test_ip is None:
        return False

    for ip_range in list_of_ip_ranges:
        if ipaddress.ip_address(test_ip) in ipaddress.ip_network(ip_range):
            return True
    return False


def validate_if_sender_is_github(sender_ip,
                                 sender_x_ip,
                                 allowed_list=None,
                                 meta_api_address="https://api.github.com/meta"):
    """Given a sender IP, queries GitHub meta API for webhook sender IPs and ensures sender is
    on that list."""

    # allow provision of a list of acceptable IPs to avoid needless queries
    if allowed_list:
        github_ips = allowed_list
    else:
        try:
            # fetch github webhook IPs from meta API
            github_ips = requests.get(
                meta_api_address).json()["hooks"]
        except requests.exceptions.ConnectionError as exception:
            raise HTTPException(
                500, "Error checking GitHub IPs") from exception

    return any([
        check_if_ip_in_cidr_range(sender_ip, github_ips),
        check_if_ip_in_cidr_range(sender_x_ip, github_ips)
    ])


def fetch_github_meta_api_result_to_file(url=r"https://api.github.com/meta"):
    """Save github meta api query to file"""
    r = requests.get(url)
    with open("meta_api_output.json", "w") as writer:
        json.dump(r.json(), writer, indent=4)


def read_local_github_meta_api_result(path="meta_api_output.json"):
    """Reads locally saved GitHub meta api data, returns list of accepted hook ids"""
    with open(path, "r") as reader:
        allowed_hook_ips = json.load(reader)["hooks"]
        return allowed_hook_ips


def clean_input_ip(ip):
    """Returns None if IP is unclean, otherwise returns the IP"""
    if ip is None:
        return None

    if str(ip).replace(".", "").isalnum():
        return ip
    return None
