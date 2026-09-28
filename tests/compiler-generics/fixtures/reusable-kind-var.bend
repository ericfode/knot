# A +binder at Kind(a) is rejected: the quantity a is not known to be &2.
type Color is Data:
  Red{}
  Green{}
  Blue{}

def keep(a, -A: Kind(a), +x: A) -> A:
  x

def main() -> Color:
  keep(&2, Color, Red{})
