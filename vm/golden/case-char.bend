import Base

type Flag is Data:
  Off{}
  On{}

def vowel(c: Char) -> Flag:
  match c:
    case 'a': On{}
    case 'e': On{}
    case _: Off{}

def main() -> Flag:
  vowel('e')
