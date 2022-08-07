"""Simple Github Webhook forwarder for securely receiving Github webhooks and passing them on to
a different webserver.

To start the server, in Azure App service use:
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
"""
import logging
import os
import sys

import requests
from fastapi import FastAPI, HTTPException, Request

import webhook_helpers

# logging configuration
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
rootLogger.addHandler(handler)
logger = logging.getLogger(__name__)

# Actual configuration

try:
    TARGET_URL = os.environ['TARGET_URL']
    WEBHOOK_TOKEN_SECRET = os.environ['WEBHOOK_TOKEN_SECRET']
except KeyError:
    # Test configuration values
    # can use any test target
    logger.error(
        "Environment configuration variables not found, using test value defaults.")
    TARGET_URL = "http://127.0.0.1:7000"
    # "https://e.g.jenkins.com/github-webhook/"
    WEBHOOK_TOKEN_SECRET = "hello"

app = FastAPI()


@app.get("/status")
async def root():
    """Aliveness check for the endpoint"""
    return {
        "status": "alive",
        "checksum": webhook_helpers.create_main_checksum()
    }


@app.post("/forward_webhook")
async def forward_webhook(request: Request):
    """Primary functionality to forward webhook to a given target address. Validates signature
    and sender IP before forwarding the payload."""

    # first check: sender IP
    sender_ip = request.client.host
    sender_x_ip = request.headers.get("x-client-ip")
    sender_is_github = webhook_helpers.validate_if_sender_is_github(
        sender_ip, sender_x_ip)

    if not sender_is_github:
        logger.warning("sender_ip: %s or x-ip %s is not a github IP",
                       sender_ip, sender_x_ip)
        raise HTTPException(403, "Invalid sender IP")
    else:
        logger.info("sender_ip/x_ip: %s/%s is valid!", sender_ip, sender_x_ip)

    # second check: webhook signature
    payload = await request.json()
    request_body = await request.body()

    payload_body_text = bytes.decode(request_body)
    payld_signature = request.headers.get('x-hub-signature-256')

    signature_validation = webhook_helpers.validate_payload_signature(
        payload_body_text,
        WEBHOOK_TOKEN_SECRET,
        payld_signature
    )
    if signature_validation:
        logger.info("Signature is valid, forwarding request...")
        requests.post(TARGET_URL, json=payload)
    else:
        raise HTTPException(403, "Invalid signature")
    return {"detail": "Webhook accepted"}


# testing endpoint
@app.post("/receive_webhook")
async def print_webhook(request: Request):
    """Testing endpoint to print the POST request value to console."""
    value = await request.json()
    logger.info("Webhook received, contents logged under debug")
    logger.debug(value)
    return {"detail": "Webhook received"}
