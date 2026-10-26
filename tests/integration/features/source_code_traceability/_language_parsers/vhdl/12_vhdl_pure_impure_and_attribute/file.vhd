package hello is
  -- @relation(REQ-1, scope=function)
  impure function next_id return natural;
  attribute keep : boolean;
  -- @relation(REQ-2, scope=function)
  pure function f (constant a : in bit_vector(7 downto 0)) return bit;
end package hello;
