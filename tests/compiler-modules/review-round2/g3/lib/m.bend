type Flag is Type:
  Off{}
  On{}

type Box is Type:
  Box{v: Flag}

def open(b: Box) -> Flag:
  match b:
    case Box{Off}: Off
