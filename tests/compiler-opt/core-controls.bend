import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/eval.bend as E
import ../../src/opt-check.bend as O
import ../../src/opt.bend as Opt

type Trial is Data:
  Trial{name: String, depth: Nat, book: C.Book, expected: String}

def token(text: String) -> S.Token:
  S.Token{text,S.At{0,0,0,0}}

def parameter(name: String, q: U32, type_id: U32) -> C.Parameter:
  C.Parameter{token(name),q,type_id}

def binding(name: String, level: U32, q: U32, type_id: U32) -> C.Binding:
  C.Binding{token(name),level,q,type_id,True{},None{}}

def types() -> List<&2,C.Datatype>:
  [C.Datatype{token("Flag"),True{},[C.Constructor{token("Off"),Nil{}},C.Constructor{token("On"),Nil{}}]},
   C.Datatype{token("Pair"),True{},[C.Constructor{token("Pair"),[parameter("left",1,0),parameter("right",1,0)]}]},
   C.Datatype{token("Owned"),False{},[C.Constructor{token("Owned"),Nil{}}]},
   C.Datatype{token("Tree"),True{},[C.Constructor{token("Empty"),Nil{}},C.Constructor{token("Node"),[parameter("child",1,3)]}]}]

def value(tag: U32) -> C.Term:
  C.Value{token("value"),0,tag}

def reference(level: U32, type_id: U32) -> C.Term:
  C.Reference{token("reference"),level,type_id}

def function(name: String, params: List<&2,C.Parameter>, result: U32, body: C.Term) -> C.Function:
  C.Function{C.Signature{token(name),params,result},body}

def book(params: List<&2,C.Parameter>, result: U32, body: C.Term) -> C.Book:
  C.Book{types(),[function("f",params,result,body)]}

def flags() -> List<&2,C.Term>:
  [C.Branch{0,Nil{},value(1)},C.Branch{1,Nil{},value(0)}]

def pair(fields: List<&2,C.Parameter>, args: List<&2,C.Term>) -> C.Term:
  C.Construct{token("Pair"),1,0,fields,args}

def pair_fields() -> List<&2,C.Parameter>:
  [parameter("left",1,0),parameter("right",1,0)]

def recursive(fields: List<&2,C.Binding>, argument: C.Term) -> C.Book:
  book([parameter("tree",1,3)],0,
    C.Case{token("tree"),0,0,[C.Branch{0,Nil{},value(0)},
      C.Branch{1,fields,C.Application{token("f"),0,0,[argument]}}]})

def forward(q: U32) -> C.Book:
  C.Book{types(),[
    function("f",Nil{},0,C.Let{token("x"),7,q,0,C.Application{token("g"),1,0,Nil{}},value(0)}),
    function("g",Nil{},0,value(1))]}

def called(type_id: U32, args: List<&2,C.Term>) -> C.Book:
  C.Book{types(),[
    function("id",[parameter("x",1,0)],0,reference(0,0)),
    function("f",Nil{},0,C.Application{token("id"),0,type_id,args})]}

def retained_parent() -> C.Book:
  book(Nil{},1,C.Let{token("p"),0,2,1,pair(pair_fields(),[value(0),value(1)]),
    C.Case{token("p"),0,1,[C.Branch{0,[binding("l",1,2,0),binding("r",2,2,0)],reference(0,1)}]}})

def overlapping_fields() -> C.Book:
  book(Nil{},0,C.Let{token("p"),0,1,1,
    pair(pair_fields(),[value(0),C.Let{token("inner"),1,2,0,value(1),reference(1,0)}]),
    C.Case{token("p"),0,0,[C.Branch{0,[binding("l",1,1,0),binding("r",2,1,0)],reference(2,0)}]}})

