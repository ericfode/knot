type Flag is Data:
  Off{}
  On{}
def __heap_live() -> Flag:
  On{}
def main() -> Flag:
  __heap_live()
