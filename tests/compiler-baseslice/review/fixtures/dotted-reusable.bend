type Flag is Data:
  Off{}
  On{}

type Answer is Data:
  No{}
  Yes{}

def main() -> Flag:
  +Flag.value : Flag = On{}
  Flag.value
