import Base

# Promoted fields leave the String column affine for the catch-all.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def default(v: String) -> Answer:
  match v:
    case SCon{+c, +t}: No{}
    case _: answer(String.eq(String.append(v, v), ""))

def main() -> Answer:
  default("")
