# Qualified constructors nested in Base generic patterns and as columns of a
# multi-scrutinee match: `Fail{B.Limit{}}` with the ByteOutput package's
# constructors, and `C.Checked{C.Sequence{..},..}` with a local module's.
import Base
import ./core.bend as C
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B

type Outcome is Type:
  Fits{}
  Full{}
  Bad{}
  Many{}
  Single{}
  Plain{}

type Input is Type:
  Small{}
  Large{}
  Wide{}

type Shape is Type:
  Lone{}
  Duo{}
  Nothing{}

type Mode is Data:
  Strict{}
  Loose{}

def written(r: Result<B.Error,B.Builder>) -> Outcome:
  match r:
    case Fail{B.Limit{}}: Full{}
    case Fail{B.InvalidByte{value}}: Bad{}
    case Done{builder}: Fits{}

def values(i: Input) -> List<&2,U32>:
  match i:
    case Small{}: Con{1,Con{2,Nil{}}}
    case Large{}: Con{1,Con{2,Con{3,Con{4,Nil{}}}}}
    case Wide{}: Con{300,Nil{}}

def write(i: Input) -> Outcome:
  written(B.append(B.empty(3),values(i)))

def classify(c: C.Checked, m: Mode) -> Outcome:
  match c m:
    case C.Checked{C.Sequence{Con{first,Con{second,rest}}},C.On{}} Strict{}: Many{}
    case C.Checked{C.Sequence{items},flag} _: Single{}
    case C.Checked{C.Leaf{C.On{}},flag} Loose{}: Many{}
    case C.Checked{C.Leaf{inner},flag} _: Plain{}

def checked(s: Shape) -> C.Checked:
  match s:
    case Lone{}: C.Checked{C.Sequence{Con{C.Leaf{C.On{}},Nil{}}},C.On{}}
    case Duo{}: C.Checked{C.Sequence{Con{C.Leaf{C.Off{}},Con{C.Leaf{C.On{}},Nil{}}}},C.On{}}
    case Nothing{}: C.Checked{C.Leaf{C.On{}},C.Off{}}

def strict(s: Shape) -> Outcome:
  classify(checked(s),Strict{})

def loose(s: Shape) -> Outcome:
  classify(checked(s),Loose{})

def main() -> Outcome:
  write(Large{})
