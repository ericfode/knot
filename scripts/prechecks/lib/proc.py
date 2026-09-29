"""Run a tool with a hang guard that can actually stop it.

Every subprocess of the suite goes through `run`: the child starts in its own session, so a timeout or a cancel
flag (raised by the runner when a check overruns its budget) kills the whole process group, never just the
direct child. A check that has been declared unavailable therefore stops consuming the host, and a pool of queued
tool runs drains in a few polling intervals instead of finishing every queued run.
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading
import time

POLL_SECONDS = 0.1


class Cancelled(Exception):
    """Raised inside a check when the hang guard has given up on it."""


def kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except OSError:
            pass


def run(argv, *, cwd=None, env=None, input: bytes | None = None, timeout: float | None = None,
        cancel: threading.Event | None = None) -> tuple[int | None, bytes, bytes]:
    """(exit code, stdout, stderr). The code is None when the tool timed out, was cancelled, or could not start;
    stderr then says which (`timeout`, `cancelled`, or the OS error). The tool's whole process group is killed."""
    if cancel is not None and cancel.is_set():
        return None, b'', b'cancelled'
    try:
        proc = subprocess.Popen([str(a) for a in argv], cwd=str(cwd) if cwd else None, env=env,
                                stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    except OSError as error:
        return None, b'', str(error).encode()
    deadline = None if timeout is None else time.monotonic() + timeout
    pending = input
    while True:
        try:
            out, err = proc.communicate(pending, timeout=POLL_SECONDS)
            return proc.returncode, out, err
        except subprocess.TimeoutExpired:
            if cancel is not None and cancel.is_set():
                reason = b'cancelled'
            elif deadline is not None and time.monotonic() >= deadline:
                reason = b'timeout'
            else:
                continue
            kill_group(proc)
            try:
                proc.communicate(timeout=5)
            except (subprocess.TimeoutExpired, OSError, ValueError):
                pass
            return None, b'', reason
