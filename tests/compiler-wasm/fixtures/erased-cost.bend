type Flag is Type:
  Off{}
  On{}
def identity(x: Flag) -> Flag:
  x
def constant(-x: Flag) -> Flag:
  On{}
def main() -> Flag:
  -unused = identity(identity(identity(Off{})))
  constant(identity(identity(identity(Off{}))))
