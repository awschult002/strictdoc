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

  -- @relation(REQ-1, REQ-2, scope=function)
  procedure hello_world_3 is
  begin
    null;
  end procedure;

  -- @relation(REQ-1, scope=function)
  -- @relation(REQ-2, scope=function)
  procedure hello_world_4 is
  begin
    null;
  end hello_world_4;
end package body hello;
