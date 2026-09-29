import Base

def code_is(c: Char, n: U32) -> Bool:
  match c:
    case Chr{x}:
      U32.is_eq(x, n)

def main() -> Bool:
  Bool.and(code_is('a', 97), code_is(Char.from_u32(2147483649), 2147483649))
