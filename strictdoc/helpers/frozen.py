"""
Helpers for running StrictDoc as a frozen (PyInstaller) binary.

A frozen binary has no Python interpreter that can run "python -m ..." and no
console scripts such as "html2pdf4doc" on PATH. StrictDoc re-invokes its own
executable instead, and main() routes the internal helper command below
before StrictDoc's own argument parsing.

The bundle has two executables: "strictdoc" (the command-line interface) and
"strictdoc_launcher" (the windowed desktop launcher). The launcher executable
runs the command-line interface of StrictDoc with the internal command
FROZEN_STRICTDOC_COMMAND, so that the launcher does not depend on the
location of the "strictdoc" executable.

@relation(SDOC-LLR-222, scope=file)
"""

import sys
from typing import List

# Internal command line marker. When a frozen StrictDoc binary is started as
# "strictdoc _html2pdf4doc <args>", it runs html2pdf4doc's CLI with <args>.
FROZEN_HTML2PDF4DOC_COMMAND = "_html2pdf4doc"

# Internal command line marker. When the frozen launcher executable is started
# as "strictdoc_launcher _strictdoc <args>", it runs "strictdoc <args>".
FROZEN_STRICTDOC_COMMAND = "_strictdoc"


class _FrozenExecutable:
    is_launcher: bool = False


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_html2pdf4doc_command() -> List[str]:
    if is_frozen():  # pragma: no cover
        return [sys.executable, FROZEN_HTML2PDF4DOC_COMMAND]
    return ["html2pdf4doc"]


def mark_launcher_executable() -> None:
    """
    Record that this process runs as the frozen launcher executable.
    """
    _FrozenExecutable.is_launcher = True


def is_launcher_executable() -> bool:
    return is_frozen() and _FrozenExecutable.is_launcher


def get_strictdoc_command() -> List[str]:
    if is_launcher_executable():  # pragma: no cover
        return [sys.executable, FROZEN_STRICTDOC_COMMAND]
    if is_frozen():  # pragma: no cover
        return [sys.executable]
    return [sys.executable or "python", "-m", "strictdoc.cli.main"]


def run_frozen_helper_command_if_requested() -> None:  # pragma: no cover
    if not is_frozen():
        return
    if len(sys.argv) < 2 or sys.argv[1] != FROZEN_HTML2PDF4DOC_COMMAND:
        return
    # Imported lazily: html2pdf4doc.main loads Selenium and replaces
    # sys.stdout at import time, which only the helper process should do.
    from html2pdf4doc.main import (  # noqa: PLC0415
        main as html2pdf4doc_main,
    )

    sys.argv = ["html2pdf4doc", *sys.argv[2:]]
    html2pdf4doc_main()
    sys.exit(0)
