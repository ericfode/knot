type Flag is Data:
  Off{}
  On{}

def one() -> Flag:
  On{}

type W is Type:
  W{value: one}

type Box<-A: Type> is Type:
  Box{value: A}

def main() -> Flag:
  On{}
