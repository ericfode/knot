# Declaration order is decided within one module: an imported constructor is declared before
# every body of its importer, whatever the byte offsets of the two files say.
import ./qualified-order-lib-first/lib.bend as L

type Answer is Type:
  No{}
  Yes{}

def g(a: Answer, b: L.Box) -> Answer:
  match b:
    case L.Box{L.On{}}: a
    case L.Box{L.Off{}}: No{}

def f(a: Answer) -> Answer:
  g(a, L.Box{L.On{}})

def main() -> Answer:
  f(Yes{})
