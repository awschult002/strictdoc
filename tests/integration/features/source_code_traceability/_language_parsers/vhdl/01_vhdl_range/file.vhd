entity hello is
end entity hello;

architecture rtl of hello is
begin
  process
  begin
    -- @relation(REQ-1, scope=range_start)
    report "hello world";
    -- @relation(REQ-1, scope=range_end)
    wait;
  end process;
end architecture rtl;
