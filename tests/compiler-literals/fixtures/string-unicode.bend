# Strings are Unicode scalar sequences: an escaped surrogate pair is two Chars.
import Base

type Answer is Type:
  No{}
  Yes{}

type Case is Type:
  Scalar{}
  Lone{}
  Accent{}
  Surrogates{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def check(c: Case) -> Answer:
  match c:
    case Scalar{}: verdict(Nat.is_eq(String.length("\u{1F600}"), 1n))
    case Lone{}: verdict(Nat.is_eq(String.length("\u{D800}x"), 2n))
    case Accent{}: verdict(String.eq("\u{e9}", SCon{Chr{233}, SNil{}}))
    case Surrogates{}: verdict(String.eq("\u{1F600}", "\u{d83d}\u{de00}"))

def main() -> Answer:
  check(Surrogates{})
