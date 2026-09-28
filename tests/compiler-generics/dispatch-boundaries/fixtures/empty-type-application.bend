type Flag is Data:
  Off{}
  On{}

type Holder is Type:
  Holder{value: Flag<>}

def main() -> Flag:
  On{}
