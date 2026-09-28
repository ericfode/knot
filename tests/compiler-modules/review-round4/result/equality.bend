type Light is Type:
  Dark{}
  Lit{}

def same() -> {Lit{} == Lit{} : Light}:
  {==}

def main() -> Light:
  Lit{}
