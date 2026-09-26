type Flag is Data:
  Off{}
  On{}
type Payload is Type:
  Payload{}
type Box is Data:
  Box{-ghost: Payload, value: Flag, +shared: Flag,}
def main() -> Flag:
  On{}
