type Flag is Data:
  Off{}
  On{}
type Other is Data:
  Other{}
type Box is Type:
  Box{-ghost: Flag, value: Flag}
def main() -> Box:
  Box{Other{},On{}}
