# Twin of fuel-continuation: the continuation reuses a non-reusable predecessor.
import Base

type Level is Type:
  Starved{}
  Rejected{}
  Count{}

type Budget is Type:
  B0{}
  B3{}
  B9{}

type Text is Type:
  Plain{}
  Marked{}

type Tally is Data:
  Zero3{}
  One3{}
  Two3{}

type Step is Data:
  Stuck{}
  Next{tally: Tally}

def bump(t: Tally) -> Tally:
  match t:
    case Zero3{}: One3{}
    case One3{}: Two3{}
    case Two3{}: Zero3{}

def decide(stop: Bool, tally: Tally) -> Step:
  match stop:
    case True{}: Stuck{}
    case False{}: Next{bump(tally)}

def step(c: Char, tally: Tally) -> Step:
  decide(Char.is_eq(c,'!'),tally)

def bind(s: Step, next: Tally -> Level) -> Level:
  match s:
    case Stuck{}: Rejected{}
    case Next{tally}: next(tally)

def scan(fuel: Nat, input: String, tally: Tally) -> Level:
  match fuel input:
    case _ SNil{}: Count{}
    case 0n SCon{c,tail}: Starved{}
    case 1n+n SCon{c,tail}: bind(step(c,tally),next => scan(n,tail,next))

def then(first: Level, next: Level -> Level) -> Level:
  match first:
    case Starved{}: Starved{}
    case Rejected{}: Rejected{}
    case Count{}: next(Count{})

def twice(fuel: Nat, input: String) -> Level:
  match fuel:
    case 0n: Starved{}
    case 1n+ n: then(scan(n,input,Zero3{}),value => scan(n,"x",Zero3{}))

def budget(b: Budget) -> Nat:
  match b:
    case B0{}: 0n
    case B3{}: 3n
    case B9{}: 9n

def text(t: Text) -> String:
  match t:
    case Plain{}: "abcd"
    case Marked{}: "ab!d"

def probe(b: Budget, t: Text) -> Level:
  twice(budget(b),text(t))

def main() -> Level:
  probe(B9{},Plain{})
