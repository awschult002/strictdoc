package p is
  type counter_t is protected
    -- @relation(REQ-1, scope=function)
    procedure incr;
    impure function get return integer;
  end protected counter_t;
end package p;

package body p is
  type counter_t is protected body
    variable n : integer := 0;
    -- @relation(REQ-2, scope=function)
    procedure incr is
    begin
      n := n + 1;
    end procedure;
    impure function get return integer is
    begin
      return n;
    end function;
  end protected body counter_t;
end package body p;
