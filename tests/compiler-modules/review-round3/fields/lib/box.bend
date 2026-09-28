type Flag is Type:
  No{}
  Yes{}

type Box is Type:
  Box{v: Flag}

def open(b: Box) -> Flag:
  match b:
    case Box{Off}: Off
