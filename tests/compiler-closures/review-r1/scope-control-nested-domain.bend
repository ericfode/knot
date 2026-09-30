type T is Data:
  K{}
def main() -> T:
  v : T = K{}
  f : (T -> T) -> T = g => g(K{})
  f(x => x)
