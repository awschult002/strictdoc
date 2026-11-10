"""
Append a saved query to the queries=[...] list of a strictdoc_config.py file.

The file is edited as text, not regenerated from the AST, so that the user's
comments and formatting stay as they are. Python's ast module is only used to
find where the new entry has to be inserted.
"""

import ast
import io
import tokenize
from typing import List, Optional, Sequence, Tuple, Union

from strictdoc.core.project_config import (
    ProjectConfig,
    ProjectConfigLoader,
    SavedQuery,
    validate_saved_queries,
)


class SavedQueryWriteError(Exception):
    pass


Position = Tuple[int, int]  # (1-based line number, 0-based character column)
_Node = Union[ast.expr, ast.keyword]


class _Source:
    def __init__(self, source: str) -> None:
        self.lines: List[str] = source.splitlines(keepends=True)
        self.newline: str = "\r\n" if "\r\n" in source else "\n"
        self.comma_positions: List[Position] = [
            token_.start
            for token_ in tokenize.generate_tokens(io.StringIO(source).readline)
            if token_.type == tokenize.OP and token_.string == ","
        ]

    def char_col(self, lineno: int, byte_col: int) -> int:
        # The ast module reports UTF-8 byte offsets, the text needs characters.
        line = self.lines[lineno - 1]
        return len(line.encode("utf-8")[:byte_col].decode("utf-8"))

    def start(self, node: _Node) -> Position:
        return node.lineno, self.char_col(node.lineno, node.col_offset)

    def end(self, node: _Node) -> Position:
        assert node.end_lineno is not None and node.end_col_offset is not None
        return node.end_lineno, self.char_col(
            node.end_lineno, node.end_col_offset
        )

    def has_comma_between(self, begin: Position, end: Position) -> bool:
        return any(begin <= comma_ < end for comma_ in self.comma_positions)

    def indent_of(self, lineno: int) -> str:
        line = self.lines[lineno - 1]
        return line[: len(line) - len(line.lstrip())]

    def insert(self, position: Position, text: str) -> None:
        lineno, col = position
        line = self.lines[lineno - 1]
        self.lines[lineno - 1] = line[:col] + text + line[col:]

    def text(self) -> str:
        return "".join(self.lines)


def _find_project_config_call(tree: ast.Module) -> ast.Call:
    create_config: Optional[ast.FunctionDef] = None
    for node_ in tree.body:
        if isinstance(node_, ast.FunctionDef) and node_.name == "create_config":
            create_config = node_
    if create_config is None:
        raise SavedQueryWriteError(
            "The config file has no create_config() function."
        )
    calls = [
        node_
        for node_ in ast.walk(create_config)
        if isinstance(node_, ast.Call)
        and (
            (
                isinstance(node_.func, ast.Name)
                and node_.func.id == "ProjectConfig"
            )
            or (
                isinstance(node_.func, ast.Attribute)
                and node_.func.attr == "ProjectConfig"
            )
        )
    ]
    if len(calls) != 1:
        raise SavedQueryWriteError(
            "Could not find exactly one ProjectConfig(...) call in "
            "create_config(). Add the query to the config file by hand."
        )
    return calls[0]


def _append_item(
    source: _Source,
    container: Union[ast.List, ast.Call],
    items: Sequence[_Node],
    new_item: str,
) -> None:
    """
    Insert new_item as the last item of a list literal or a call, right
    before its closing bracket. The existing items keep their formatting.
    """
    closing = source.end(container)
    closing = (closing[0], closing[1] - 1)
    opening_lineno = container.lineno

    closing_line_prefix = source.lines[closing[0] - 1][: closing[1]]
    closing_is_on_own_line = (
        opening_lineno != closing[0] and closing_line_prefix.strip() == ""
    )

    if len(items) == 0:
        if closing_is_on_own_line:
            indent = source.indent_of(opening_lineno) + "    "
            source.insert(
                (closing[0], 0), f"{indent}{new_item},{source.newline}"
            )
        else:
            source.insert(closing, new_item)
        return

    last_item_end = source.end(items[-1])
    has_trailing_comma = source.has_comma_between(last_item_end, closing)

    if not closing_is_on_own_line:
        # The closing bracket follows the last item on the same line:
        # ProjectConfig(a=1) or [SavedQuery(...)].
        separator = " " if has_trailing_comma else ", "
        source.insert(closing, separator + new_item)
        return

    # Multi-line: add a new line before the closing bracket, indented like
    # the last item.
    indent = source.indent_of(source.start(items[-1])[0])
    source.insert((closing[0], 0), f"{indent}{new_item},{source.newline}")
    if not has_trailing_comma:
        source.insert(last_item_end, ",")


