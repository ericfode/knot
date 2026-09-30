type T is Data:
  K{}
def use(f: T -> T) -> T:
  f(K{})
def main() -> T:
  use(x => x)
