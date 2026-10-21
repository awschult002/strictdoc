"""
Start dialog and new project dialog of the desktop launcher.

@relation(SDOC-LLR-220, scope=file)
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Union

from strictdoc.core.project_templates import (
    PROJECT_TEMPLATE_HELLO_WORLD,
    PROJECT_TEMPLATE_TITLES,
)
from strictdoc.features.launcher.launcher_session import (
    LauncherError,
    create_new_project,
    is_strictdoc_project,
    validate_new_project_location,
)

_PADDING: Dict[str, Any] = {"padx": 8, "pady": 6}


class StartDialog(tk.Toplevel):
    """
    The first window of the launcher: open a project or create a new one.

    The dialog calls on_open_project with the folder of the project that the
    user opened or created. If the user closes the dialog without choosing a
    project, the dialog calls on_dismiss.
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        recent_projects: List[str],
        on_open_project: Callable[[str], None],
        on_dismiss: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.title("StrictDoc")
        self.resizable(False, False)
        self._recent_projects: List[str] = list(recent_projects)
        self._on_open_project: Callable[[str], None] = on_open_project
        self._on_dismiss: Callable[[], None] = on_dismiss

        content = ttk.Frame(self)
        content.grid(row=0, column=0, sticky="nsew", **_PADDING)

        ttk.Label(
            content,
            text="Open a StrictDoc project or create a new one.",
            font="TkHeadingFont",
        ).grid(row=0, column=0, columnspan=2, sticky="w", **_PADDING)

        self.open_project_button = ttk.Button(
            content,
            text="Open project ...",
            command=self.choose_project_folder,
        )
        self.open_project_button.grid(row=1, column=0, sticky="we", **_PADDING)

        self.new_project_button = ttk.Button(
            content,
            text="New project ...",
            command=self.open_new_project_dialog,
        )
        self.new_project_button.grid(row=1, column=1, sticky="we", **_PADDING)

        recent_frame = ttk.LabelFrame(content, text="Recent projects")
        recent_frame.grid(
            row=2, column=0, columnspan=2, sticky="nsew", **_PADDING
        )
        self.recent_projects_listbox = tk.Listbox(
            recent_frame,
            height=max(1, min(len(self._recent_projects), 5)),
            width=60,
            activestyle="dotbox",
        )
        for recent_project_ in self._recent_projects:
            self.recent_projects_listbox.insert("end", recent_project_)
        self.recent_projects_listbox.grid(
            row=0, column=0, sticky="nsew", **_PADDING
        )
        self.recent_projects_listbox.bind(
            "<Double-Button-1>", lambda _event: self.open_selected_project()
        )
        self.recent_projects_listbox.bind(
            "<Return>", lambda _event: self.open_selected_project()
        )
        self.open_recent_button = ttk.Button(
            recent_frame,
            text="Open selected",
            command=self.open_selected_project,
        )
        self.open_recent_button.grid(row=1, column=0, sticky="e", **_PADDING)
        if len(self._recent_projects) == 0:
            self.recent_projects_listbox.insert("end", "No recent projects.")
            self.recent_projects_listbox.configure(state="disabled")
            self.open_recent_button.configure(state="disabled")
        else:
            self.recent_projects_listbox.selection_set(0)
            self.recent_projects_listbox.activate(0)

        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        recent_frame.columnconfigure(0, weight=1)

        self.protocol("WM_DELETE_WINDOW", self.dismiss)
        self.bind("<Escape>", lambda _event: self.dismiss())
        self._center_on_screen()
        self.lift()
        self.focus_force()

    def choose_project_folder(self) -> None:
        directory = filedialog.askdirectory(
            parent=self, title="Open StrictDoc project", mustexist=True
        )
        if directory is None or len(directory) == 0:
            return
        self.open_project(directory)

    def open_selected_project(self) -> None:
        listbox = self.recent_projects_listbox
        selection = listbox.curselection()  # type: ignore[no-untyped-call]
        if len(selection) == 0 or len(self._recent_projects) == 0:
            return
        project_path = self._recent_projects[selection[0]]
        if not os.path.isdir(project_path):
            messagebox.showerror(
                "Open project",
                f"The project folder does not exist anymore:\n{project_path}",
                parent=self,
            )
            return
        self.open_project(project_path)

    def open_project(self, project_path: str) -> None:
        # An empty folder opens without asking, so it can be filled with
        # Git > Git Clone.
        is_empty = len(os.listdir(project_path)) == 0
        if (
            not is_empty
            and not is_strictdoc_project(project_path)
            and not messagebox.askyesno(
                "Open project",
                "The folder has no StrictDoc config file and no SDoc "
                "documents:\n"
                f"{project_path}\n\nOpen it anyway?",
                parent=self,
            )
        ):
            return
        self._finish(project_path)

    def open_new_project_dialog(self) -> None:
        NewProjectDialog(
            self,
            initial_parent_path=os.path.expanduser("~"),
            on_project_created=self._finish,
        )

    def dismiss(self) -> None:
        self.destroy()
        self._on_dismiss()

    def _finish(self, project_path: str) -> None:
        self.destroy()
        self._on_open_project(project_path)

    def _center_on_screen(self) -> None:
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x_position = max(0, (self.winfo_screenwidth() - width) // 2)
        y_position = max(0, (self.winfo_screenheight() - height) // 3)
        self.geometry(f"+{x_position}+{y_position}")


class NewProjectDialog(tk.Toplevel):
    """
    Create a project from a starter template in a folder that the user picks.
    """

    def __init__(
        self,
        master: Union[tk.Tk, tk.Toplevel],
        *,
        initial_parent_path: str,
        on_project_created: Callable[[str], None],
    ) -> None:
        super().__init__(master)
        self.title("New StrictDoc project")
        self.resizable(False, False)
        if master.winfo_viewable():
            self.transient(master)
        self._on_project_created: Callable[[str], None] = on_project_created

        self.template_var = tk.StringVar(value=PROJECT_TEMPLATE_HELLO_WORLD)
        self.parent_path_var = tk.StringVar(value=initial_parent_path)
        self.project_name_var = tk.StringVar(value="")

        content = ttk.Frame(self)
        content.grid(row=0, column=0, sticky="nsew", **_PADDING)

        template_frame = ttk.LabelFrame(content, text="Template")
        template_frame.grid(
            row=0, column=0, columnspan=3, sticky="we", **_PADDING
        )
        for row_, (template_name_, template_title_) in enumerate(
            PROJECT_TEMPLATE_TITLES.items()
        ):
            ttk.Radiobutton(
                template_frame,
                text=template_title_,
                value=template_name_,
                variable=self.template_var,
            ).grid(row=row_, column=0, sticky="w", **_PADDING)

        ttk.Label(content, text="Create in folder:").grid(
            row=1, column=0, sticky="w", **_PADDING
        )
        ttk.Entry(content, textvariable=self.parent_path_var, width=45).grid(
            row=1, column=1, sticky="we", **_PADDING
        )
        ttk.Button(
            content, text="Browse ...", command=self.choose_parent_folder
        ).grid(row=1, column=2, sticky="we", **_PADDING)

        ttk.Label(content, text="Project name:").grid(
            row=2, column=0, sticky="w", **_PADDING
        )
        self.project_name_entry = ttk.Entry(
            content, textvariable=self.project_name_var, width=45
        )
        self.project_name_entry.grid(row=2, column=1, sticky="we", **_PADDING)

        buttons_frame = ttk.Frame(content)
        buttons_frame.grid(row=3, column=0, columnspan=3, sticky="e")
        self.create_button = ttk.Button(
            buttons_frame, text="Create", command=self.create_project
        )
        self.create_button.grid(row=0, column=0, **_PADDING)
        ttk.Button(buttons_frame, text="Cancel", command=self.destroy).grid(
            row=0, column=1, **_PADDING
        )
        content.columnconfigure(1, weight=1)

        self.bind("<Return>", lambda _event: self.create_project())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.project_name_entry.focus_set()
        self.lift()
        try:
            self.grab_set()
        except tk.TclError:
            # The grab fails if the window is not visible yet. The dialog
            # still works without it.
            pass

    def choose_parent_folder(self) -> None:
        directory = filedialog.askdirectory(
            parent=self,
            title="Select the folder for the new project",
            initialdir=self.parent_path_var.get(),
            mustexist=True,
        )
        if directory is None or len(directory) == 0:
            return
        self.parent_path_var.set(directory)

    def create_project(self) -> Optional[str]:
        """
        Create the project and return its path, or None if it failed.
        """
        parent_path = self.parent_path_var.get().strip()
        project_name = self.project_name_var.get().strip()
        error_message = validate_new_project_location(parent_path, project_name)
        if error_message is not None:
            messagebox.showerror("New project", error_message, parent=self)
            return None
        try:
            project_path = create_new_project(
                self.template_var.get(),
                os.path.join(parent_path, project_name),
            )
        except (LauncherError, OSError) as error_:
            messagebox.showerror("New project", str(error_), parent=self)
            return None
        self.destroy()
        self._on_project_created(project_path)
        return project_path
