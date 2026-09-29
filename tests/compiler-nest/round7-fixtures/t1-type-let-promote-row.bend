type Mode is Type:
  Lo{}
  Hi{}

def f(m: Mode) -> Mode:
  k = m
  match k:
    case +y: y
