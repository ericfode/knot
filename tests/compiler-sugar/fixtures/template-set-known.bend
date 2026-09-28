# The scope.set_known shape: ~A: Data and ~value: A -> Flag -> Flag, a self-call, two instances.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Row is Data:
  End{}
  Cell{flag: Flag, rest: Row}

def set_all(~A: Data, ~value: A -> Flag -> Flag, row: Row, +payload: A) -> Row:
  match row:
    case End{}: End{}
    case Cell{flag,rest}:
      Cell{value(payload,flag),set_all(~A,~value,rest,payload)}

def mix(c: Color, f: Flag) -> Flag:
  match c:
    case Red{}: Off{}
    case Blue{}: f

def refine(row: Row, +c: Color) -> Row:
  set_all(~Color,~(c => f => mix(c,f)),row,c)

def replace(row: Row, +g: Flag) -> Row:
  set_all(~Flag,~(g => f => g),row,g)

def first(row: Row) -> Flag:
  match row:
    case End{}: Off{}
    case Cell{flag,rest}: flag

def second(row: Row) -> Flag:
  match row:
    case End{}: Off{}
    case Cell{flag,rest}: first(rest)

def refined(a: Flag, c: Color) -> Flag:
  first(refine(Cell{a,End{}},c))

def replaced(a: Flag, g: Flag) -> Flag:
  second(replace(Cell{Off{},Cell{a,End{}}},g))

def main() -> Flag:
  refined(On{},Blue{})
