import os

PAYLOAD_SIZES = {
    "small": 100,
    "medium": 10_240,
    "large": 1_048_576,
}


def generate_payload(size: str) -> bytes:
    if size not in PAYLOAD_SIZES:
        raise ValueError(f"unknown payload size '{size}'; choose from {list(PAYLOAD_SIZES)}")
    return os.urandom(PAYLOAD_SIZES[size])
