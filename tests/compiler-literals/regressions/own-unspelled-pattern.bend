# N declares no Zero, so `0n` spells no constructor of N.
type Answer is Type:
  No{}
  Yes{}

type N is Data:
  Z{}
  S{pred: N}

def zero(n: N) -> Answer:
  match n:
    case 0n: Yes{}
    case _: No{}

def main() -> Answer:
  zero(Z{})
