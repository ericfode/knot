type Flag is Data:
  Off{}
  On{}

type Bit<a> is Kind(a):
  Zero{}
  One{}

type Hold is Type:
  Hold{bit: Bit}

def main() -> Flag:
  On{}
