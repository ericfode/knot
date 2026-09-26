type Flag is Type:
  Off{}
  On{}
def take(-x: Flag,y: Flag) -> Flag:
  y
def main() -> Flag:
  take(missing,On{})
