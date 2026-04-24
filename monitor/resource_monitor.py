import threading
import time
from dataclasses import dataclass
from typing import Optional
import psutil


@dataclass
class ResourceSnapshot:
    timestamp: float
    cpu_percent: float
    rss_mb: float


class ResourceMonitor:
    def __init__(self, pid: int, interval: float = 0.05):
        self.pid = pid
        self.interval = interval
        self.samples: list[ResourceSnapshot] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._collect, daemon=True)
        self._disk_before: Optional[object] = None
        self._disk_after: Optional[object] = None

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=self.interval * 3)

    def capture_disk_before(self):
        self._disk_before = psutil.disk_io_counters()

    def capture_disk_after(self):
        self._disk_after = psutil.disk_io_counters()

    def disk_io_delta(self) -> dict:
        if not self._disk_before or not self._disk_after:
            return {"read_bytes": 0, "write_bytes": 0}
        return {
            "read_bytes": self._disk_after.read_bytes - self._disk_before.read_bytes,
            "write_bytes": self._disk_after.write_bytes - self._disk_before.write_bytes,
        }

    def summary(self) -> dict:
        if not self.samples:
            return {"avg_cpu_percent": 0.0, "max_cpu_percent": 0.0,
                    "avg_rss_mb": 0.0, "max_rss_mb": 0.0, "sample_count": 0}
        cpus = [s.cpu_percent for s in self.samples]
        rams = [s.rss_mb for s in self.samples]
        return {
            "avg_cpu_percent": sum(cpus) / len(cpus),
            "max_cpu_percent": max(cpus),
            "avg_rss_mb": sum(rams) / len(rams),
            "max_rss_mb": max(rams),
            "sample_count": len(self.samples),
        }

    def _collect(self):
        try:
            proc = psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            return
        # Prime cpu_percent so the first measured delta reflects actual interval usage.
        try:
            proc.cpu_percent()
        except psutil.NoSuchProcess:
            return

        def _snap():
            cpu = proc.cpu_percent()
            rss = proc.memory_info().rss / 1024 / 1024
            self.samples.append(ResourceSnapshot(
                timestamp=time.monotonic(),
                cpu_percent=cpu,
                rss_mb=rss,
            ))

        try:
            _snap()  # immediate first sample so short runs still get data
        except psutil.NoSuchProcess:
            return
        while not self._stop.wait(self.interval):
            try:
                _snap()
            except psutil.NoSuchProcess:
                break
