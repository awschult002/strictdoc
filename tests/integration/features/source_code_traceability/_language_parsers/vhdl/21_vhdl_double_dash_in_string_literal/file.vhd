package body hello is
  constant lbl : string := "-- @relation(REQ-2, scope=file)";

  -- @relation(REQ-1, scope=function)
  procedure hello_world is
    constant t : string := "-- @relation(REQ-2, scope=line)";
  begin
    null;
  end procedure;
end package body hello;
