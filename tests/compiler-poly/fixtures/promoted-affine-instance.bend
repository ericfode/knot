# A + binder promotes an &1 instance: bound => +fs => at Seq<&1,Flag>, so once could read fs twice.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def bind(-A: Data, -B: Data, result: Res<Fault,A>, next: A -> Res<Fault,B>) -> Res<Fault,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def signature(f: Flag) -> Res<Fault,Seq<&2,Flag>>:
  match f:
    case Off{}: Fail{Invalid{}}
    case On{}: Done{Link{On{},Link{Off{},Stop{}}}}

def first(xs: Seq<&2,Flag>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}: h

def second(xs: Seq<&2,Flag>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}: first(t)

def first_once(xs: Seq<&1,Flag>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}: h

def both(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}: Off{}
    case On{}: y

def arity(g: Flag, xs: Seq<&2,Flag>) -> Res<Fault,Flag>:
  match g:
    case Off{}: Fail{Unsupported{}}
    case On{}: Done{first(xs)}

def paint(x: Flag) -> Color:
  match x:
    case Off{}: Red{}
    case On{}: Blue{}

def scope(g: Flag, next: Flag -> Seq<&2,Flag> -> Res<Fault,Color>) -> Res<Fault,Color>:
  match g:
    case Off{}: next(Off{},Stop{})
    case On{}: next(On{},Link{On{},Link{On{},Stop{}}})

def scope_once(g: Flag, next: Flag -> Seq<&1,Flag> -> Res<Fault,Color>) -> Res<Fault,Color>:
  match g:
    case Off{}: next(Off{},Stop{})
    case On{}: next(On{},Link{On{},Stop{}})

def color_of(r: Res<Fault,Color>) -> Color:
  match r:
    case Fail{e}: Red{}
    case Done{c}: c

def flag_of(r: Res<Fault,Flag>) -> Flag:
  match r:
    case Fail{e}: On{}
    case Done{x}: x

def params(f: Flag, g: Flag) -> Flag:
  flag_of(bind(Seq<&2,Flag>,Flag,signature(f),+ps =>
    bind(Flag,Flag,arity(g,ps),x => Done{both(x,second(ps))})))

def fields(g: Flag) -> Color:
  color_of(scope(g,bound => +fs => Done{paint(both(both(bound,first(fs)),second(fs)))}))

def once(g: Flag) -> Color:
  color_of(scope_once(g,bound => +fs => Done{paint(both(first_once(fs),both(first_once(fs),bound)))}))

def main() -> Flag:
  params(On{},On{})
