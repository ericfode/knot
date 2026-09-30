type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def wrap(x: Flag) -> Box<Flag>
  :
  Box{x}

def main() -> Flag:
  On{}
