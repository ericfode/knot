import Base

type Part is Data:
  Blank{}
  Ab{}
  Cee{}

type Spelling is Data:
  Vacant{}
  AbOnly{}
  CeeOnly{}
  AbCee{}
  CeeAb{}
  AbAb{}
  CeeCee{}
  Unknown{}

def part(p: Part) -> String:
  match p:
    case Blank{}: ""
    case Ab{}: "ab"
    case Cee{}: "c"

def spelling(+s: String) -> Spelling:
  Bool.pick(Spelling, String.eq(s, ""), Vacant{},
  Bool.pick(Spelling, String.eq(s, "ab"), AbOnly{},
  Bool.pick(Spelling, String.eq(s, "c"), CeeOnly{},
  Bool.pick(Spelling, String.eq(s, "abc"), AbCee{},
  Bool.pick(Spelling, String.eq(s, "cab"), CeeAb{},
  Bool.pick(Spelling, String.eq(s, "abab"), AbAb{},
  Bool.pick(Spelling, String.eq(s, "cc"), CeeCee{}, Unknown{})))))))

# The left argument comes first: String.append is an intrinsic on one seed lane.
def joined(l: Part, r: Part) -> Spelling:
  spelling(String.append(part(l), part(r)))

def main() -> Spelling:
  joined(Cee{}, Ab{})
