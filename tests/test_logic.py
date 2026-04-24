import hashlib
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logic import process_payload


def test_checksum():
    data = b"hello"
    r = process_payload("small", data)
    assert r["checksum"] == hashlib.sha256(data).hexdigest()

def test_data_echoed():
    data = b"test"
    assert process_payload("medium", data)["data"] == data

def test_payload_size_field():
    assert process_payload("large", b"x")["payload_size"] == "large"

def test_timestamp_positive():
    assert process_payload("small", b"t")["server_timestamp"] > 0

def test_deterministic_checksum():
    data = b"same"
    assert process_payload("small", data)["checksum"] == process_payload("small", data)["checksum"]
