# Both columns bind v; the later binder shadows the earlier one, which is dropped.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def second(a: Flag, b: Color) -> Color:
  match a b:
    case v v: v

def main() -> Color:
  second(On{}, Green{})