# Literal expectations target the checker boundary, including malformed IR.
def trials() -> List<&2,Trial>:
  [Trial{"constant",128n,book(Nil{},0,value(1)),"Done"},
   Trial{"reference",128n,book([parameter("x",1,0)],0,reference(0,0)),"Done"},
   Trial{"sparse-let-case",128n,book(Nil{},0,C.Let{token("x"),4095,1,0,value(0),C.Case{token("x"),4095,0,flags()}}),"Done"},
   Trial{"sparse-field",128n,book([parameter("p",1,1)],0,C.Case{token("p"),0,0,[C.Branch{0,[binding("l",7,1,0),binding("r",31,1,0)],reference(31,0)}]}),"Done"},
   Trial{"field-promotion",128n,book([parameter("p",1,1)],1,C.Case{token("p"),0,1,[C.Branch{0,[binding("l",7,2,0),binding("r",31,1,0)],pair(pair_fields(),[reference(7,0),reference(7,0)])}]}),"Done"},
   Trial{"constructor",128n,book(Nil{},1,pair(pair_fields(),[value(0),value(1)])),"Done"},
   Trial{"call",128n,called(0,[value(1)]),"Done"},
   Trial{"erased-forward",128n,forward(0),"Done"},
   Trial{"descent",128n,recursive([binding("child",9,1,3)],reference(9,3)),"Done"},
   Trial{"free-level",128n,book(Nil{},0,reference(0,0)),"Internal:opt-core:binding-level"},
   Trial{"reference-type",128n,book([parameter("x",1,0)],1,reference(0,1)),"Internal:opt-core:reference-type"},
   Trial{"erased-live",128n,book([parameter("x",0,0)],0,reference(0,0)),"Internal:opt-core:erased-live"},
   Trial{"erased-free",128n,book(Nil{},0,C.Let{token("x"),7,0,0,reference(3,0),value(0)}),"Internal:opt-core:binding-level"},
   Trial{"affine-reuse",128n,book([parameter("x",1,0)],0,C.Let{token("a"),7,1,0,reference(0,0),reference(0,0)}),"Internal:opt-core:affine-reuse"},
   Trial{"let-collision",128n,book([parameter("x",1,0)],0,C.Let{token("a"),0,1,0,value(0),value(1)}),"Internal:opt-core:binder-level"},
   Trial{"let-type",128n,book(Nil{},0,C.Let{token("x"),7,1,1,value(0),value(1)}),"Internal:opt-core:type-mismatch"},
   Trial{"let-quantity",128n,book(Nil{},0,C.Let{token("x"),7,3,0,value(0),value(1)}),"Internal:opt-core:quantity-range"},
   Trial{"level-bound",128n,book(Nil{},0,C.Let{token("x"),4096,1,0,value(0),value(1)}),"Exhausted:opt-core"},
   Trial{"constructor-tag",128n,book(Nil{},0,value(2)),"Internal:opt-core:constructor-tag"},
   Trial{"constant-fields",128n,book(Nil{},1,C.Value{token("Pair"),1,0}),"Internal:opt-core:constant-fields"},
   Trial{"constructor-signature",128n,book(Nil{},1,pair([parameter("left",2,0),parameter("right",1,0)],[value(0),value(1)])),"Internal:opt-core:constructor-signature"},
   Trial{"constructor-arity",128n,book(Nil{},1,pair(pair_fields(),[value(0)])),"Internal:opt-core:argument-arity"},
   Trial{"call-arity",128n,called(0,Nil{}),"Internal:opt-core:argument-arity"},
   Trial{"call-type",128n,called(1,[value(0)]),"Internal:opt-core:call-type"},
   Trial{"call-index",128n,book(Nil{},0,C.Application{token("missing"),1,0,Nil{}}),"Internal:opt-core:forward-live-call"},
   Trial{"live-forward",128n,forward(1),"Internal:opt-core:forward-live-call"},
   Trial{"recursive-nondescendant",128n,recursive([binding("child",9,1,3)],reference(0,3)),"Unsupported:opt-core:recursive-call"},
   Trial{"missing-arm",128n,book([parameter("x",1,0)],0,C.Case{token("x"),0,0,[C.Branch{0,Nil{},value(0)}]}),"Internal:opt-core:missing-arm"},
   Trial{"duplicate-arm",128n,book([parameter("x",1,0)],0,C.Case{token("x"),0,0,[C.Branch{0,Nil{},value(0)},C.Branch{0,Nil{},value(1)}]}),"Internal:opt-core:duplicate-arm"},
   Trial{"case-type",128n,book([parameter("x",1,0)],0,C.Case{token("x"),0,1,flags()}),"Internal:opt-core:case-type"},
   Trial{"case-erased",128n,book([parameter("x",0,0)],0,C.Case{token("x"),0,0,flags()}),"Internal:opt-core:erased-scrutinee"},
   Trial{"case-affine-reuse",128n,book([parameter("x",1,0)],0,C.Case{token("x"),0,0,[C.Branch{0,Nil{},reference(0,0)},C.Branch{1,Nil{},value(1)}]}),"Internal:opt-core:affine-reuse"},
   Trial{"field-collision",128n,recursive([binding("child",0,1,3)],reference(0,3)),"Internal:opt-core:binder-level"},
   Trial{"field-type",128n,recursive([binding("child",9,1,0)],reference(9,3)),"Internal:opt-core:field-type"},
   Trial{"field-quantity",128n,recursive([binding("child",9,0,3)],reference(9,3)),"Internal:opt-core:field-quantity"},
   Trial{"field-arity",128n,recursive(Nil{},value(0)),"Internal:opt-core:field-arity"},
   Trial{"sequence-expression",128n,book(Nil{},0,C.Sequence{Nil{}}),"Internal:opt-core:expression-sequence"},
   Trial{"branch-expression",128n,book(Nil{},0,C.Branch{0,Nil{},value(0)}),"Internal:opt-core:expression-branch"},
   Trial{"reusable-type",128n,book([parameter("x",2,2)],0,value(0)),"Internal:opt-core:reusable-type"},
   Trial{"missing-type",128n,book([parameter("x",1,4)],0,value(0)),"Internal:opt-core:type-index"},
   Trial{"zero-depth",0n,book(Nil{},0,value(0)),"Exhausted:opt-core"}]

