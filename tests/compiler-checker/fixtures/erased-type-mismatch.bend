type Flag is Type:
  Off{}
  On{}
type Other is Type:
  OtherTag{}
def take(-x: Flag,y: Flag) -> Flag:
  y
def main() -> Flag:
  take(OtherTag{},On{})
