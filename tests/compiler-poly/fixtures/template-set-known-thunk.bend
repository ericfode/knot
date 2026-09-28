# The exact scope.set_known shape: ~value runs inside a choose thunk over + fields, refine and replace instantiate it.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Slot is Data:
  Zero{}
  One{}

type Known is Data:
  Unknown{}
  KnownOff{}
  KnownOn{}
  Referenced{}

type Unit is Data:
  Unit{}

type Opt<a, -A: Kind(a)> is Kind(a):
  None{}
  Some{value: A}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

type Term is Data:
  Value{token: Flag, type_id: Color, tag: Flag}
  Ref{token: Flag}

type Binding is Data:
  Binding{token: Flag, id: Slot, q: Flag, type_id: Color, param: Flag, known: Opt<&2,Term>}

def choose(-A: Type, condition: Flag, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case On{}: yes(Unit{})
    case Off{}: no(Unit{})

def same(a: Slot, b: Slot) -> Flag:
  match a:
    case Zero{}:
      match b:
        case Zero{}: On{}
        case One{}: Off{}
    case One{}:
      match b:
        case Zero{}: Off{}
        case One{}: On{}

def set_known(~A: Data, ~value: A -> Flag -> Color -> Term, bindings: Seq<&2,Binding>, +level: Slot, +payload: A) -> Seq<&2,Binding>:
  match bindings:
    case Stop{}: Stop{}
    case Link{Binding{+token,+id,q,+type_id,param,+known},tail}:
      Link{Binding{token,id,q,type_id,param,
        choose(Opt<&2,Term>,same(id,level),u => Some{value(payload,token,type_id)},u => known)},
        set_known(~A,~value,tail,level,payload)}

def refine(bindings: Seq<&2,Binding>, +level: Slot, +tag: Flag) -> Seq<&2,Binding>:
  set_known(~Flag,~(tag => token => type_id => Value{token,type_id,tag}),bindings,level,tag)

def replace(bindings: Seq<&2,Binding>, +level: Slot, +term: Term) -> Seq<&2,Binding>:
  set_known(~Term,~(term => token => type_id => term),bindings,level,term)

def fresh(id: Slot) -> Binding:
  Binding{On{},id,On{},Red{},Off{},None{}}

def pair() -> Seq<&2,Binding>:
  Link{fresh(Zero{}),Link{fresh(One{}),Stop{}}}

def known_of(t: Opt<&2,Term>) -> Known:
  match t:
    case None{}: Unknown{}
    case Some{Value{token,type_id,Off{}}}: KnownOff{}
    case Some{Value{token,type_id,On{}}}: KnownOn{}
    case Some{Ref{token}}: Referenced{}

def first(bs: Seq<&2,Binding>) -> Known:
  match bs:
    case Stop{}: Unknown{}
    case Link{Binding{token,id,q,type_id,param,known},tail}: known_of(known)

def refined(level: Slot, tag: Flag) -> Known:
  first(refine(pair(),level,tag))

def replaced(level: Slot, token: Flag) -> Known:
  first(replace(pair(),level,Ref{token}))

def main() -> Known:
  refined(Zero{},On{})
