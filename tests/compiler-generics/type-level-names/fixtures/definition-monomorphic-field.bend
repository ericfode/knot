type Flag is Data:
  Off{}
  On{}

def T() -> Type:
  Flag

type W is Type:
  W{value: T}

def unw(w: W) -> Flag:
  match w:
    case W{v}:
      v

def main() -> Flag:
  unw(W{On{}})
