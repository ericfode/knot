# An imported module calls its own generic def while the entry reuses the bare
# name with another signature (INT-02: eval.bend's `select` against eval-cli's).
import Base
import ./lib.bend as L

type Answer is Type:
  No{}
  Yes{}

type Choice is Type:
  Keep{}
  Swap{}

def select(x: L.Color) -> Answer:
  match x:
    case L.Red{}: Yes{}
    case L.Green{}: No{}
    case L.Blue{}: No{}

def flag(c: Choice) -> L.Flag:
  match c:
    case Keep{}: L.Off{}
    case Swap{}: L.On{}

def probe(c: Choice) -> Answer:
  select(L.pick(flag(c),L.Red{},L.Blue{}))

def main() -> Answer:
  probe(Keep{})
