type Flag is Data:
  Off{}
  On{}

type ProofBox is Data:
  ProofBox{-proof: Flag, item: Flag}

def get(b: ProofBox) -> Flag:
  match b:
    case ProofBox{p,x}: x

def main() -> Flag:
  get(ProofBox{Off{},On{}})
