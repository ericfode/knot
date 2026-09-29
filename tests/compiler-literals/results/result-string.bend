# A String result displays as the seed's quoted literal, code by code as a
# Char does, except that the double quote is escaped instead of the apostrophe.
# Escaped surrogates stay two codes, literal or computed.
import Base

type Sample is Type:
  Blank{}
  Nul{}
  Greeting{}
  Escapes{}
  Quotes{}
  Separators{}
  Controls{}
  Boundaries{}
  Surrogates{}
  JoinedSurrogates{}
  ReversedSurrogates{}
  PastScalar{}
  Emoji{}
  Shown{}
  NatShown{}
  Appended{}

def sample(s: Sample) -> String:
  match s:
    case Blank{}: ""
    case Nul{}: "\0"
    case Greeting{}: "hi"
    case Escapes{}: "\0\t\n\r\\"
    case Quotes{}: "'\""
    case Separators{}: "a, b{}"
    case Controls{}: "\u{1}\u{1f}\u{7f}"
    case Boundaries{}: "\u{80}\u{9f}\u{fffe}\u{10ffff}"
    case Surrogates{}: "\u{d83d}\u{de00}"
    case JoinedSurrogates{}: String.append("\u{d83d}", "\u{de00}")
    case ReversedSurrogates{}: String.reverse("\u{de00}\u{d83d}")
    case PastScalar{}: "a\u{110000}"
    case Emoji{}: "\u{1f600}"
    case Shown{}: U32.show(300)
    case NatShown{}: Nat.show(12n)
    case Appended{}: String.append("a\n", "b")

def main() -> String:
  sample(Nul{})
