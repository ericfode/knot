type Flag is Data:
  Off{}
  On{}

type Two is Data:
  Two{left: Flag, right: Flag}

def two(left: Flag, right: Flag) -> Two:
  Two{left,right}

def main() -> Two:
  two(On{},Off{})
