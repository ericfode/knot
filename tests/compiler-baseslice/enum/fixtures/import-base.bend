import Base

type Answer is Data:
  No{}
  Yes{}

def answer(x: Bool) -> Answer:
  match x:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  answer(Bool.not(False{}))
