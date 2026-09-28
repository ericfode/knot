type Flag is Data:
  Off{}
  On{}

type Void<a> is Kind(a):

def main() -> Flag:
  On{}
