type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def main() -> Flag:
  -Alias : Type = Flag
  On{}
