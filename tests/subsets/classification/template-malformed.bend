type Flag is Type:
  Off{}
  On{}

def constant(~: Flag) -> Flag:
  x

def main() -> Flag:
  constant(On{})
