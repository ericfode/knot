type Light is Data:
  Dark{}
  Lit{}

type Box is Data:
  Box{v: Light}

def f(b: Box) -> Light:
  match b:
    case Box{Light}:
      y : Light = Dark{}
      y

def main() -> Light:
  f(Box{Lit{}})