def _has_saved_query_import(tree: ast.Module) -> bool:
    for node_ in tree.body:
        if isinstance(node_, ast.ImportFrom):
            for alias_ in node_.names:
                if (alias_.asname or alias_.name) == "SavedQuery":
                    return True
        elif isinstance(node_, ast.Assign):
            for target_ in node_.targets:
                if isinstance(target_, ast.Name) and target_.id == "SavedQuery":
                    return True
    return False


def append_saved_query(config_source: str, *, title: str, value: str) -> str:
    """
    Return config_source with SavedQuery(title=..., value=...) appended to
    the queries=[...] list of the ProjectConfig(...) call in create_config().
    If the call has no queries= argument yet, one is added.
    """
    try:
        tree = ast.parse(config_source)
    except SyntaxError as exception_:
        raise SavedQueryWriteError(
            f"The config file could not be parsed: {exception_}"
        ) from exception_

    source = _Source(config_source)
    new_query = f"SavedQuery(title={title!r}, value={value!r})"

    call = _find_project_config_call(tree)
    queries_keyword = next(
        (keyword_ for keyword_ in call.keywords if keyword_.arg == "queries"),
        None,
    )
    if queries_keyword is not None:
        if not isinstance(queries_keyword.value, ast.List):
            raise SavedQueryWriteError(
                "The queries argument of ProjectConfig(...) is not a list "
                "literal. Add the query to the config file by hand."
            )
        _append_item(
            source, queries_keyword.value, queries_keyword.value.elts, new_query
        )
    else:
        call_items: List[_Node] = [*call.args, *call.keywords]
        call_items.sort(key=source.start)
        _append_item(source, call, call_items, f"queries=[{new_query}]")

    if not _has_saved_query_import(tree):
        # Insert after the last top-level import, or after the module
        # docstring if there are no imports.
        last_import_lineno = 0
        first_node = tree.body[0] if len(tree.body) > 0 else None
        if (
            isinstance(first_node, ast.Expr)
            and isinstance(first_node.value, ast.Constant)
            and isinstance(first_node.value.value, str)
        ):
            last_import_lineno = first_node.end_lineno or first_node.lineno
        for node_ in tree.body:
            if isinstance(node_, (ast.Import, ast.ImportFrom)):
                last_import_lineno = node_.end_lineno or node_.lineno
        import_line = f"from strictdoc.api import SavedQuery{source.newline}"
        source.lines.insert(last_import_lineno, import_line)

    return source.text()


def save_query_to_project_config(
    project_config: ProjectConfig, *, title: str, value: str
) -> None:
    """
    Append a saved query to the project's strictdoc_config.py and reload the
    queries of the in-memory project config from the updated file.
    """
    config_py_path = project_config.config_py_path
    if config_py_path is None:
        raise SavedQueryWriteError(
            "Queries can only be saved to a strictdoc_config.py project "
            "config. Add the query to the config file by hand."
        )
    title = title.strip()
    value = value.strip()
    if len(title) == 0:
        raise SavedQueryWriteError("The query title must not be empty.")
    if project_config.get_saved_query(title) is not None:
        raise SavedQueryWriteError(
            f"A saved query with the title '{title}' already exists."
        )
    try:
        validate_saved_queries(
            [*project_config.queries, SavedQuery(title=title, value=value)]
        )
    except ValueError as exception_:
        raise SavedQueryWriteError(str(exception_)) from exception_

    with open(config_py_path, encoding="utf-8", newline="") as file_:
        old_source = file_.read()
    new_source = append_saved_query(old_source, title=title, value=value)

    def write(source: str) -> None:
        with open(config_py_path, "w", encoding="utf-8", newline="") as file_:
            file_.write(source)

    write(new_source)
    try:
        reloaded_config = ProjectConfigLoader.load_from_python(
            config_py_path=config_py_path
        )
        reloaded_query = reloaded_config.get_saved_query(title)
        if reloaded_query is None or reloaded_query.value != value:
            raise SavedQueryWriteError(
                "The saved query was not found after reloading the config "
                "file. Add the query to the config file by hand."
            )
    except Exception as exception_:
        write(old_source)
        if isinstance(exception_, SavedQueryWriteError):
            raise
        raise SavedQueryWriteError(
            f"The config file could not be reloaded after saving the query, "
            f"so the change was undone: {exception_}"
        ) from exception_

    project_config.queries = reloaded_config.queries
