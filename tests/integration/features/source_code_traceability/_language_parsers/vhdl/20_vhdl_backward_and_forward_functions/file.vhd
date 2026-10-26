-- @relation(REQ-1, scope=file)

package body hello is
  -- @relation(REQ-2, scope=function, role=Implementation)
  -- @relation(REQ-1, scope=function, role=Test)
  procedure foo is
  begin
    null;
  end procedure foo;

  -- @relation(REQ-3, scope=range_start)
  procedure bar is
  begin
    null;
  end procedure bar;
  -- @relation(REQ-3, scope=range_end)

  procedure some_func is begin end;

  -- @relation(REQ-3, scope=function)
  procedure long_function_name is
  begin
    -- boo
    -- @relation(REQ-4, scope=range_start)
    -- boo
    some_func; -- @relation(REQ-1, scope=line)
    -- boo
    -- @relation(REQ-4, scope=range_end)
    -- boo
  end procedure long_function_name;
end package body hello;
