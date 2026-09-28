# Twin of qualified-fields: a field names a type its module does not declare.
import Base
import ./flags.bend as F
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B

type Answer is Type:
  No{}
  Yes{}

type Batch is Data:
  Batch{flags: List<&2,F.Flag>, mode: F.Modes, out: B.Builder}

type Plan is Type:
  Quiet{}
  Loud{}
  Mixed{}

def any(flags: List<&2,F.Flag>) -> Answer:
  match flags:
    case Nil{}: No{}
    case Con{F.On{},rest}: Yes{}
    case Con{F.Off{},rest}: any(rest)

def batch(p: Plan) -> Batch:
  match p:
    case Quiet{}: Batch{Con{F.Off{},Nil{}},F.Fast{},B.empty(4)}
    case Loud{}: Batch{Con{F.Off{},Con{F.On{},Nil{}}},F.Safe{},B.empty(4)}
    case Mixed{}: Batch{Nil{},F.Safe{},B.empty(0)}

def raised(b: Batch) -> Answer:
  match b:
    case Batch{flags,mode,out}: any(flags)

def careful(b: Batch) -> Answer:
  match b:
    case Batch{flags,F.Safe{},out}: Yes{}
    case Batch{flags,F.Fast{},out}: No{}

def room(closed: Bool) -> Answer:
  match closed:
    case True{}: No{}
    case False{}: Yes{}

def roomy(b: Batch) -> Answer:
  match b:
    case Batch{flags,mode,out}: room(U32.is_eq(B.limit(out),0))

def flagged(p: Plan) -> Answer:
  raised(batch(p))

def safe(p: Plan) -> Answer:
  careful(batch(p))

def spare(p: Plan) -> Answer:
  roomy(batch(p))

def main() -> Answer:
  flagged(Loud{})
