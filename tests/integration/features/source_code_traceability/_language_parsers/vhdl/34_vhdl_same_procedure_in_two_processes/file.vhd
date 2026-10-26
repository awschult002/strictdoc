entity counter is
end entity counter;

architecture rtl of counter is
begin
  a : process
    -- @relation(REQ-1, scope=function)
    procedure tick is
    begin
      null;
    end procedure;
  begin
    wait;
  end process a;

  b : process
    -- @relation(REQ-2, scope=function)
    procedure tick is
    begin
      null;
    end procedure;
  begin
    wait;
  end process b;
end architecture rtl;
