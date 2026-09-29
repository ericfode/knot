# depth-13 unary pattern plus one default row.
type Flag is Data:
  Off{}
  On{}

type N is Type:
  Z{}
  S{p: N}

def is_d(n: N) -> Flag:
  match n:
    case S{S{S{S{S{S{S{S{S{S{S{S{S{Z{}}}}}}}}}}}}}}: On{}
    case _: Off{}

def main() -> Flag:
  is_d(S{S{S{S{S{S{S{S{S{S{S{S{S{Z{}}}}}}}}}}}}}})
