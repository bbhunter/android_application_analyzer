import subprocess
import threading
from PySide6.QtCore import QThread, Signal


class Logcat(QThread):

    # Emit accumulated log text to the main thread
    log_received = Signal(str)

    # How many milliseconds to accumulate lines before emitting to the UI.
    # Lower = more responsive; higher = fewer repaints on noisy streams.
    BATCH_INTERVAL_MS = 200

    def __init__(self, main_win, device: str, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        self.device = device
        self._stop_event = threading.Event()
        self._process: subprocess.Popen | None = None

        # Connect signal to slot once; keeps the run() loop clean
        self.log_received.connect(self.main_win.txtLogcat.append)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def stop(self):
        """Request a clean shutdown. Safe to call from any thread."""
        self._stop_event.set()
        self._terminate_process()

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self):
        cmd = ["adb", "-s", self.device, "logcat"]

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # suppress adb startup noise
                shell=False,               # safer: no shell injection
            )
        except FileNotFoundError:
            self.log_received.emit("[ERROR] adb not found in PATH.")
            return
        except OSError as exc:
            self.log_received.emit(f"[ERROR] Failed to start adb: {exc}")
            return

        batch: list[str] = []
        last_flush = self.msecsSinceEpoch()

        try:
            for raw_line in self._process.stdout:
                if self._stop_event.is_set():
                    break

                line = raw_line.decode("utf-8", errors="replace").rstrip()
                if line:
                    batch.append(line)

                now = self.msecsSinceEpoch()
                if now - last_flush >= self.BATCH_INTERVAL_MS and batch:
                    self.log_received.emit("\n".join(batch))
                    batch.clear()
                    last_flush = now

        finally:
            # Flush any remaining lines
            if batch:
                self.log_received.emit("\n".join(batch))

            self._terminate_process()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def msecsSinceEpoch() -> int:
        """Millisecond timestamp; avoids importing time at module level."""
        import time
        return int(time.monotonic() * 1000)

    def _terminate_process(self):
        proc = self._process
        if proc is None:
            return
        if proc.poll() is None:          # still running?
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()              # forceful fallback
        self._process = None