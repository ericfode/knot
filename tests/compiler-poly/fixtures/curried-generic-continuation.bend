# The patterns.add and check.arm_scope shapes: curried continuations over Seq<&2,Flag>, one captured in a choose thunk.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Fault is Data:
  Invalid{}
  Exhausted{}

type Unit is Data:
  Unit{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

type Scope is Data:
  Scope{live: Flag, bound: Seq<&2,Flag>}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def choose(-A: Type, condition: Flag, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case On{}: yes(Unit{})
    case Off{}: no(Unit{})

def exhausted(-A: Type) -> Res<Fault,A>:
  Fail{Exhausted{}}

def open(scope: Scope, next: Flag -> Seq<&2,Flag> -> Res<Fault,Color>) -> Res<Fault,Color>:
  match scope:
    case Scope{live,bound}: next(live,bound)

def full(bound: Seq<&2,Flag>) -> Flag:
  match bound:
    case Stop{}: Off{}
    case Link{h,t}: On{}

def add(scope: Scope, +extra: Flag, next: Scope -> Flag -> Res<Fault,Color>) -> Res<Fault,Color>:
  match scope:
    case Scope{+live,+bound}:
      choose(Res<Fault,Color>,full(bound),u => exhausted(Color),u =>
        +grown : Seq<&2,Flag> = Link{extra,bound}
        next(Scope{live,grown},extra))

def judge(live: Flag, bound: Seq<&2,Flag>) -> Res<Fault,Color>:
  match live:
    case Off{}: Fail{Invalid{}}
    case On{}:
      match bound:
        case Stop{}: Done{Red{}}
        case Link{h,t}: Done{Blue{}}

def judge_with(extra: Flag, live: Flag, bound: Seq<&2,Flag>) -> Res<Fault,Color>:
  match extra:
    case Off{}: judge(live,bound)
    case On{}: judge(live,Link{On{},bound})

def verdict(r: Res<Fault,Color>) -> Color:
  match r:
    case Fail{e}: Red{}
    case Done{c}: c

def fault(r: Res<Fault,Color>) -> Fault:
  match r:
    case Fail{e}: e
    case Done{c}: Invalid{}

def empty(live: Flag) -> Scope:
  Scope{live,Stop{}}

def arm(live: Flag, extra: Flag) -> Color:
  verdict(open(empty(live),l => b => judge(l,Link{extra,b})))

def partial(live: Flag, extra: Flag) -> Color:
  verdict(open(empty(live),judge_with(extra)))

def added(live: Flag, extra: Flag) -> Color:
  verdict(add(empty(live),extra,s => x => open(s,judge_with(x))))

def grow(extra: Flag) -> Seq<&2,Flag>:
  match extra:
    case Off{}: Stop{}
    case On{}: Link{On{},Stop{}}

def grown(live: Flag, extra: Flag) -> Fault:
  fault(add(Scope{live,grow(extra)},On{},s => x => open(s,judge_with(x))))

def main() -> Color:
  added(On{},On{})
