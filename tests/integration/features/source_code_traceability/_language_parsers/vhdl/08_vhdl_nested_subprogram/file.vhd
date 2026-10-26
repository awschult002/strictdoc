package body outer is
  -- @relation(REQ-1, scope=function)
  procedure p is
    -- @relation(REQ-2, scope=function)
    function inner (x : integer) return integer is
    begin
      return x;
    end function inner;
  begin
    null;
  end procedure p;
end package body outer;
