"""Run the real program in a pseudo-terminal."""

import os
import pty
import select
import signal
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="needs a pty")


def run_in_pty(args, send_sigint_after=None, timeout=15.0, keys_after=None):
    pid, fd = pty.fork()
    if pid == 0:
        os.environ.update(TERM="xterm-256color", LANG="C.UTF-8", LC_ALL="C.UTF-8",
                          LINES="24", COLUMNS="80")
        os.execv(sys.executable, [sys.executable, str(ROOT / "matrix"), *args])
    out = b""
    start = time.monotonic()
    sent = False
    keys_sent = 0.0
    while time.monotonic() - start < timeout:
        if send_sigint_after is not None and not sent and \
                time.monotonic() - start > send_sigint_after:
            os.kill(pid, signal.SIGINT)
            sent = True
        # Keep pressing the key every 0.5 s once the delay has passed
        # (keys pressed while the message is still being typed are ignored).
        if keys_after is not None and time.monotonic() - start > keys_after[0] \
                and time.monotonic() - keys_sent > 0.5:
            try:
                os.write(fd, keys_after[1])
            except OSError:
                pass
            keys_sent = time.monotonic()
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                chunk = os.read(fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            out += chunk
    done, status = os.waitpid(pid, os.WNOHANG)
    if not done:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        pytest.fail(f"matrix did not exit in {timeout}s")
    os.close(fd)
    return os.waitstatus_to_exitcode(status), out, time.monotonic() - start


def test_runs_and_exits_by_itself():
    code, out, took = run_in_pty(["-d", "0.5", "-s", "4"])
    assert code == 0
    assert "ｱ".encode() in out or any(chr(c).encode() in out for c in range(0xFF66, 0xFF9E))
    assert took >= 0.5


def test_ignores_ctrl_c_like_sl():
    code, out, took = run_in_pty(["-d", "1.5", "-s", "4"], send_sigint_after=0.5)
    assert code == 0
    assert took >= 1.5  # it kept going


def test_cancellable_stops_on_ctrl_c():
    code, out, took = run_in_pty(["-c", "-d", "30"], send_sigint_after=0.5)
    assert code == 0
    assert took < 10


def test_message_is_typed_and_stays_until_a_key():
    args = ["-a", "-d", "0.2", "-s", "4", "-m", "HELLO"]
    code, out, took = run_in_pty(args, keys_after=(4.0, b"x"))
    assert code == 0
    for ch in "HELLO":
        assert ch.encode() in out
    assert took >= 4.0  # waited for the key


def test_message_waits_without_a_key():
    pid_timeout = 3.0
    with pytest.raises(pytest.fail.Exception, match="did not exit"):
        run_in_pty(["-a", "-d", "0.2", "-s", "4", "-m", "HI"], timeout=pid_timeout)
