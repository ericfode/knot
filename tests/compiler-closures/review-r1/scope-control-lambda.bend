type T is Data:
  K{}
def main() -> T:
  f : T -> T = v =>
    g : T -> T = x => x
    g(v)
  f(K{})
