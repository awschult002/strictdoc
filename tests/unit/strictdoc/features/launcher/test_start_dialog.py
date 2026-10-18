"""
Tests for the launcher dialogs. They need Tk and a display.

@relation(SDOC-LLR-220, scope=file)
"""

import gc
import os
import sys
from pathlib import Path
from typing import Any, Iterator, List

import pytest

from strictdoc.commands.launcher_command import is_launcher_available

if not is_launcher_available():
    pytest.skip("tkinter is not available", allow_module_level=True)
if sys.platform.startswith("linux") and len(os.environ.get("DISPLAY", "")) == 0:
    pytest.skip("no display (DISPLAY is not set)", allow_module_level=True)

import tkinter as tk  # noqa: E402

from strictdoc.features.launcher import start_dialog  # noqa: E402
from strictdoc.features.launcher.start_dialog import (  # noqa: E402
    NewProjectDialog,
    StartDialog,
)


@pytest.fixture(autouse=True)
def collect_tk_garbage() -> Iterator[None]:
    """
    Collect the Tk objects of a test in the main thread.

    Tk variables and images call Tcl when Python deletes them. If the garbage
    collector deletes them later in a background thread of another test, Tcl
    crashes the process.
    """
    yield
    gc.collect()


@pytest.fixture
def root() -> Iterator[tk.Tk]:
    try:
        tk_root = tk.Tk()
    except tk.TclError as tcl_error:
        pytest.skip(f"Tk cannot open a window: {tcl_error}")
    tk_root.withdraw()
    yield tk_root
    tk_root.destroy()


@pytest.fixture
def messages(monkeypatch: pytest.MonkeyPatch) -> List[str]:
    """Record message boxes instead of showing them."""
    recorded_messages: List[str] = []

    def _record(title: str, message: str, **_kwargs: Any) -> bool:
        recorded_messages.append(f"{title}: {message}")
        return False

    for function_name_ in ("showerror", "showinfo", "askyesno"):
        monkeypatch.setattr(start_dialog.messagebox, function_name_, _record)
    return recorded_messages


def test_start_dialog_opens_a_recent_project(
    root: tk.Tk, tmp_path: Path, messages: List[str]
) -> None:
    (tmp_path / "strictdoc_config.py").write_text("", encoding="utf-8")
    opened_projects: List[str] = []
    dismissed: List[bool] = []

    dialog = StartDialog(
        root,
        recent_projects=[str(tmp_path)],
        on_open_project=opened_projects.append,
        on_dismiss=lambda: dismissed.append(True),
    )
    assert dialog.recent_projects_listbox.get(0) == str(tmp_path)
    dialog.open_recent_button.invoke()

    assert opened_projects == [str(tmp_path)]
    assert dismissed == []
    assert messages == []


def test_start_dialog_without_recent_projects(root: tk.Tk) -> None:
    dismissed: List[bool] = []

    dialog = StartDialog(
        root,
        recent_projects=[],
        on_open_project=lambda _path: None,
        on_dismiss=lambda: dismissed.append(True),
    )
    assert str(dialog.open_recent_button.cget("state")) == "disabled"
    dialog.dismiss()

    assert dismissed == [True]


def test_start_dialog_reports_a_missing_recent_project(
    root: tk.Tk, tmp_path: Path, messages: List[str]
) -> None:
    opened_projects: List[str] = []
    dialog = StartDialog(
        root,
        recent_projects=[str(tmp_path / "deleted")],
        on_open_project=opened_projects.append,
        on_dismiss=lambda: None,
    )

    dialog.open_selected_project()

    assert opened_projects == []
    assert len(messages) == 1
    assert "does not exist anymore" in messages[0]
    dialog.destroy()


def test_start_dialog_asks_before_opening_a_folder_without_documents(
    root: tk.Tk, tmp_path: Path, messages: List[str]
) -> None:
    opened_projects: List[str] = []
    dialog = StartDialog(
        root,
        recent_projects=[],
        on_open_project=opened_projects.append,
        on_dismiss=lambda: None,
    )

    # The recorded askyesno answers "No".
    dialog.open_project(str(tmp_path))

    assert opened_projects == []
    assert "Open it anyway?" in messages[0]
    dialog.destroy()


def test_new_project_dialog_creates_a_project(
    root: tk.Tk, tmp_path: Path, messages: List[str]
) -> None:
    created_projects: List[str] = []
    dialog = NewProjectDialog(
        root,
        initial_parent_path=str(tmp_path),
        on_project_created=created_projects.append,
    )
    dialog.template_var.set("empty")
    dialog.project_name_var.set("My project")

    dialog.create_button.invoke()

    project_path = tmp_path / "My project"
    assert messages == []
    assert created_projects == [str(project_path)]
    assert (project_path / "docs" / "requirements.sdoc").is_file()
    assert (project_path / "strictdoc_config.py").is_file()


def test_new_project_dialog_rejects_an_invalid_name(
    root: tk.Tk, tmp_path: Path, messages: List[str]
) -> None:
    created_projects: List[str] = []
    dialog = NewProjectDialog(
        root,
        initial_parent_path=str(tmp_path),
        on_project_created=created_projects.append,
    )
    dialog.project_name_var.set("")

    assert dialog.create_project() is None

    assert created_projects == []
    assert messages == ["New project: Enter a project name."]
    dialog.destroy()
