import sys
from typing import Iterator

import pytest

from strictdoc.helpers import frozen


@pytest.fixture(name="launcher_state")
def fixture_launcher_state() -> Iterator[None]:
    is_launcher = frozen._FrozenExecutable.is_launcher
    yield
    frozen._FrozenExecutable.is_launcher = is_launcher


def test_strictdoc_command_runs_the_module_when_not_frozen(
    launcher_state: None,  # noqa: ARG001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delattr(sys, "frozen", raising=False)
    frozen.mark_launcher_executable()

    assert frozen.is_frozen() is False
    assert frozen.is_launcher_executable() is False
    assert frozen.get_strictdoc_command() == [
        sys.executable,
        "-m",
        "strictdoc.cli.main",
    ]


def test_strictdoc_command_runs_the_frozen_strictdoc_executable(
    launcher_state: None,  # noqa: ARG001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    frozen._FrozenExecutable.is_launcher = False

    assert frozen.is_launcher_executable() is False
    assert frozen.get_strictdoc_command() == [sys.executable]


def test_strictdoc_command_uses_the_internal_command_in_the_launcher(
    launcher_state: None,  # noqa: ARG001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    frozen._FrozenExecutable.is_launcher = False

    frozen.mark_launcher_executable()

    assert frozen.is_launcher_executable() is True
    assert frozen.get_strictdoc_command() == [
        sys.executable,
        frozen.FROZEN_STRICTDOC_COMMAND,
    ]
