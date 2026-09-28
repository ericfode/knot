type Flag is Data:
  Off{}
  On{}

type ProofBox is Data:
  ProofBox{-proof: Flag, item: Flag}

def main() -> ProofBox:
  ProofBox{Off{},On{}}
