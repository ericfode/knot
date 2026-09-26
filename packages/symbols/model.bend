import Base
import ./protocol.bend as P

# Independent abstract state: no Vec, Map, Symbols or hash dependency.
type Model is Data:
  Names{limit: U32, entries: List<&2,String>}

def length(xs: List<&2,String>) -> U32:
  match xs:
    case Nil{}: 0
    case Con{h,t}: U32.add(1,length(t))

def search_step(index: U32, equal: Bool, later: Maybe<&2,U32>) -> Maybe<&2,U32>:
  match equal:
    case True{}: Some{index}
    case False{}: later

def search(xs: List<&2,String>, +name: String, +index: U32) -> Maybe<&2,U32>:
  match xs:
    case Nil{}: None{}
    case Con{head,tail}: search_step(index,String.eq(head,name),search(tail,name,U32.add(index,1)))

def append(xs: List<&2,String>, name: String) -> List<&2,String>:
  match xs:
    case Nil{}: Con{name,Nil{}}
    case Con{h,t}: Con{h,append(t,name)}

def at(xs: List<&2,String>, i: Nat) -> P.Reply:
  match xs i:
    case Nil{} _: P.Invalid{}
    case Con{h,t} 0n: P.Name{h}
    case Con{h,t} 1n+p: at(t,p)

def find_reply(x: Maybe<&2,U32>) -> P.Reply:
  match x:
    case None{}: P.Missing{}
    case Some{i}: P.Id{i}

def insert_if(limit: U32, xs: List<&2,String>, name: String, n: U32, room: Bool) -> Model & P.Reply:
  match room:
    case True{}: (Names{limit,append(xs,name)},P.Id{n})
    case False{}: (Names{limit,xs},P.Full{})

def insert_found(+limit: U32, +xs: List<&2,String>, name: String, found: Maybe<&2,U32>) -> Model & P.Reply:
  match found:
    case Some{i}: (Names{limit,xs},P.Id{i})
    case None{}: insert_if(limit,xs,name,length(xs),U32.is_lt(length(xs),limit))

def step(m: Model, command: P.Command) -> Model & P.Reply:
  match m:
    case Names{+limit,+xs}:
      match command:
        case P.Intern{+name}: insert_found(limit,xs,name,search(xs,name,0))
        case P.Find{name}: (Names{limit,xs},find_reply(search(xs,name,0)))
        case P.Resolve{i}: (Names{limit,xs},at(xs,U32.to_nat(i)))
        case P.Length{}: (Names{limit,xs},P.Number{length(xs)})
        case P.Limit{}: (Names{limit,xs},P.Number{limit})

def trace_next(next: Model -> List<&2,P.Observation>, pair: Model & P.Reply) -> List<&2,P.Observation>:
  (m,r) = pair
  match m:
    case Names{+limit,+xs}:
      Con{P.Observed{r,length(xs),limit,xs},next(Names{limit,xs})}

def trace(commands: List<&2,P.Command>, m: Model) -> List<&2,P.Observation>:
  match commands:
    case Nil{}: Nil{}
    case Con{c,cs}: trace_next(trace(cs),step(m,c))

def run(commands: List<&2,P.Command>, limit: U32) -> List<&2,P.Observation>:
  trace(commands,Names{U32.min(limit,16777216),Nil{}})
