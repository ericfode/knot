# The other order of the same offsets: the pattern sits later in main than the imported constructors.
import ./qualified-order-lib-last/lib.bend as L

type Answer is Type:
  No{}
  Yes{}

# 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
def g(a: Answer, b: L.Box) -> Answer:
  match b:
    case L.Box{L.On{}}: a
    case L.Box{L.Off{}}: No{}

def f(a: Answer) -> Answer:
  g(a, L.Box{L.On{}})

def main() -> Answer:
  f(Yes{})
