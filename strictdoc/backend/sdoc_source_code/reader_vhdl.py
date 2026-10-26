"""
@relation(SDOC-SRS-142, SDOC-SRS-209, scope=file)
"""

import re
from typing import Dict, List, Optional, Tuple

import tree_sitter_vhdl
from tree_sitter import Language, Node, Parser

from strictdoc.backend.sdoc_source_code.constants import FunctionAttribute
from strictdoc.backend.sdoc_source_code.marker_parser import MarkerParser
from strictdoc.backend.sdoc_source_code.models.language import LanguageItem
from strictdoc.backend.sdoc_source_code.models.language_item_marker import (
    LanguageItemMarker,
    RangeMarkerType,
)
from strictdoc.backend.sdoc_source_code.models.line_marker import LineMarker
from strictdoc.backend.sdoc_source_code.models.range_marker import (
    RangeMarker,
)
from strictdoc.backend.sdoc_source_code.models.source_file_info import (
    SourceFileTraceabilityInfo,
)
from strictdoc.backend.sdoc_source_code.models.source_location import ByteRange
from strictdoc.backend.sdoc_source_code.models.source_node import SourceNode
from strictdoc.backend.sdoc_source_code.parse_context import ParseContext
from strictdoc.backend.sdoc_source_code.processors.general_language_marker_processors import (
    language_item_marker_processor,
    line_marker_processor,
    range_marker_processor,
    source_file_traceability_info_processor,
)
from strictdoc.backend.sdoc_source_code.tree_sitter_helpers import (
    traverse_tree,
)
from strictdoc.helpers.cast import assert_cast
from strictdoc.helpers.file_stats import SourceFileStats
from strictdoc.helpers.file_system import file_open_read_bytes

COMMENTS = ("line_comment", "block_comment")
SUBPROGRAM_DECLARATIONS = ("subprogram_declaration",)
SUBPROGRAM_DEFINITIONS = ("subprogram_definition",)
NAMES = ("identifier", "operator_symbol")
SPECIFICATIONS = ("procedure_specification", "function_specification")
# Referenceable, but not counted as functions in the source coverage.
DESIGN_ITEMS = (
    "entity_declaration",
    "architecture_definition",
    "process_statement",
)
UNITS = (
    "entity_declaration",
    "package_declaration",
    "package_definition",
    "type_declaration",
)

ITEMS = SUBPROGRAM_DECLARATIONS + SUBPROGRAM_DEFINITIONS + DESIGN_ITEMS
PARENTS = UNITS + SUBPROGRAM_DEFINITIONS + DESIGN_ITEMS[1:]


