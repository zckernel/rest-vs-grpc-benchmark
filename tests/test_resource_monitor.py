import time
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.resource_monitor import ResourceMonitor, ResourceSnapshot


def _mock_proc(cpu_vals, rss_vals):
    proc = MagicMock()
    proc.cpu_percent.side_effect = cpu_vals
    proc.memory_info.side_effect = [MagicMock(rss=r) for r in rss_vals]
    return proc


def test_collects_samples():
    with patch("monitor.resource_monitor.psutil.Process") as MockProc:
        MockProc.return_value = _mock_proc(
            [10.0] * 20, [50 * 1024**2] * 20
        )
        m = ResourceMonitor(pid=1, interval=0.01)
        m.start()
        time.sleep(0.08)
        m.stop()
        assert len(m.samples) >= 2
        assert all(isinstance(s, ResourceSnapshot) for s in m.samples)


def test_immediate_sample_on_start():
    """Verifies at least one sample is captured even when benchmark ends immediately."""
    with patch("monitor.resource_monitor.psutil.Process") as MockProc:
        MockProc.return_value = _mock_proc(
            [0.0, 5.0] * 20, [30 * 1024**2] * 40
        )
        m = ResourceMonitor(pid=1, interval=10.0)  # interval longer than test duration
        m.start()
        m.stop()  # stop before the interval would fire
        assert len(m.samples) >= 1, "must capture at least one sample immediately on start"
        s = m.summary()
        assert s["sample_count"] >= 1


def test_summary_avg_max():
    with patch("monitor.resource_monitor.psutil.Process") as MockProc:
        MockProc.return_value = _mock_proc(
            [10.0, 20.0, 30.0] * 10, [100 * 1024**2, 200 * 1024**2, 150 * 1024**2] * 10
        )
        m = ResourceMonitor(pid=1, interval=0.01)
        m.start()
        time.sleep(0.08)
        m.stop()
        s = m.summary()
        assert s["max_cpu_percent"] >= s["avg_cpu_percent"] > 0
        assert s["max_rss_mb"] >= s["avg_rss_mb"] > 0


def test_disk_io_delta():
    with patch("monitor.resource_monitor.psutil.Process"):
        with patch("monitor.resource_monitor.psutil.disk_io_counters") as mock_disk:
            mock_disk.side_effect = [
                MagicMock(read_bytes=1000, write_bytes=2000),
                MagicMock(read_bytes=1500, write_bytes=2800),
            ]
            m = ResourceMonitor(pid=1, interval=100)
            m.capture_disk_before()
            m.capture_disk_after()
            d = m.disk_io_delta()
            assert d["read_bytes"] == 500
            assert d["write_bytes"] == 800


def test_summary_empty():
    with patch("monitor.resource_monitor.psutil.Process"):
        m = ResourceMonitor(pid=1, interval=100)
        s = m.summary()
        assert s == {"avg_cpu_percent": 0.0, "max_cpu_percent": 0.0,
                     "avg_rss_mb": 0.0, "max_rss_mb": 0.0, "sample_count": 0}


def test_summary_includes_sample_count():
    with patch("monitor.resource_monitor.psutil.Process") as MockProc:
        MockProc.return_value = _mock_proc(
            [10.0] * 20, [50 * 1024**2] * 20
        )
        m = ResourceMonitor(pid=1, interval=0.01)
        m.start()
        time.sleep(0.05)
        m.stop()
        s = m.summary()
        assert "sample_count" in s
        assert s["sample_count"] == len(m.samples)
