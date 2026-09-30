# two rows by 13 columns.
type Flag is Data:
  Off{}
  On{}

def all(x0: Flag, x1: Flag, x2: Flag, x3: Flag, x4: Flag, x5: Flag, x6: Flag, x7: Flag, x8: Flag, x9: Flag, x10: Flag, x11: Flag, x12: Flag) -> Flag:
  match x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 x10 x11 x12:
    case On{} On{} On{} On{} On{} On{} On{} On{} On{} On{} On{} On{} On{}: Off{}
    case _ _ _ _ _ _ _ _ _ _ _ _ _: On{}

def main() -> Flag:
  all(On{}, On{}, On{}, On{}, On{}, On{}, On{}, On{}, On{}, On{}, On{}, On{}, On{})
