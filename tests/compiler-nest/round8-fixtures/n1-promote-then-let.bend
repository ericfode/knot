type Mode is Type:
  Lo{}
  Hi{}

def f(m: Mode) -> Mode:
  match m:
    case +y:
      k = y
      k