class SourceFileTraceabilityReader_VHDL:
    @staticmethod
    def supported_elements() -> list[str]:
        return ["function"]

    def __init__(self, custom_tags: Optional[set[str]] = None) -> None:
        self.custom_tags: Optional[set[str]] = custom_tags

    def read(
        self,
        input_buffer: bytes,
        file_path: Optional[str] = None,
    ) -> SourceFileTraceabilityInfo:
        assert isinstance(input_buffer, bytes)

        file_stats = SourceFileStats.create(input_buffer)
        parse_context = ParseContext(file_path, file_stats)
        parser = Parser(Language(tree_sitter_vhdl.language()))
        tree = parser.parse(input_buffer)

        traceability_info = SourceFileTraceabilityInfo([])

        # VHDL has "--" line comments and, since VHDL-2008, "/* */" block
        # comments. Consecutive full-line comments form one comment block. A
        # comment after code on the same line is a block of its own.
        comment_blocks: List[List[Node]] = []
        trailing_comment_lines: set[int] = set()
        item_nodes: List[Node] = []
        for node_ in traverse_tree(tree):
            if node_.type in COMMENTS:
                if self._is_trailing_comment(input_buffer, node_):
                    trailing_comment_lines.add(node_.start_point[0])
                    comment_blocks.append([node_])
                elif (
                    len(comment_blocks) > 0
                    and self._last_line(comment_blocks[-1][-1]) + 1
                    == node_.start_point[0]
                    and node_.start_point[0] - 1 not in trailing_comment_lines
                ):
                    comment_blocks[-1].append(node_)
                else:
                    comment_blocks.append([node_])
            elif node_.type in ITEMS:
                item_nodes.append(node_)

        blocks_by_last_line: Dict[int, List[Node]] = {
            self._last_line(block_[-1]): block_
            for block_ in comment_blocks
            if self._last_line(block_[-1]) not in trailing_comment_lines
        }
        attached_blocks: set[int] = set()

        root_node = tree.root_node
        if (
            len(comment_blocks) > 0
            and len(root_node.children) > 0
            and root_node.children[0] == comment_blocks[0][0]
        ):
            file_source_node = self._parse_comment_block(
                input_buffer,
                comment_blocks[0],
                line_end=file_stats.lines_total,
                parse_context=parse_context,
                custom_tags=self.custom_tags,
            )
            for marker_ in file_source_node.markers:
                if (
                    isinstance(marker_, LanguageItemMarker)
                    and marker_.scope == RangeMarkerType.FILE
                ):
                    language_item_marker_processor(marker_, parse_context)
                    traceability_info.markers.append(marker_)
                    # The file comment does not belong to the item below it.
                    blocks_by_last_line.pop(
                        self._last_line(comment_blocks[0][-1]), None
                    )

        for node_ in item_nodes:
            item_name = self._get_name(node_)
            if item_name is None:
                continue
            function_display_name = ".".join(
                [*self._get_parent_names(node_), item_name]
            )
            # Basic identifiers are case-insensitive, extended identifiers
            # (\Name\) are not. The key links a body to its declaration.
            function_name = ".".join(
                part_ if part_.startswith("\\") else part_.lower()
                for part_ in function_display_name.split(".")
            )
            is_definition = node_.type not in SUBPROGRAM_DECLARATIONS
            attributes = {
                FunctionAttribute.DEFINITION
                if is_definition
                else FunctionAttribute.DECLARATION
            }
            if node_.type in DESIGN_ITEMS:
                attributes.add(FunctionAttribute.NON_FUNCTION)

            comment_block = blocks_by_last_line.get(node_.start_point[0] - 1)
            language_item_markers: List[LanguageItemMarker] = []
            source_node: Optional[SourceNode] = None
            if comment_block is not None:
                attached_blocks.add(comment_block[0].start_byte)
                source_node = self._parse_comment_block(
                    input_buffer,
                    comment_block,
                    line_end=node_.end_point[0] + 1,
                    parse_context=parse_context,
                    entity_name=function_display_name,
                    custom_tags=self.custom_tags,
                )
                if is_definition:
                    traceability_info.source_nodes.append(source_node)
                for marker_ in source_node.markers:
                    if isinstance(marker_, LanguageItemMarker):
                        language_item_marker_processor(marker_, parse_context)
                        traceability_info.markers.append(marker_)
                        language_item_markers.append(marker_)

            start_node = (
                comment_block[0] if comment_block is not None else node_
            )
            new_function = LanguageItem(
                parent=traceability_info,
                name=function_name,
                display_name=function_display_name,
                line_begin=start_node.start_point[0] + 1,
                line_end=node_.end_point[0] + 1,
                code_byte_range=ByteRange.create_from_ts_node(node_),
                child_functions=[],
                markers=language_item_markers,
                attributes=attributes,
            )
            if source_node is not None:
                source_node.function = new_function
            traceability_info.functions.append(new_function)

        for block_ in comment_blocks:
            source_node = self._parse_comment_block(
                input_buffer,
                block_,
                line_end=self._last_line(block_[-1]) + 1,
                parse_context=parse_context,
            )
            for marker_ in source_node.markers:
                if isinstance(marker_, RangeMarker):
                    range_marker_processor(marker_, parse_context)
                elif isinstance(marker_, LineMarker):
                    line_marker_processor(marker_, parse_context)
                elif (
                    isinstance(marker_, LanguageItemMarker)
                    and marker_.scope == RangeMarkerType.FUNCTION
                    and block_[0].start_byte not in attached_blocks
                ):
                    print(  # noqa: T201
                        "warning: VHDL source reader: "
                        f"{parse_context.filename}:"
                        f"{marker_.ng_source_line_begin}: "
                        "skipping a scope=function marker for "
                        f"{', '.join(marker_.reqs)}: "
                        "no subprogram found directly below the comment."
                    )

        source_file_traceability_info_processor(
            traceability_info, parse_context
        )

        traceability_info.ng_map_reqs_to_markers = (
            parse_context.map_reqs_to_markers
        )

        return traceability_info

    def read_from_file(self, file_path: str) -> SourceFileTraceabilityInfo:
        with file_open_read_bytes(file_path) as file:
            return self.read(file.read(), file_path=file_path)

    def _parse_comment_block(
        self,
        input_buffer: bytes,
        comment_block: List[Node],
        line_end: int,
        parse_context: ParseContext,
        entity_name: Optional[str] = None,
        custom_tags: Optional[set[str]] = None,
    ) -> SourceNode:
        line_start = comment_block[0].start_point[0] + 1
        comment_bytes = input_buffer[
            comment_block[0].start_byte : comment_block[-1].end_byte
        ]
        # The common comment preprocessor does not know "--". Blank out the
        # comment delimiters with the same length to keep the byte offsets
        # for write-back.
        comment_text = re.sub(
            r"^(\s*)--|/\*|\*/",
            lambda match_: " " * len(match_.group(0)),
            comment_bytes.decode("utf8"),
            flags=re.MULTILINE,
        )
        return MarkerParser.parse(
            input_string=comment_text,
            line_start=line_start,
            line_end=line_end,
            comment_line_start=line_start,
            comment_byte_range=ByteRange.create_from_ts_nodes(
                comment_block[0], comment_block[-1]
            ),
            filename=parse_context.filename,
            entity_name=entity_name,
            custom_tags=custom_tags,
        )

    @staticmethod
    def _is_trailing_comment(input_buffer: bytes, node: Node) -> bool:
        line_start_byte = input_buffer.rfind(b"\n", 0, node.start_byte) + 1
        return len(input_buffer[line_start_byte : node.start_byte].strip()) > 0

    @staticmethod
    def _last_line(node: Node) -> int:
        # A line comment node includes the newline and ends on the next row.
        if node.type == "line_comment":
            return node.start_point[0]
        return node.end_point[0]

    @staticmethod
    def _child(node: Node, types: Tuple[str, ...] = NAMES) -> Optional[Node]:
        for child_ in node.children:
            if child_.type in types:
                return child_
        return None

    @staticmethod
    def _get_name(node: Node) -> Optional[str]:
        # A unit, subprogram or process label name, or "Top(Rtl)" for the
        # architecture Rtl of the entity Top.
        child = SourceFileTraceabilityReader_VHDL._child
        text = SourceFileTraceabilityReader_VHDL._node_text
        if node.type == "architecture_definition":
            entity_ = text(child(child(node, ("name",)) or node))
            return f"{entity_}({text(child(node))})"
        if node.type == "process_statement":
            label_ = child(node, ("label_declaration",))
            name_node = child(label_, ("label",)) if label_ else None
        else:
            name_node = child(child(node, SPECIFICATIONS) or node)
        return text(name_node) if name_node is not None else None

    @staticmethod
    def _get_parent_names(node: Node) -> List[str]:
        # Names of the enclosing units and subprograms, outermost first, e.g.
        # "Pkg.Proc", or "Top(Rtl).Func" in the architecture Rtl of Top.
        parent_names = []
        cursor = node.parent
        while cursor is not None:
            if cursor.type in PARENTS:
                name_ = SourceFileTraceabilityReader_VHDL._get_name(cursor)
                if name_ is not None:
                    parent_names.append(name_)
            cursor = cursor.parent
        parent_names.reverse()
        return parent_names

    @staticmethod
    def _node_text(node: Optional[Node]) -> str:
        return assert_cast(assert_cast(node, Node).text, bytes).decode("utf8")
