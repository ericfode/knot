# Seed-accepted raw non-ASCII source text; Knot source stays ASCII (use \u{e9}).
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(String.eq("é", "\u{e9}"))
