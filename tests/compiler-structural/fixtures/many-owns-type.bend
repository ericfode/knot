type Flag is Data:
  Off{}
  On{}
type Payload is Type:
  Payload{}
type Box is Type:
  Box{+x: Payload}
def main() -> Flag:
  On{}
