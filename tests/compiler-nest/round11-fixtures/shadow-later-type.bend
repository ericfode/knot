def f(a: Later) -> Later:
  match a:
    case Later:
      y : Later = L0{}
      y

type Later is Data:
  L0{}

def main() -> Later:
  f(L0{})
