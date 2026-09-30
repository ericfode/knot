type Light is Type:
  Dark{}
  Lit{}

type Box is Type:
  Box{v: Light}

def f(a.b: Light, p: Box) -> Light:
  match p:
    case Box{a.b}: a.b

def main() -> Light:
  f(Dark{}, Box{Lit{}})
