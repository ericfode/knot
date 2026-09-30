import Base

# Source algebra only. Compiler refinement is tested by the frozen oracle.
law not_involution:
  for x: Bool
  {Bool.not(Bool.not(x)) == x : Bool}

law and_associative:
  for x: Bool
  for y: Bool
  for z: Bool
  {Bool.and(Bool.and(x,y),z) == Bool.and(x,Bool.and(y,z)) : Bool}

law or_associative:
  for x: Bool
  for y: Bool
  for z: Bool
  {Bool.or(Bool.or(x,y),z) == Bool.or(x,Bool.or(y,z)) : Bool}

law de_morgan:
  for x: Bool
  for y: Bool
  {Bool.not(Bool.and(x,y)) == Bool.or(Bool.not(x),Bool.not(y)) : Bool}

law lt_is_unequal:
  {Cmp.is_eq(LT{}) == False{} : Bool}

law eq_is_equal:
  {Cmp.is_eq(EQ{}) == True{} : Bool}

law gt_is_unequal:
  {Cmp.is_eq(GT{}) == False{} : Bool}

law unit_unique:
  for x: Unit
  {x == Unit{} : Unit}
