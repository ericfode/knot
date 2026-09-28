# The driver.bend source and ordinals shapes: S.bind at Seq<&2,Flag> and Tree, nested, inner lambda capturing x.
type Flag is Data:
  Off{}
  On{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Verdict is Data:
  Rejected{}
  Deferred{}
  Accepted{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

type Tree is Data:
  Leaf{flag: Flag}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def bind(-A: Data, -B: Data, result: Res<Fault,A>, next: A -> Res<Fault,B>) -> Res<Fault,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def tokenize(a: Flag, b: Flag) -> Res<Fault,Seq<&2,Flag>>:
  match a:
    case Off{}: Fail{Invalid{}}
    case On{}: Done{Link{b,Stop{}}}

def parse(tokens: Seq<&2,Flag>) -> Res<Fault,Tree>:
  match tokens:
    case Stop{}: Fail{Unsupported{}}
    case Link{h,t}: Done{Leaf{h}}

def check(tree: Tree) -> Res<Fault,Flag>:
  match tree:
    case Leaf{f}:
      match f:
        case Off{}: Fail{Unsupported{}}
        case On{}: Done{On{}}

def ordinal(f: Flag) -> Res<Fault,Flag>:
  match f:
    case Off{}: Fail{Invalid{}}
    case On{}: Done{On{}}

def ordinals(values: Seq<Flag>) -> Res<Fault,Seq<&2,Flag>>:
  match values:
    case Stop{}: Done{Stop{}}
    case Link{head,tail}:
      bind(Flag,Seq<&2,Flag>,ordinal(head),x =>
        bind(Seq<&2,Flag>,Seq<&2,Flag>,ordinals(tail),xs => Done{Link{x,xs}}))

def verdict(-A: Data, r: Res<Fault,A>) -> Verdict:
  match r:
    case Fail{Invalid{}}: Rejected{}
    case Fail{Unsupported{}}: Deferred{}
    case Done{x}: Accepted{}

def source(a: Flag, b: Flag) -> Verdict:
  verdict(Flag,
    bind(Seq<&2,Flag>,Flag,tokenize(a,b),tokens =>
      bind(Tree,Flag,parse(tokens),tree =>
        check(tree))))

def count(a: Flag, b: Flag, c: Flag) -> Verdict:
  verdict(Seq<&2,Flag>,ordinals(Link{a,Link{b,Link{c,Stop{}}}}))

def main() -> Verdict:
  source(On{},On{})
