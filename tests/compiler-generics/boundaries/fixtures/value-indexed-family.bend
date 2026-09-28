type Flag is Data:
  Off{}
  On{}

type At<-x: Flag> is Data:
  Marker{}

def main() -> Flag:
  On{}
