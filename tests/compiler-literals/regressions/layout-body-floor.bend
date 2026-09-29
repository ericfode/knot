import Base

# A match in a dedented arm body takes only the cases right of the enclosing `case`. These
# cases stand in that column, so the seed reads the match with no rows and the cases as rows
# of the Answer match; read as the inner match's, they would complete both matches.
type Answer is Type:
  No{}
  Yes{}

def f(a: Answer, b: Bool) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  f(Yes{}, True{})
