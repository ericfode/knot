import Base

# A String tail bound without `+` is affine after a literal row splits it.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def tail(s: String) -> Answer:
  match s:
    case "ab": No{}
    case SCon{c, t}: answer(String.eq(String.append(t, t), "cc"))
    case _: No{}

def main() -> Answer:
  tail("bc")
