package body hello is
  -- Some text.
  --
  procedure hello_world is
  begin
    report "hello world";
  end procedure hello_world;

  function answer return integer is
  begin
    return 42;
  end function answer;

  procedure hello_world_3 is
  begin
    null;
  end procedure;

  procedure hello_world_4 is
  begin
    null;
  end hello_world_4;
end package body hello;
