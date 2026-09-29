import Base

type Answer is Type:
  No{}
  Yes{}

type Probe is Type:
  OffsetZero{}
  OffsetOne{}
  OffsetTwo{}
  OffsetThree{}
  Less{}
  Equal{}
  Greater{}
  Mask{}
  MaskMiss{}
  Reverse{}
  ReverseUnicode{}
  ReverseEmpty{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def offset(n: Nat) -> Bool:
  match n:
    case 0n: False{}
    case 1n+ +n: Nat.is_eq(Nat.add(n, n), 2n)

def observe(p: Probe) -> Answer:
  match p:
    case OffsetZero{}: verdict(offset(0n))
    case OffsetOne{}: verdict(offset(1n))
    case OffsetTwo{}: verdict(offset(2n))
    case OffsetThree{}: verdict(offset(3n))
    case Less{}: verdict(Nat.is_le(2n, 3n))
    case Equal{}: verdict(Nat.is_le(3n, 3n))
    case Greater{}: verdict(Nat.is_le(4n, 3n))
    case Mask{}: verdict(U32.is_eq(U32.and(4294967295, 2147483648), 2147483648))
    case MaskMiss{}: verdict(U32.is_eq(U32.and(10, 5), 15))
    case Reverse{}: verdict(String.eq(String.reverse("abc"), "cba"))
    case ReverseUnicode{}: verdict(String.eq(String.reverse("\u{d83d}\u{de00}"), "\u{de00}\u{d83d}"))
    case ReverseEmpty{}: verdict(String.eq(String.reverse(""), ""))

def main() -> Answer:
  observe(OffsetTwo{})
