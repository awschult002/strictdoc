package body hello is
  /* Some text.
     @relation(REQ-1, scope=function) */
  procedure hello_world is
  begin
    null;
  end procedure;

  /* @relation(REQ-2, scope=line) */ constant c : integer := 1;
end package body hello;
