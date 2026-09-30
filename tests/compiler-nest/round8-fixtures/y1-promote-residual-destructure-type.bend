type Mode is Type:
  Lo{}
  Hi{}

def f(m: Mode) -> Mode:
  match m:
    case Lo{}: Hi{}
    case +y:
      match y:
        case Hi{}: Lo{}
