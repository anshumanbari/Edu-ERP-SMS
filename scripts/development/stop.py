"""
Stop whatever process is listening on the dev server's port. Cross-platform
(Windows via netstat/taskkill, POSIX via lsof/kill) so this works the same
locally and inside a future Linux container.

Usage:
    python -m scripts.development.stop
    python -m scripts.development.stop --port 8080
"""
import argparse
import platform
import subprocess
import sys

from scripts._shared.common import fail, info, ok, warn


def _find_pids_windows(port: int) -> list[str]:
    result = subprocess.run(
        ["netstat", "-ano"], capture_output=True, text=True, check=False
    )
    pids = set()
    for line in result.stdout.splitlines():
        if f":{port}" in line and "LISTENING" in line:
            pids.add(line.split()[-1])
    return list(pids)


def _find_pids_posix(port: int) -> list[str]:
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=False
    )
    return [pid for pid in result.stdout.split() if pid]


def stop_port(port: int) -> int:
    is_windows = platform.system() == "Windows"
    pids = _find_pids_windows(port) if is_windows else _find_pids_posix(port)

    if not pids:
        info(f"No process is listening on port {port}.")
        return 0

    for pid in pids:
        # /T (Windows only) also kills child processes — required because
        # `uvicorn --reload` runs the actual server as a child of the
        # reloader process; killing only the parent leaves the child
        # orphaned and still listening on the port.
        kill_cmd = ["taskkill", "/F", "/T", "/PID", pid] if is_windows else ["kill", "-9", pid]
        result = subprocess.run(kill_cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            ok(f"Stopped process {pid} on port {port}.")
        else:
            fail(f"Could not stop process {pid} on port {port}: {result.stderr.strip()}")
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stop the process listening on the dev server's port.")
    parser.add_argument("--port", type=int, default=8000, help="Port to free (default: 8000).")
    args = parser.parse_args(argv)

    if platform.system() not in ("Windows",) and not _has_lsof():
        warn("`lsof` was not found - cannot locate the process by port on this system.")
        return 1

    return stop_port(args.port)


def _has_lsof() -> bool:
    return subprocess.run(["which", "lsof"], capture_output=True, check=False).returncode == 0


if __name__ == "__main__":
    sys.exit(main())
