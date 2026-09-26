type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{f: Flag -> Flag}
def main() -> Flag:
  On{}
