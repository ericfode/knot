import Base

type Suit is Data:
  Club{}
  Heart{}
  Spade{}

def top(m: Maybe<Suit>) -> Suit:
  match m:
    case None{}: Club{}
    case Some{s}: s

def main() -> Suit:
  top(List.head(&1, Suit, List.reverse(&1, Suit, [Club{}, Heart{}, Spade{}])))
