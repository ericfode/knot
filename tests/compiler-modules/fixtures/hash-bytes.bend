import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B

type Case is Type:
  Fits{}
  Wide{}
  Long{}

type Verdict is Type:
  Accepted{}
  BadByte{}
  Full{}

def why(e: B.Error) -> Verdict:
  match e:
    case B.InvalidByte{v}: BadByte{}
    case B.Limit{}: Full{}

def judge(r: Result<B.Error,B.Builder>) -> Verdict:
  match r:
    case Fail{e}: why(e)
    case Done{b}: Accepted{}

def probe(c: Case) -> Verdict:
  match c:
    case Fits{}: judge(B.fragment(4, [0, 97, 255]))
    case Wide{}: judge(B.fragment(4, [0, 256]))
    case Long{}: judge(B.fragment(2, [1, 2, 3]))

def main() -> Verdict:
  probe(Fits{})
