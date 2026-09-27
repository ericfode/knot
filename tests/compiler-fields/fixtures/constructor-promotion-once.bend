type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{+value: Flag}
def box(x: Flag) -> Box:
  Box{x}
def main() -> Box:
  box(On{})
