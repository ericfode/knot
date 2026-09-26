type Flag is Type:
  Off{}
  On{}

type Other is Type:
  OtherTag{}

def identity(x: Flag) -> Flag:
  x

def shadow(x: Flag) -> Flag:
  x : Other = OtherTag{}
  identity(x)

def main() -> Flag:
  shadow(Off{})
