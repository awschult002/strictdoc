package hello is
  procedure pub;
end package hello;

package body hello is
  -- @relation(REQ-1, scope=function)
  procedure local_helper is
  begin
    null;
  end procedure;
  procedure pub is
  begin
    local_helper;
  end procedure;
end package body hello;
