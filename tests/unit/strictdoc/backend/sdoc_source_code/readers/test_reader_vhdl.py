"""
@relation(SDOC-SRS-209, scope=file)
"""

from strictdoc.backend.sdoc_source_code.constants import FunctionAttribute
from strictdoc.backend.sdoc_source_code.models.source_file_info import (
    SourceFileTraceabilityInfo,
)
from strictdoc.backend.sdoc_source_code.reader_registry import (
    SourceCodeReaderRegistry,
)
from strictdoc.backend.sdoc_source_code.reader_vhdl import (
    SourceFileTraceabilityReader_VHDL,
)
from strictdoc.core.file_system.source_tree import SourceFileType
from strictdoc.core.project_config import ProjectConfig


def test_00_empty_file():
    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(b"", file_path="NOT_RELEVANT")

    assert isinstance(info, SourceFileTraceabilityInfo)
    assert len(info.functions) == 0
    assert len(info.markers) == 0


def test_01_subprogram_bodies():
    input_string = b"""\
package body hello is
  -- Some text.
  --
  -- @relation(REQ-1, scope=function)
  procedure hello_world is
  begin
    report "hello world";
  end procedure hello_world;

  -- @relation(REQ-2, scope=function)
  function answer return integer is
  begin
    return 42;
  end function answer;
end package body hello;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="hello.vhd")

    assert [function_.display_name for function_ in info.functions] == [
        "hello.hello_world",
        "hello.answer",
    ]
    assert len(info.markers) == 2
    assert info.markers[0].ng_source_line_begin == 4
    assert info.markers[0].ng_range_line_begin == 2
    assert info.markers[0].ng_range_line_end == 8
    assert info.markers[0].reqs_objs[0].ng_source_column == 16
    assert info.markers[1].ng_range_line_begin == 10
    assert info.markers[1].ng_range_line_end == 14
    assert info.functions[0].attributes == {FunctionAttribute.DEFINITION}
    assert len(info.source_nodes) == 2


def test_02_package_declarations():
    input_string = b"""\
package hello is
  -- @relation(REQ-1, scope=function)
  procedure hello_world (count : integer);

  /* @relation(REQ-2, scope=function) */
  function answer return integer;
end package hello;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="hello.vhd")

    assert [function_.display_name for function_ in info.functions] == [
        "hello.hello_world",
        "hello.answer",
    ]
    assert info.functions[0].attributes == {FunctionAttribute.DECLARATION}
    assert info.markers[0].ng_range_line_begin == 2
    assert info.markers[0].ng_range_line_end == 3
    assert info.markers[1].ng_range_line_begin == 5
    assert info.markers[1].ng_range_line_end == 6
    assert len(info.source_nodes) == 0


def test_03_nested_subprogram_and_architecture():
    input_string = b"""\
architecture rtl of counter is
  procedure outer is
    -- @relation(REQ-1, scope=function)
    function inner return bit is
    begin
      return '0';
    end function;
  begin
    null;
  end procedure;
begin
  p : process
    procedure tick is
    begin
      null;
    end procedure;
  begin
    wait;
  end process p;
end architecture rtl;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="counter.vhd")

    assert [function_.display_name for function_ in info.functions] == [
        "counter(rtl)",
        "counter(rtl).outer",
        "counter(rtl).outer.inner",
        "counter(rtl).p",
        "counter(rtl).p.tick",
    ]
    assert [function_.is_function() for function_ in info.functions] == [
        False,
        True,
        True,
        False,
        True,
    ]
    assert info.functions[2].markers[0].reqs == ["REQ-1"]


def test_04_file_range_and_line_markers():
    input_string = b"""\
/* @relation(REQ-1, scope=file) */

entity hello is
end entity;

architecture rtl of hello is
  -- @relation(REQ-2, scope=range_start)
  signal count : integer := 0;
  -- @relation(REQ-2, scope=range_end)
  constant lbl : string := "-- @relation(REQ-3, scope=line)";
begin
end architecture;"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="hello.vhd")

    assert [function_.display_name for function_ in info.functions] == [
        "hello",
        "hello(rtl)",
    ]
    assert info.functions[0].line_begin == 3
    assert len(info.functions[0].markers) == 0
    assert info.markers[0].reqs == ["REQ-1"]
    assert info.markers[0].ng_range_line_begin == 1
    assert info.markers[0].ng_range_line_end == 12
    assert info.markers[1].reqs == ["REQ-2"]
    assert info.markers[1].ng_range_line_begin == 7
    assert info.markers[1].ng_range_line_end == 9
    assert "REQ-3" not in info.ng_map_reqs_to_markers


def test_05_warning_for_scope_function_marker_without_subprogram(capsys):
    input_string = b"""\
-- @relation(REQ-1, scope=function)
context ctx is
  library ieee;
end context;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="ctx.vhd")

    assert len(info.functions) == 0
    assert (
        "VHDL source reader: ctx.vhd:1: skipping a scope=function marker "
        "for REQ-1" in capsys.readouterr().out
    )


def test_06_lower_case_name_and_extended_identifiers():
    input_string = b"""\
