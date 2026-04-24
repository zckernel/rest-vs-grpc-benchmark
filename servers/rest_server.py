import base64
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
from core.logic import process_payload

app = FastAPI()


class BenchmarkRequest(BaseModel):
    payload_size: str
    data: str          # base64-encoded bytes
    client_timestamp: int


class BenchmarkResponse(BaseModel):
    data: str          # base64-encoded bytes
    checksum: str
    server_timestamp: int
    payload_size: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process", response_model=BenchmarkResponse)
def process(req: BenchmarkRequest):
    raw = base64.b64decode(req.data)
    result = process_payload(req.payload_size, raw)
    return BenchmarkResponse(
        data=base64.b64encode(result["data"]).decode(),
        checksum=result["checksum"],
        server_timestamp=result["server_timestamp"],
        payload_size=result["payload_size"],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")
