type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def main() -> Box:
  Box{Off{},On{}}
