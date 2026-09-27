import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import 0xc409b77d3230ca33374caf6b0993f0cb/byte_model.bend as M

type Verdict is Type:
  Kept{}
  Refused{}

def see(r: Result<B.Error, List<&2,U32> & U32>) -> Verdict:
  match r:
    case Fail{e}: Refused{}
    case Done{p}: Kept{}

def main() -> Verdict:
  see(M.observe(B.fragment(4, [7, 8])))
