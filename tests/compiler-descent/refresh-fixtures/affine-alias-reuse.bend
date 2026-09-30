type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
type A is Type:
  AZ{}
  AS{pred: A}
def keep(discarded: A, result: Flag) -> Flag:
  result
def drain(n: A) -> Flag:
  match n:
    case AZ{}: On{}
    case AS{x}:
      copy : A = x
      keep(copy,drain(copy))
def main() -> Flag:
  drain(AZ{})
