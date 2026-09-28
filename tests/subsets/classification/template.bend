type Flag is Type:
  Off{}
  On{}

def constant(~x: Flag) -> Flag:
  x

def main() -> Flag:
  constant(On{})
