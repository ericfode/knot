type Flag is Data:
  Off{}
  On{}

type Answer is Data:
  No{}
  Yes{}

def pick(Flag: Flag) -> Answer:
  value : Flag = On{}
  Yes{}

def main() -> Answer:
  pick(On{})
