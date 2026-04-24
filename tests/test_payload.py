import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.payload import generate_payload, PAYLOAD_SIZES


def test_small_size():
    assert len(generate_payload("small")) == PAYLOAD_SIZES["small"]

def test_medium_size():
    assert len(generate_payload("medium")) == PAYLOAD_SIZES["medium"]

def test_large_size():
    assert len(generate_payload("large")) == PAYLOAD_SIZES["large"]

def test_returns_bytes():
    assert isinstance(generate_payload("small"), bytes)

def test_invalid_size_raises():
    with pytest.raises(ValueError, match="unknown payload size"):
        generate_payload("xlarge")

def test_random_output():
    assert generate_payload("small") != generate_payload("small")
