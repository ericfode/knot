type Flag is Data:
  Off{}
  On{}

def before() -> Flag:
  -hidden : Flag = after()
  On{}
def after() -> Flag:
  Off{}
def main() -> Flag:
  before()
