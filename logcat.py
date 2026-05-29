import subprocess
import threading
import time
from PySide6.QtCore import QThread, Signal


class Logcat(QThread):
    log_received = Signal(str)

    BATCH_INTERVAL_S = 0.2   # seconds to accumulate before emitting

    def __init__(self, main_win, device: str, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        self.device = device
        self._stop_event = threading.Event()
        self._process: subprocess.Popen | None = None
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
        cmd = ["adb", "-s", self.device, "logcat", "-v", "time"]
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                shell=False,
                # bufsize=1 (line-buffered) is only valid in text mode;
                # in binary mode it raises RuntimeWarning. The reader
                # daemon thread calls readline() directly so default
                # block buffering is fine.
            )
        except FileNotFoundError:
            self.log_received.emit("[ERROR] adb not found in PATH.")
            return
        except OSError as exc:
            self.log_received.emit(f"[ERROR] Failed to start adb: {exc}")
            return

        batch: list[str] = []
        last_flush = time.monotonic()

        while not self._stop_event.is_set():
            # --- Non-blocking read with a short timeout ---
            # readline() on a Popen pipe blocks indefinitely, so we use
            # a daemon reader thread + queue to avoid hanging the QThread.
            raw_line = self._readline_timeout(timeout=1.0)

            if raw_line is None:
                # Timeout — no data yet; check stop flag and flush batch
                pass
            elif raw_line == b"":
                # EOF — process exited
                break
            else:
                line = raw_line.decode("utf-8", errors="replace").rstrip()
                if line:
                    batch.append(line)

            now = time.monotonic()
            if now - last_flush >= self.BATCH_INTERVAL_S and batch:
                self.log_received.emit("\n".join(batch))
                batch.clear()
                last_flush = now

        # Final flush
        if batch:
            self.log_received.emit("\n".join(batch))

        self._terminate_process()

    # ------------------------------------------------------------------
    # Non-blocking readline via background thread + queue
    # ------------------------------------------------------------------
    def _readline_timeout(self, timeout: float) -> bytes | None:
        """
        Read one line from stdout without blocking forever.
        Returns:
          bytes  — a line was read
          b""    — EOF (process ended)
          None   — timed out, no data yet
        """
        import queue

        # Lazily create the reader queue and daemon thread once
        if not hasattr(self, "_line_queue"):
            self._line_queue: queue.Queue[bytes] = queue.Queue()
            self._reader_thread = threading.Thread(
                target=self._reader_worker,
                args=(self._line_queue,),
                daemon=True,
            )
            self._reader_thread.start()

        try:
            return self._line_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _reader_worker(self, q):
        """
        Runs in a daemon thread. Blocks on readline() and pushes lines
        into the queue. Sends b"" sentinel on EOF so the main loop exits.
        """
        try:
            for raw_line in iter(self._process.stdout.readline, b""):
                q.put(raw_line)
                if self._stop_event.is_set():
                    break
        finally:
            q.put(b"")  # EOF sentinel

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _terminate_process(self):
        proc = self._process
        if proc is None:
            return
        self._process = None

        if proc.poll() is not None:
            return  # already dead

        try:
            proc.terminate()           # SIGTERM on Unix, TerminateProcess on Windows
        except OSError:
            pass

        # Give it a moment to exit cleanly
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                return
            time.sleep(0.05)

        # Force-kill if still alive
        try:
            proc.kill()
        except OSError:
            pass

        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass