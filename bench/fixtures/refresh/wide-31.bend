type Tag is Type:
  T0{}
  T1{}
  T2{}
  T3{}
  T4{}
  T5{}
  T6{}
  T7{}
  T8{}
  T9{}
  T10{}
  T11{}
  T12{}
  T13{}
  T14{}
  T15{}
  T16{}
  T17{}
  T18{}
  T19{}
  T20{}
  T21{}
  T22{}
  T23{}
  T24{}
  T25{}
  T26{}
  T27{}
  T28{}
  T29{}
  T30{}

def rotate(x: Tag) -> Tag:
  match x:
    case T0{}: T1{}
    case T1{}: T2{}
    case T2{}: T3{}
    case T3{}: T4{}
    case T4{}: T5{}
    case T5{}: T6{}
    case T6{}: T7{}
    case T7{}: T8{}
    case T8{}: T9{}
    case T9{}: T10{}
    case T10{}: T11{}
    case T11{}: T12{}
    case T12{}: T13{}
    case T13{}: T14{}
    case T14{}: T15{}
    case T15{}: T16{}
    case T16{}: T17{}
    case T17{}: T18{}
    case T18{}: T19{}
    case T19{}: T20{}
    case T20{}: T21{}
    case T21{}: T22{}
    case T22{}: T23{}
    case T23{}: T24{}
    case T24{}: T25{}
    case T25{}: T26{}
    case T26{}: T27{}
    case T27{}: T28{}
    case T28{}: T29{}
    case T29{}: T30{}
    case T30{}: T0{}

def main() -> Tag:
  rotate(T30{})
