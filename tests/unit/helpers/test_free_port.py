import socket


def free_port():
    """
    Return an unused local TCP port StrictDoc's --port will accept.

    StrictDoc allows [1024, 65000]. Binding to port 0 lets the OS pick an
    ephemeral port, and on Windows those can be above 65000, which then fails
    argparse before the server starts.
    """
    for _ in range(100):
        sock = socket.socket()
        try:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        finally:
            sock.close()
        if 1024 <= port <= 65000:
            return port
    raise RuntimeError(
        "could not find a free TCP port in StrictDoc's allowed range "
        "[1024, 65000]"
    )


def test_free_port_stays_inside_strictdoc_cli_range():
    for _ in range(20):
        port = free_port()
        assert 1024 <= port <= 65000


def test_free_port_retries_when_os_gives_port_above_65000(monkeypatch):
    ports = iter([65001, 65535, 4242])

    class FakeSocket:
        def bind(self, _addr):
            return None

        def getsockname(self):
            return ("127.0.0.1", next(ports))

        def close(self):
            return None

    monkeypatch.setattr(socket, "socket", lambda *_a, **_k: FakeSocket())
    assert free_port() == 4242
