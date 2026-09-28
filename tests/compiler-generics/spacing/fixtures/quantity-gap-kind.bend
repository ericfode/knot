type Flag is Data:
  Off{}
  On{}

type Both is Kind(& 2):
  Both{fst: Flag, snd: Flag}

def main() -> Flag:
  On{}
