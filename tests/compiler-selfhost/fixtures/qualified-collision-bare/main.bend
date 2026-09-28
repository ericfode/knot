# Twin of qualified-collision: the entry calls the module's `pick` by its bare name.
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
  select(pick(flag(c),L.Red{},L.Blue{}))

def main() -> Answer:
  probe(Keep{})
