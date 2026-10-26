entity counter is
  port (clk : in bit);
end entity counter;

-- @relation(REQ-1, scope=range_start)
architecture rtl of counter is
  -- @relation(REQ-2, scope=function)
  function inc (x : integer) return integer is
  begin
    return x + 1;
  end function;
begin
end architecture rtl;
-- @relation(REQ-1, scope=range_end)

architecture sim of counter is
  function inc (x : integer) return integer is
  begin
    return x + 2;
  end function;
begin
  p : process (clk)
    -- @relation(REQ-3, scope=function)
    procedure tick is
    begin
      null;
    end procedure;
  begin
    tick;
  end process p;
end architecture sim;
