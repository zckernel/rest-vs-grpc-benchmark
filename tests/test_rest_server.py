import base64
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from servers.rest_server import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_process_checksum():
    data = b"hello world"
    r = client.post("/process", json={
        "payload_size": "small",
        "data": base64.b64encode(data).decode(),
        "client_timestamp": 0,
    })
    assert r.status_code == 200
    assert r.json()["checksum"] == hashlib.sha256(data).hexdigest()


def test_process_echoes_data():
    data = b"echo me"
    r = client.post("/process", json={
        "payload_size": "medium",
        "data": base64.b64encode(data).decode(),
        "client_timestamp": 0,
    })
    assert base64.b64decode(r.json()["data"]) == data


def test_process_payload_size_field():
    r = client.post("/process", json={
        "payload_size": "large",
        "data": base64.b64encode(b"x").decode(),
        "client_timestamp": 0,
    })
    assert r.json()["payload_size"] == "large"
