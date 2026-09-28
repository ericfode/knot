type Box -A: Type> is Type:
  Box{value: A}

type Flag is Type:
  Off{}
  On{}

def main() -> Box<Flag>:
  Box{On{}}
