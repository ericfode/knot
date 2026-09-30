type Flag is Data:
  Off{}
  On{}

type Answer is Data:
  No{}
  Yes{}

type Holder is Data:
  Held{flag: Flag, value: Flag}

def main() -> Answer:
  Yes{}
