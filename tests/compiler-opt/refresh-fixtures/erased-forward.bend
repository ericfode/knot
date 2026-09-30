type Flag is Data:
  Off{}
  On{}

def keep(-a: Flag, b: Flag) -> Flag:
  b
def before() -> Flag:
  keep(after(),On{})
def after() -> Flag:
  Off{}
def main() -> Flag:
  before()