def error(error: S.Error) -> String:
  match error:
    case S.Invalid{phase,code,at}: String.concat(["Invalid:",phase,":",code])
    case S.Unsupported{phase,code,at}: String.concat(["Unsupported:",phase,":",code])
    case S.Exhausted{phase,at}: String.concat(["Exhausted:",phase])
    case S.Internal{phase,code}: String.concat(["Internal:",phase,":",code])
    case S.Host{phase,code}: String.concat(["Host:",phase,":",code])

def status(result: Result<S.Error,C.Book>) -> String:
  match result:
    case Fail{failure}: error(failure)
    case Done{book}: "Done"

def observation(+book: C.Book) -> Result<S.Error,String>:
  S.bind(E.Value,String,E.invoke(book,"f",Nil{},4096n),value => E.describe(value,book))

def observed(result: Result<S.Error,String>, +expected: String) -> IO(Unit):
  match result:
    case Fail{failure}: IO.die(Unit,1,error(failure))
    case Done{+actual}:
      S.choose(IO(Unit),String.eq(actual,expected),u => IO.pure(Unit,Unit{}),u =>
        IO.die(Unit,1,String.concat(["expected ",expected,"\tactual ",actual])))

def pipeline_control(+book: C.Book, +expected: String) -> IO(Unit):
  do IO<Unit>:
    observed(observation(book),expected)
    observed(S.bind(C.Book,String,Opt.pipeline(4096n,book),next => observation(next)),expected)

def check(pending: List<&2,Trial>, +passed: U32) -> IO(Unit):
  match pending:
    case Nil{}: IO.print(String.concat(["CoreControls\t",U32.show(passed)]))
    case Con{Trial{+name,depth,book,+expected},+tail}:
      +actual = status(O.verify(depth,book))
      S.choose(IO(Unit),String.eq(actual,expected),u => check(tail,U32.add(passed,1)),u =>
        IO.die(Unit,1,String.concat([name,"\texpected ",expected,"\tactual ",actual])))

def main() -> IO(Unit):
  do IO<Unit>:
    pipeline_control(retained_parent(),"Evaluated\t1\t0\tPair{Off{},On{}}")
    pipeline_control(overlapping_fields(),"Evaluated\t0\t1\tOn{}")
    check(trials(),2)
