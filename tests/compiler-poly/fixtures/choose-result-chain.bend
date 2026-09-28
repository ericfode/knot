# The lex.bend normal shape: S.choose chained four deep at Res<Fault,State>, thunks capturing + locals.
type Flag is Data:
  Off{}
  On{}

type Glyph is Data:
  Newline{}
  Space{}
  Hash{}
  Tab{}
  Letter{}

type Mode is Data:
  Blank{}
  Comment{}
  Word{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Report is Data:
  Blanked{}
  Commented{}
  Worded{}
  Refused{}
  Deferred{}

type Unit is Data:
  Unit{}

type State is Data:
  State{mode: Mode, line: Flag}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def choose(-A: Type, condition: Flag, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case On{}: yes(Unit{})
    case Off{}: no(Unit{})

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def newline(g: Glyph) -> Flag:
  match g:
    case Newline{}: On{}
    case _: Off{}

def space(g: Glyph) -> Flag:
  match g:
    case Space{}: On{}
    case _: Off{}

def hash(g: Glyph) -> Flag:
  match g:
    case Hash{}: On{}
    case _: Off{}

def tab(g: Glyph) -> Flag:
  match g:
    case Tab{}: On{}
    case _: Off{}

def normal(+g: Glyph, +line: Flag) -> Res<Fault,State>:
  +blank : Mode = Blank{}
  choose(Res<Fault,State>,newline(g),u =>
    Done{State{blank,invert(line)}},u =>
  choose(Res<Fault,State>,space(g),u =>
    Done{State{blank,line}},u =>
  choose(Res<Fault,State>,hash(g),u =>
    Done{State{Comment{},line}},u =>
  choose(Res<Fault,State>,tab(g),u =>
    Fail{Unsupported{}},u =>
    Done{State{Word{},line}}))))

def report(r: Res<Fault,State>) -> Report:
  match r:
    case Fail{Invalid{}}: Refused{}
    case Fail{Unsupported{}}: Deferred{}
    case Done{State{Blank{},l}}: Blanked{}
    case Done{State{Comment{},l}}: Commented{}
    case Done{State{Word{},l}}: Worded{}

def line_of(r: Res<Fault,State>) -> Flag:
  match r:
    case Fail{e}: Off{}
    case Done{State{m,l}}: l

def step(g: Glyph, line: Flag) -> Report:
  report(normal(g,line))

def line_after(g: Glyph, line: Flag) -> Flag:
  line_of(normal(g,line))

def main() -> Report:
  step(Hash{},On{})
