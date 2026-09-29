type Mode is Type:
  Lo{}
  Hi{}

def f(m: Mode) -> Mode:
  match m:
    case +y:
      match y:
        case Lo{}: y
        case z: z
