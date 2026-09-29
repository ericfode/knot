type Flag is Data:
  Off{}
  On{}

type Box is Data:
  Box{item: Flag}

def wrap() -> Box:
  x : Flag = On{}
  Box{x}

def main() -> Box:
  wrap()
