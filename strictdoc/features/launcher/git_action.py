import os
import subprocess
import threading
from dataclasses import dataclass
from tkinter import messagebox, simpledialog
from typing import Any, List, Optional, Set

ACTION_INIT = "init"
ACTION_CLONE = "clone"
ACTION_PULL = "pull"
ACTION_PUSH = "push"


@dataclass(frozen=True)
class GitResult:
    ok: bool
    message: str


def _run_git(git_args: List[str], folder: str) -> GitResult:
    # The launcher has no terminal, so a password prompt would hang git
    # forever. Fail instead and show git's own error text.
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        completed = subprocess.run(
            ["git", *git_args],
            cwd=folder,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    except OSError as exc:
        return GitResult(ok=False, message=f"Could not run git: {exc}")
    output = (completed.stdout + completed.stderr).strip()
    return GitResult(ok=completed.returncode == 0, message=output)


def get_git_work_tree_root(folder: str) -> Optional[str]:
    result = _run_git(["rev-parse", "--show-toplevel"], folder)
    if not result.ok or not result.message:
        return None
    return result.message.splitlines()[-1]


def get_available_git_actions(folder: str) -> Set[str]:
    if get_git_work_tree_root(folder) is not None:
        return {ACTION_PULL, ACTION_PUSH}
    actions = {ACTION_INIT}
    if os.path.isdir(folder) and not os.listdir(folder):
        actions.add(ACTION_CLONE)
    return actions


def git_init(folder: str) -> GitResult:
    return _run_git(["init"], folder)


def git_clone(url: str, folder: str) -> GitResult:
    if not os.path.isdir(folder):
        return GitResult(ok=False, message=f"Folder does not exist: {folder}")
    if os.listdir(folder):
        return GitResult(
            ok=False,
            message=f"Git clone needs an empty folder. Not empty: {folder}",
        )
    return _run_git(["clone", "--", url, "."], folder)


def _ensure_git_workspace(self: Any) -> bool:
    if not self._ensure_workspace():
        return False

    assert self.workspace_dir is not None
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        messagebox.showerror("Git error", str(exc))
        return False

    if completed.returncode != 0 or completed.stdout.strip().lower() != "true":
        messagebox.showerror(
            "Git repository missing",
            "The selected workspace is not a Git repository.",
        )
        return False

    return True


def _run_git_action(
    self: Any,
    action_name: str,
    git_args: list[str],
) -> None:
    """Run a Git command in the current workspace in the background."""

    if not _ensure_git_workspace(self):
        return

    assert self.workspace_dir is not None
    workspace_dir = self.workspace_dir
    git_command_text = "git " + " ".join(git_args)
    self.set_status(f"{action_name}...")
    self._append_log(f"[{action_name.upper()}] {git_command_text}\n")

    def run_git_action() -> None:
        try:
            completed = subprocess.run(
                ["git", *git_args],
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            error = exc

            def _handle_exc(error: Exception = error) -> None:
                self.set_status(f"{action_name} failed.")
                self._append_log(f"[{action_name.upper()} ERROR] {error}\n")
                messagebox.showerror(f"{action_name} error", str(error))

            self.after(0, _handle_exc)
            return

        def _handle_result() -> None:
            if completed.returncode == 0:
                self.set_status(f"{action_name} completed.")
                self._append_log(
                    f"[{action_name.upper()} OK] {git_command_text}\n"
                )
                if completed.stdout:
                    self._append_log(
                        f"[{action_name.upper()} STDOUT]\n"
                        + completed.stdout
                        + "\n"
                    )
                if completed.stderr:
                    self._append_log(
                        f"[{action_name.upper()} STDERR]\n"
                        + completed.stderr
                        + "\n"
                    )
                messagebox.showinfo(
                    action_name,
                    f"{action_name} completed successfully.",
                )
            elif "commit " in git_args:
                self.set_status(f"{action_name} completed.")
                self._append_log(
                    f"[{action_name.upper()}] Update from StrictDoc Launcher\n"
                )
                if completed.stdout:
                    self._append_log(
                        f"[{action_name.upper()} STDOUT]\n"
                        + completed.stdout
                        + "\n"
                    )
                if completed.stderr:
                    self._append_log(
                        f"[{action_name.upper()} STDERR]\n"
                        + completed.stderr
                        + "\n"
                    )
            else:
                self.set_status(f"{action_name} failed.")
                self._append_log(
                    f"[{action_name.upper()} FAILED] rc="
                    f"{completed.returncode}\n"
                )
                if completed.stdout:
                    self._append_log(
                        f"[{action_name.upper()} STDOUT]\n"
                        + completed.stdout
                        + "\n"
                    )
                if completed.stderr:
                    self._append_log(
                        f"[{action_name.upper()} STDERR]\n"
                        + completed.stderr
                        + "\n"
                    )
                messagebox.showerror(
                    f"{action_name} failed",
                    "Return code: "
                    f"{completed.returncode}\n\nSTDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}",
                )

        self.after(0, _handle_result)

    threading.Thread(target=run_git_action, daemon=True).start()


def _git_pull(self: Any) -> None:
    _run_git_action(self, "Git pull", ["pull"])


def _git_commit(self: Any) -> None:
    commit_message = simpledialog.askstring(
        "Git Commit",
        "Enter the commit message:",
        parent=self,
        initialvalue="Update from StrictDoc Launcher",
    )
    if commit_message is None:
        return

    commit_message = commit_message.strip()
    if not commit_message:
        messagebox.showwarning("Git Commit", "Commit message cannot be empty.")
        return

    _run_git_action(
        self,
        "Git commit",
        ["commit", "-a", "-m", commit_message],
    )


def _git_push(self: Any) -> None:
    _run_git_action(self, "Git push", ["push"])


def _report(self: Any, action_name: str, result: GitResult) -> None:
    status = "completed" if result.ok else "failed"
    self.set_status(f"{action_name} {status}.")
    self._append_log(f"[{action_name.upper()}] {status}\n{result.message}\n")
    if result.ok:
        messagebox.showinfo(action_name, f"{action_name} completed.")
    else:
        messagebox.showerror(f"{action_name} failed", result.message)


def _git_init(self: Any) -> None:
    if not self._ensure_workspace():
        return
    _report(self, "Git init", git_init(self.workspace_dir))


def _git_clone(self: Any) -> None:
    if not self._ensure_workspace():
        return
    url = simpledialog.askstring(
        "Git Clone", "Repository URL to clone into this folder:", parent=self
    )
    if url is None or not url.strip():
        return
    workspace_dir = self.workspace_dir
    self.set_status("Git clone...")

    def run_clone() -> None:
        result = git_clone(url.strip(), workspace_dir)
        self.after(0, lambda: _report(self, "Git clone", result))

    threading.Thread(target=run_clone, daemon=True).start()
