type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  Pair{left: Flag, right: Flag}

def main() -> Pair:
  Pair{Off{},On{}}
