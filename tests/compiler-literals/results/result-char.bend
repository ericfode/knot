# A Char result displays as the seed's quoted literal: named escapes, the
# apostrophe escaped, \u{..} for controls, DEL, surrogates and codes past
# U+10FFFF, and every other code as raw UTF-8.
import Base

type Sample is Type:
  Nul{}
  Start{}
  Letter{}
  Apostrophe{}
  Quotation{}
  Backslash{}
  Newline{}
  Tab{}
  CarriageReturn{}
  UnitSeparator{}
  Space{}
  Tilde{}
  Delete{}
  FirstC1{}
  LastC1{}
  Latin{}
  BeforeSurrogates{}
  HighSurrogate{}
  LowSurrogate{}
  AfterSurrogates{}
  Noncharacter{}
  Emoji{}
  LastScalar{}
  PastScalar{}
  AllOnes{}
  Sum{}
  FromCode{}

def sample(s: Sample) -> Char:
  match s:
    case Nul{}: '\0'
    case Start{}: '\u{1}'
    case Letter{}: 'a'
    case Apostrophe{}: '\''
    case Quotation{}: '"'
    case Backslash{}: '\\'
    case Newline{}: '\n'
    case Tab{}: '\t'
    case CarriageReturn{}: '\r'
    case UnitSeparator{}: '\u{1f}'
    case Space{}: ' '
    case Tilde{}: '~'
    case Delete{}: '\u{7f}'
    case FirstC1{}: '\u{80}'
    case LastC1{}: '\u{9f}'
    case Latin{}: '\u{e9}'
    case BeforeSurrogates{}: '\u{d7ff}'
    case HighSurrogate{}: '\u{d83d}'
    case LowSurrogate{}: '\u{dfff}'
    case AfterSurrogates{}: '\u{e000}'
    case Noncharacter{}: '\u{fffe}'
    case Emoji{}: '\u{1F600}'
    case LastScalar{}: '\u{10ffff}'
    case PastScalar{}: '\u{110000}'
    case AllOnes{}: '\u{FFFFFFFF}'
    case Sum{}: Char.from_u32(U32.add(64, 1))
    case FromCode{}: Char.from_u32(10)

def main() -> Char:
  sample(Start{})
