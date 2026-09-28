# Twin of template-qualified-arg: the template's type argument is Bool, the payload a C.Term.
import Base
import ./core.bend as C

type Slot is Data:
  Slot{id: Bool, known: Maybe<&2,C.Term>}

type Answer is Type:
  Unset{}
  Known{}
  Blank{}

type Pick is Type:
  First{}
  Second{}

def pick(hit: Bool, fresh: C.Term, old: Maybe<&2,C.Term>) -> Maybe<&2,C.Term>:
  match hit:
    case True{}: Some{fresh}
    case False{}: old

def set_known(~A: Data, ~value: A -> C.Term, slots: List<&2,Slot>, +level: Bool, +payload: A) -> List<&2,Slot>:
  match slots:
    case Nil{}: Nil{}
    case Con{Slot{+id,known},tail}:
      Con{Slot{id,pick(Bool.not(Bool.xor(id,level)),value(payload),known)},set_known(~A,~value,tail,level,payload)}

def store(slots: List<&2,Slot>, +level: Bool, +term: C.Term) -> List<&2,Slot>:
  set_known(~Bool,~(term => term),slots,level,term)

def first(slots: List<&2,Slot>) -> Answer:
  match slots:
    case Nil{}: Blank{}
    case Con{Slot{id,None{}},rest}: Unset{}
    case Con{Slot{id,Some{C.Value{tag}}},rest}: Known{}
    case Con{Slot{id,Some{C.Hole{}}},rest}: Blank{}

def level(p: Pick) -> Bool:
  match p:
    case First{}: True{}
    case Second{}: False{}

def probe(p: Pick) -> Answer:
  first(store([Slot{True{},None{}},Slot{False{},None{}}],level(p),C.Value{True{}}))

def main() -> Answer:
  probe(First{})
