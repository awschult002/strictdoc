import socket

from tests.bundle.conftest import free_port


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