PACKAGE Hello IS
  PROCEDURE DO_IT;
  procedure put (value : integer);
  procedure put (value : real);
  procedure \\Foo\\;
  procedure \\foo\\;
END PACKAGE;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="hello.vhd")

    assert info.functions[0].name == "hello.do_it"
    assert info.functions[0].display_name == "Hello.DO_IT"
    assert info.functions[1].name == info.functions[2].name == "hello.put"
    assert info.functions[3].name == "hello.\\Foo\\"
    assert info.functions[4].name == "hello.\\foo\\"


def test_07_marked_overloads_keep_all_markers():
    input_string = b"""\
package body hello is
  -- @relation(REQ-1, scope=function)
  procedure put (value : integer) is begin end;

  -- @relation(REQ-2, scope=function)
  procedure put (value : real) is begin end;
end package body;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="hello.vhd")

    assert [marker_.reqs for marker_ in info.markers] == [["REQ-1"], ["REQ-2"]]
    assert info.functions[0].markers[0].reqs == ["REQ-1"]
    assert info.functions[1].markers[0].reqs == ["REQ-2"]


def test_08_generics_and_protected_types():
    input_string = b"""\
package gpkg is
  generic (type t; function eq (a, b : t) return boolean is <>);
  procedure swap generic (type e) parameter (a, b : inout e);
  type counter_t is protected
    procedure incr;
  end protected counter_t;
end package gpkg;

package ipkg is new work.gpkg generic map (t => integer, eq => "=");
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="gpkg.vhd")

    assert [function_.display_name for function_ in info.functions] == [
        "gpkg.swap",
        "gpkg.counter_t.incr",
    ]


def test_09_broken_input_does_not_crash():
    input_string = b"""\
package body hello is
  -- @relation(REQ-1, scope=function)
  procedure hello_world is
  begin
    null;
  end procedure;
end package body hello
garbage (((
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="hello.vhd")

    assert info.markers[0].reqs == ["REQ-1"]


def test_10_registry_and_file_type():
    for path_ in ("x.vhd", "x.vhdl"):
        reader = SourceCodeReaderRegistry.get_reader(
            path_, ProjectConfig.default_config(), None
        )
        assert isinstance(reader, SourceFileTraceabilityReader_VHDL)
        assert SourceFileType.create_from_path(path_) == SourceFileType.VHDL


def test_11_subprogram_in_entity_declarative_part():
    input_string = b"""\
entity counter is
  port (clk : in bit);
  -- @relation(REQ-1, scope=function)
  procedure foo is
  begin
    null;
  end procedure;
end entity counter;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="counter.vhd")

    assert [function_.display_name for function_ in info.functions] == [
        "counter",
        "counter.foo",
    ]
    assert info.functions[1].markers[0].reqs == ["REQ-1"]


def test_12_entity_architecture_and_process_items():
    input_string = b"""\
-- @relation(REQ-1, scope=function)
entity counter is
end entity counter;

-- @relation(REQ-2, scope=function)
architecture rtl of counter is
begin
  -- @relation(REQ-3, scope=function)
  tick : process
  begin
    wait;
  end process tick;

  process
  begin
    wait;
  end process;
end architecture rtl;

architecture sim of counter is
begin
end architecture sim;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="counter.vhd")

    assert [
        (function_.display_name, function_.line_begin, function_.line_end)
        for function_ in info.functions
    ] == [
        ("counter", 1, 3),
        ("counter(rtl)", 5, 18),
        ("counter(rtl).tick", 8, 12),
        ("counter(sim)", 20, 22),
    ]
    assert [marker_.reqs for marker_ in info.markers] == [
        ["REQ-1"],
        ["REQ-2"],
        ["REQ-3"],
    ]
    assert not any(function_.is_function() for function_ in info.functions)
    assert info.get_functions_total() == 0


def test_13_subprograms_in_labeled_and_unlabeled_processes():
    input_string = b"""\
architecture rtl of counter is
begin
  a : process
    -- @relation(REQ-1, scope=function)
    procedure tick is begin end;
  begin
    wait;
  end process a;

  b : process
    -- @relation(REQ-2, scope=function)
    procedure tick is begin end;
  begin
    wait;
  end process b;

  process
    procedure tock is begin end;
  begin
    wait;
  end process;
end architecture rtl;
"""

    reader = SourceFileTraceabilityReader_VHDL()

    info = reader.read(input_string, file_path="counter.vhd")

    assert [function_.name for function_ in info.functions] == [
        "counter(rtl)",
        "counter(rtl).a",
        "counter(rtl).a.tick",
        "counter(rtl).b",
        "counter(rtl).b.tick",
        "counter(rtl).tock",
    ]
    assert info.functions[2].markers[0].reqs == ["REQ-1"]
    assert info.functions[4].markers[0].reqs == ["REQ-2"]
