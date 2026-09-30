type Flag is Data:
  Off{}
  On{}

type Answer is Data:
  No{}
  Yes{}

def pick(Flag: Flag, value: Flag) -> Answer:
  Yes{}

def main() -> Answer:
  pick(On{},Off{})
