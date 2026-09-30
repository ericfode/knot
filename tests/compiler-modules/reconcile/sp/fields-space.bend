type Light is Type:
  Dark{}
  Lit{}
type P is Type:
  P{a: Light}

def main() -> Light:
  match_it(P {Lit{}})

def match_it(p: P) -> Light:
  Lit{}
