--! @relation(REQ-1, scope=file)
entity e is
end entity;

architecture rtl of e is
begin
  --! @relation(REQ-2, scope=range_start)
  p : process
  begin
    wait; --! @relation(REQ-3, scope=line)
  end process;
  --! @relation(REQ-2, scope=range_end)
end architecture;
