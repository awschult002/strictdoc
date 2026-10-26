package gpkg is
  generic (type t; function eq (a, b : t) return boolean is <>);
  -- @relation(REQ-1, scope=function)
  procedure swap generic (type e) parameter (a, b : inout e);
end package gpkg;

package body gpkg is
  procedure swap generic (type e) parameter (a, b : inout e) is
    variable tmp : e;
  begin
    tmp := a; a := b; b := tmp;
  end procedure swap;
end package body gpkg;

package ipkg is new work.gpkg generic map (t => integer, eq => "=");
