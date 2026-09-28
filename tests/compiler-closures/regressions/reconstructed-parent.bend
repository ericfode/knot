type Flag is Data:
  Off{}
  On{}

type Box is Type:
  Box{value: Flag}

def take(box: Box, x: Flag) -> Flag:
  match box:
    case Box{v}: v

def hold(box: Box) -> Flag -> Flag:
  match box:
    case Box{v}: x => take(box, x)

def main() -> Flag:
  hold(Box{On{}})(Off{})
