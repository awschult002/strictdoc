"""
Run "strictdoc launcher --no-window ..." and check the server it starts.

Usage:
    launcher_probe.py [--occupy-port PORT] -- <launcher command ...>

The probe starts the launcher command and waits until the launcher prints
the server URL. It then fetches the start page, stops the launcher like a
user or the operating system would, and checks that the server port is
free again. Every step prints one line for FileCheck.
"""

import argparse
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from typing import Any, Dict, List, Optional

READY_REGEX = re.compile(r"StrictDoc server is ready: (http://([^:/]+):(\d+)/)")

# Launcher output lines that the probe passes on to FileCheck. The server
# log lines are not passed on because their order is not stable.
LAUNCHER_LINE_REGEX = re.compile(
    r"^(Created a new project|StrictDoc server|error)"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--occupy-port", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command: List[str] = args.command
    if len(command) > 0 and command[0] == "--":
        command = command[1:]
    assert len(command) > 0, "launcher_probe: expect a launcher command."

    occupied_socket: Optional[socket.socket] = None
    if args.occupy_port is not None:
        occupied_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupied_socket.bind(("127.0.0.1", args.occupy_port))
        occupied_socket.listen(1)
        _report(f"PROBE: occupied port {args.occupy_port}")

    popen_options: Dict[str, Any] = {}
    if sys.platform == "win32":
        popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        **popen_options,
    )
    output_lines: List[str] = []
    ready_event = threading.Event()
    ready_match: List[re.Match[str]] = []

    def _read_output() -> None:
        assert process.stdout is not None
        for line_ in process.stdout:
            output_lines.append(line_)
            if LAUNCHER_LINE_REGEX.match(line_) is not None:
                _report(f"LAUNCHER: {line_.rstrip()}")
            match = READY_REGEX.search(line_)
            if match is not None and not ready_event.is_set():
                ready_match.append(match)
                ready_event.set()

    reader = threading.Thread(target=_read_output, daemon=True)
    reader.start()

    port: Optional[int] = None
    try:
        if not ready_event.wait(args.timeout) or len(ready_match) == 0:
            _report("PROBE: the launcher did not report a ready server")
            _report("".join(output_lines))
            sys.exit(1)
        url, host, port_string = ready_match[0].groups()
        port = int(port_string)
        _report(f"PROBE: server ready on {host}")
        if args.occupy_port is not None:
            relation = "a different" if port != args.occupy_port else "the"
            _report(f"PROBE: server uses {relation} port")

        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url, timeout=60) as response:
            page = response.read().decode("utf-8", errors="replace")
        _report(f"PROBE: GET / returned {response.status}")
        if "Requirements" in page:
            _report("PROBE: start page lists the requirements")
    finally:
        _stop_launcher(process, reader)
        if occupied_socket is not None:
            occupied_socket.close()

    if port is not None:
        is_free = _wait_until_port_is_free(port)
        _report(
            "PROBE: server port is " + ("free" if is_free else "still in use")
        )


def _stop_launcher(
    process: "subprocess.Popen[str]", reader: threading.Thread
) -> None:
    if process.poll() is not None:
        reader.join(timeout=10)
        return
    if sys.platform == "win32":
        # TerminateProcess: the launcher cannot clean up, so Windows must
        # end the server through the launcher's job object.
        process.terminate()
    else:
        process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=30)
    # Print the remaining launcher output before the probe's own line.
    reader.join(timeout=10)
    _report("PROBE: launcher stopped")


def _wait_until_port_is_free(port: int, timeout_seconds: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
            if sys.platform != "win32":
                test_socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
                )
            try:
                test_socket.bind(("127.0.0.1", port))
                return True
            except OSError:
                pass
        time.sleep(0.2)
    return False


def _report(text: str) -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
