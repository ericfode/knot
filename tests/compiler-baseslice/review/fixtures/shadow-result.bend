type Flag is Data:
  Off{}
  On{}

type Answer is Data:
  No{}
  Yes{}

def pick(Flag: Flag) -> Flag:
  Flag

def main() -> Flag:
  pick(On{})
