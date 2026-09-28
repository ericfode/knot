type Flag is Data:
  Off{}
  On{}

type Box is Data:
  Box{item: Flag}

def main() -> Box:
  Box{On{}}
