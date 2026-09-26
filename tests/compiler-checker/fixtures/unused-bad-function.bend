type Flag is Type:
  Off{}
  On{}
type Other is Type:
  OtherTag{}
def bad() -> Flag:
  OtherTag{}
def main() -> Flag:
  On{}
