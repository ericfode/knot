type F is Data:
  F0{}
  F1{}

def id(a: F) - > F:
  a

def main() -> F:
  id(F1{})
