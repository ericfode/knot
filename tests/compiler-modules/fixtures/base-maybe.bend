import Base

type Suit is Data:
  Club{}
  Heart{}
  Spade{}

def see(x: Bool) -> Suit:
  match x:
    case False{}: Club{}
    case True{}: Spade{}

def main() -> Suit:
  see(Maybe.is_some(&1, Suit, Maybe.or(&1, Suit, None{}, Some{Heart{}})))
