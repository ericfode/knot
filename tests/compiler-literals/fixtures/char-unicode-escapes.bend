# \u{..} escapes: 1 to 8 hex digits, either case, any U32 value (even past U+10FFFF).
import Base

type Answer is Type:
  No{}
  Yes{}

type Point is Data:
  Letter{}
  UpperU{}
  Padded{}
  Emoji{}
  EmojiLower{}
  Surrogate{}
  PastUnicode{}
  AllOnes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def char(p: Point) -> Char:
  match p:
    case Letter{}: '\u{41}'
    case UpperU{}: '\U{41}'
    case Padded{}: '\u{00000041}'
    case Emoji{}: '\u{1F600}'
    case EmojiLower{}: '\u{1f600}'
    case Surrogate{}: '\u{D800}'
    case PastUnicode{}: '\u{110000}'
    case AllOnes{}: '\u{FFFFFFFF}'

def code(p: Point) -> U32:
  match p:
    case Letter{}: 65
    case UpperU{}: 65
    case Padded{}: 65
    case Emoji{}: 128512
    case EmojiLower{}: 128512
    case Surrogate{}: 55296
    case PastUnicode{}: 1114112
    case AllOnes{}: 4294967295

def exact(+p: Point) -> Answer:
  verdict(U32.is_eq(Char.to_u32(char(p)), code(p)))

def is_a(p: Point) -> Answer:
  verdict(Char.is_eq(char(p), 'A'))

def main() -> Answer:
  exact(Emoji{})
