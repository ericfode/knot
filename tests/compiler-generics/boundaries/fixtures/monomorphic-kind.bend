type Flag is Kind(&2):
  Off{}
  On{}

def round(x: Flag) -> Flag:
  match x:
    case Off{}:
      On{}
    case On{}:
      Off{}

def main() -> Flag:
  round(On{})
