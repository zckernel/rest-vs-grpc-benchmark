import hashlib
import time


def process_payload(payload_size: str, data: bytes) -> dict:
    return {
        "data": data,
        "checksum": hashlib.sha256(data).hexdigest(),
        "server_timestamp": int(time.time() * 1_000_000),
        "payload_size": payload_size,
    }
