type Light is Type:
  Dark{}
  Lit{}

type Box is Type:
  Box{v: Light, w: Light}

def f(a.b: Light, p: Box) -> Light:
  match p:
    case Box{a.b, Lit{}}: a.b
    case _: Dark{}

def main() -> Light:
  f(Dark{}, Box{Lit{}, Lit{}})
