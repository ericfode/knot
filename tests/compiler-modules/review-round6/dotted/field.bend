type Light is Type:
  Dark{}
  Lit{}

type Box is Type:
  Box{a.b: Light}

def f(p: Box) -> Light:
  match p:
    case Box{a.b}: a.b

def main() -> Light:
  f(Box{Lit{}})
