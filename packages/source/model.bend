import Base
import ./types.bend as T

# Independent sequential specification: no Vec, main, binary search, or line index.
def get(text: String, pos: Nat) -> Result<T.Error,Char>:
  match text pos:
    case SNil{} 0n: Fail{T.Bounds{}}
    case SNil{} 1n+p: Fail{T.Bounds{}}
    case SCon{c,t} 0n: Done{c}
    case SCon{c,t} 1n+p: get(t,p)

def advance(line: U32, col: U32, lf: Bool) -> T.Location:
  match lf:
    case False{}: T.Location{line,(col + 1 : U32)}
    case True{}: T.Location{(line + 1 : U32),0}

def locate_go(text: String, pos: Nat, loc: T.Location) -> Result<T.Error,T.Location>:
  match text pos loc:
    case SNil{} 0n T.Location{l,c}: Done{T.Location{l,c}}
    case SNil{} 1n+p T.Location{l,c}: Fail{T.Bounds{}}
    case SCon{h,t} 0n T.Location{l,c}: Done{T.Location{l,c}}
    case SCon{h,t} 1n+p T.Location{l,c}: locate_go(t,p,advance(l,c,Char.is_eq(h,'\n')))

def locate(text: String, pos: U32) -> Result<T.Error,T.Location>:
  locate_go(text,U32.to_nat(pos),T.Location{0,0})

def slice(text: String, start: Nat, size: Nat) -> String:
  String.take(String.drop(text,start),size)

# Reverse lookup enumerates positions from a freshly scanned string. It cannot
# reproduce the implementation's line-index arithmetic by accident.
def location_eq(a: T.Location, b: T.Location) -> Bool:
  match a b:
    case T.Location{l,c} T.Location{l2,c2}: Bool.and(U32.is_eq(l,l2),U32.is_eq(c,c2))

def choose_offset(pos: U32, later: Result<T.Error,U32>, same: Bool) -> Result<T.Error,U32>:
  match same:
    case True{}: Done{pos}
    case False{}: later

def next(loc: T.Location, c: Char) -> T.Location:
  match loc:
    case T.Location{l,col}: advance(l,col,Char.is_eq(c,'\n'))


def offset_go(text: String, +wanted: T.Location, +loc: T.Location, +pos: U32) -> Result<T.Error,U32>:
  match text:
    case SNil{}: choose_offset(pos,Fail{T.Bounds{}},location_eq(wanted,loc))
    case SCon{h,t}:
      choose_offset(pos,offset_go(t,wanted,next(loc,h),(pos + 1 : U32)),location_eq(wanted,loc))


def offset(text: String, loc: T.Location) -> Result<T.Error,U32>:
  offset_go(text,loc,T.Location{0,0},0)

def line_count(text: String) -> U32:
  match text:
    case SNil{}: 1
    case SCon{h,t}: (line_count(t) + Bool.to_u32(Char.is_eq(h,'\n')) : U32)
