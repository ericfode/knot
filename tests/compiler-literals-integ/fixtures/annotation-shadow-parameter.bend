# A parameter binds its name in the whole body: the annotation reads the parameter.
type Flag is Data:
  Off{}
  On{}

type Other is Data:
  O1{}

def f(Flag: Other, +x: Other) -> Other:
  y : Flag = x
  x

def main() -> Other:
  f(O1{}, O1{})
