type Flag is Data:
  Off{}
  On{}

type Answer is Data:
  No{}
  Yes{}

def pick(flag: Flag) -> Flag:
  flag

def main() -> Flag:
  pick(On{})
