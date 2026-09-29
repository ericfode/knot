# The rule holds inside an imported module too: there the type is spelled `promoted-type-module.Flag`
# to the book and `Flag` to its own bodies.
import ./promoted-type-module/lib.bend as L

type Answer is Type:
  No{}
  Yes{}

def main() -> Answer:
  Yes{}
