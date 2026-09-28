import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/opt.bend as O
import ../../src/opt-check.bend as K
import ../../src/opt-fold.bend as F
import ./core-controls.bend as X

def before() -> List<&2,C.Function>:
  [X.function("f",[X.parameter("x",1,0)],0,X.reference(0,0)),
   X.function("g",Nil{},0,X.value(1))]

def checked(after: List<&2,C.Function>) -> String:
  X.status(K.recheck(128n,X.types(),before(),after))

def shape(result: Result<S.Error,C.Term>) -> String:
  match result:
    case Done{C.Reference{token,level,typ}}: "reference"
    case Done{C.Value{token,typ,tag}}: "value"
    case _: "unexpected"

def known(+typ: U32) -> List<&2,C.Binding>:
  [C.Binding{X.token("x"),0,2,typ,False{},Some{C.Value{X.token("x"),typ,0}}}]

def literal(option: Maybe<&2,C.Term>) -> String:
  match option:
    case None{}: "retained"
    case Some{term}: "propagated"

def settled(result: Result<S.Error,C.Book>) -> String:
  match result:
    case Done{C.Book{types,Con{C.Function{signature,C.Value{token,typ,tag}},Nil{}}}}: "checked-rewrite"
    case Fail{error}: X.error(error)
    case _: "unexpected"

def main() -> List<String>:
  [checked(before()),
   checked([X.function("g",Nil{},0,X.value(1))]),
   checked([X.function("f",[X.parameter("x",1,0)],0,X.reference(0,0))]),
   checked([X.function("g",Nil{},0,X.value(1)),X.function("f",[X.parameter("x",1,0)],0,X.reference(0,0))]),
   checked([X.function("renamed",[X.parameter("x",1,0)],0,X.reference(0,0)),X.function("g",Nil{},0,X.value(1))]),
   checked([X.function("f",[X.parameter("x",0,0)],0,X.value(0)),X.function("g",Nil{},0,X.value(1))]),
   checked([X.function("f",[X.parameter("x",1,1)],0,X.value(0)),X.function("g",Nil{},0,X.value(1))]),
   checked([X.function("f",[X.parameter("x",1,0)],1,X.reference(0,0)),X.function("g",Nil{},0,X.value(1))]),
   checked([X.function("f",[X.parameter("x",1,0)],0,X.reference(99,0)),X.function("g",Nil{},0,X.value(1))]),
   shape(O.walk(128n,O.Expression{X.reference(0,0)},O.Fold{},X.types(),Nil{},Nil{},1,known(0))),
   shape(O.walk(128n,O.Expression{X.reference(0,3)},O.Fold{},X.types(),Nil{},Nil{},1,known(3))),
   literal(F.literal(C.Value{X.token("Empty"),3,0},X.types())),
   settled(O.settle(1n,128n,X.book(Nil{},0,C.Let{X.token("x"),0,2,0,X.value(0),X.value(1)}))),
   settled(O.settle(0n,128n,X.book(Nil{},0,X.value(1))))]
