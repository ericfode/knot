import Base
import ./syntax.bend as S
import ./core.bend as C

# Comparison provenance never substitutes runtime references or spends uses.
type Alias is Data:
  Alias{level: U32, value: C.Term}
type Shape is Data:
  Variable{level: U32}
  Constructor{type_id: U32, tag: U32, fields: List<&2,Shape>}
  Opaque{}
  Deferred{term: C.Term}
type Comparison is Data:
  Compare{argument: Shape, column: Shape}
  Fields{arguments: List<&2,Shape>, columns: List<&2,Shape>, index: U32, order: Cmp}
  Inside{argument: Shape, columns: List<&2,Shape>, failed: Maybe<&2,U32>, index: U32}
type Product is Data:
  Product{order: Cmp, failed: Maybe<&2,U32>}
type Frame is Data:
  Aligned{argument: Shape, columns: List<&2,Shape>}
  Field{arguments: List<&2,Shape>, columns: List<&2,Shape>, index: U32, order: Cmp}
  Search{argument: Shape, columns: List<&2,Shape>, failed: Maybe<&2,U32>, index: U32}
type Progress is Data:
  Complete{result: Product}
  Continue{mode: Comparison, frames: List<&2,Frame>}

def equal(order: Cmp) -> Bool:
  match order:
    case EQ{}: True{}
    case _: False{}

def smaller(order: Cmp) -> Bool:
  match order:
    case LT{}: True{}
    case _: False{}

def known(bindings: List<&2,C.Binding>, +level: U32) -> Maybe<&2,C.Term>:
  match bindings:
    case Nil{}: None{}
    case Con{C.Binding{token,id,q,type_id,param,+value},+tail}:
      S.choose(Maybe<&2,C.Term>,U32.is_eq(id,level),u => value,u => known(tail,level))

def origin(aliases: List<&2,Alias>, +bindings: List<&2,C.Binding>, +level: U32) -> Maybe<&2,C.Term>:
  match aliases:
    case Nil{}: known(bindings,level)
    case Con{Alias{id,+value},+tail}:
      S.choose(Maybe<&2,C.Term>,U32.is_eq(id,level),u => Some{value},u => origin(tail,bindings,level))

def reference(value: Maybe<&2,C.Term>, level: U32) -> Shape:
  match value:
    case None{}: Variable{level}
    case Some{term}: Deferred{term}

def deferred(terms: List<&2,C.Term>) -> List<&2,Shape>:
  match terms:
    case Nil{}: Nil{}
    case Con{term,tail}: Con{Deferred{term},deferred(tail)}

# Expose one head; constructor children retain sharing until compared.
def view(term: C.Term, bindings: List<&2,C.Binding>, aliases: List<&2,Alias>) -> Shape:
  match term:
    case C.Reference{token,+level,type_id}: reference(origin(aliases,bindings,level),level)
    case C.Value{token,type_id,tag}: Constructor{type_id,tag,Nil{}}
    case C.Construct{token,type_id,tag,params,args}: Constructor{type_id,tag,deferred(args)}
    case _: Opaque{}

def force(+head: Shape, next: C.Term -> Result<S.Error,Shape>) -> Result<S.Error,Shape>:
  match head:
    case Deferred{term}: next(term)
    case _: Done{head}

def shape(fuel: Nat, term: C.Term, +bindings: List<&2,C.Binding>, +aliases: List<&2,Alias>) -> Result<S.Error,Shape>:
  match fuel:
    case 0n: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ n:
      force(view(term,bindings,aliases),next => shape(n,next,bindings,aliases))

# A product keeps every field non-increasing; columns below are lexicographic.
def join(prior: Cmp, current: Cmp) -> Cmp:
  match prior current:
    case _ GT{}: GT{}
    case GT{} _: GT{}
    case _ LT{}: LT{}
    case LT{} _: LT{}
    case _ _: EQ{}

def skipped(failed: Maybe<&2,U32>, index: U32) -> Bool:
  match failed:
    case None{}: False{}
    case Some{at}: U32.is_eq(at,index)

def variable(arg: Shape, level: U32) -> Cmp:
  match arg:
    case Variable{id}: S.choose(Cmp,U32.is_eq(id,level),u => EQ{},u => GT{})
    case _: GT{}

def aligned(arg: Shape, type_id: U32, tag: U32, cols: List<&2,Shape>) -> Bool:
  match arg:
    case Constructor{typ,ctr,args}:
      Bool.and(Bool.and(U32.is_eq(typ,type_id),U32.is_eq(ctr,tag)),
        Nat.is_eq(List.length(&2,Shape,args),List.length(&2,Shape,cols)))
    case _: False{}

def arguments(arg: Shape) -> List<&2,Shape>:
  match arg:
    case Constructor{type_id,tag,items}: items
    case _: Nil{}

def order(result: Product) -> Cmp:
  match result:
    case Product{value,failed}: value

# Every popped frame was pushed by one charged transition.
def settle(frames: List<&2,Frame>, result: Product) -> Progress:
  match frames result:
    case Nil{} value: Complete{value}
    case Con{Aligned{arg,cols},tail} Product{value,None{}}:
      settle(tail,Product{value,None{}})
    case Con{Aligned{arg,cols},tail} Product{value,Some{index}}:
      Continue{Inside{arg,cols,Some{index},0},tail}
    case Con{Field{args,cols,index,prior},tail} Product{GT{},failed}:
      settle(tail,Product{GT{},Some{index}})
    case Con{Field{args,cols,index,prior},tail} Product{value,failed}:
      Continue{Fields{args,cols,U32.add(index,1),join(prior,value)},tail}
    case Con{Search{arg,cols,failed,index},tail} Product{GT{},unused}:
      Continue{Inside{arg,cols,failed,U32.add(index,1)},tail}
    case Con{Search{arg,cols,failed,index},tail} Product{value,unused}:
      settle(tail,Product{LT{},None{}})

def step(mode: Comparison, +frames: List<&2,Frame>, bindings: List<&2,C.Binding>, aliases: List<&2,Alias>) -> Result<S.Error,Progress>:
  match mode:
    case Compare{Deferred{term},col}: Done{Continue{Compare{view(term,bindings,aliases),col},frames}}
    case Compare{arg,Deferred{term}}: Done{Continue{Compare{arg,view(term,bindings,aliases)},frames}}
    case Compare{arg,Variable{level}}: Done{settle(frames,Product{variable(arg,level),None{}})}
    case Compare{+arg,Constructor{+type_id,+tag,+cols}}:
      Done{S.choose(Progress,aligned(arg,type_id,tag,cols),u =>
        Continue{Fields{arguments(arg),cols,0,EQ{}},Con{Aligned{arg,cols},frames}},u =>
        Continue{Inside{arg,cols,None{},0},frames})}
    case Compare{arg,col}: Done{settle(frames,Product{GT{},None{}})}
    case Fields{Nil{},Nil{},index,value}: Done{settle(frames,Product{value,None{}})}
    case Fields{Con{arg,tail},Con{col,rest},index,value}:
      Done{Continue{Compare{arg,col},Con{Field{tail,rest,index,value},frames}}}
    case Fields{args,cols,index,value}: C.internal(Progress,"descent-product-arity")
    case Inside{arg,Nil{},failed,index}: Done{settle(frames,Product{GT{},None{}})}
    case Inside{+arg,Con{+col,+tail},+failed,+index}:
      Done{S.choose(Progress,skipped(failed,index),u =>
        Continue{Inside{arg,tail,failed,U32.add(index,1)},frames},u =>
        Continue{Compare{arg,col},Con{Search{arg,tail,failed,index},frames}})}

# A single quota covers head exposure, products and fallback search.
def drive(fuel: Nat, progress: Progress, +bindings: List<&2,C.Binding>, +aliases: List<&2,Alias>) -> Result<S.Error,Product>:
  match fuel progress:
    case n Complete{result}: Done{result}
    case 0n Continue{mode,frames}: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ n Continue{mode,frames}:
      S.bind(Progress,Product,step(mode,frames,bindings,aliases),next => drive(n,next,bindings,aliases))

def run(fuel: Nat, mode: Comparison) -> Result<S.Error,Product>:
  drive(fuel,Continue{mode,Nil{}},Nil{},Nil{})

def compare(fuel: Nat, arg: Shape, col: Shape) -> Result<S.Error,Cmp>:
  S.bind(Product,Cmp,run(fuel,Compare{arg,col}),result => Done{order(result)})

def compare_in(fuel: Nat, arg: C.Term, col: C.Term, bindings: List<&2,C.Binding>, aliases: List<&2,Alias>) -> Result<S.Error,Cmp>:
  S.bind(Product,Cmp,drive(fuel,Continue{Compare{Deferred{arg},Deferred{col}},Nil{}},bindings,aliases),result => Done{order(result)})

def columns(params: List<&2,C.Parameter>, args: List<&2,C.Term>, +index: U32, +fuel: Nat,
  +bindings: List<&2,C.Binding>, +aliases: List<&2,Alias>) -> Result<S.Error,Cmp>:
  match params args:
    case Nil{} Nil{}: Done{EQ{}}
    case Con{C.Parameter{+token,q,+type_id},+tail} Con{+arg,+rest}:
      S.choose(Result<S.Error,Cmp>,U32.is_eq(q,0),u => columns(tail,rest,U32.add(index,1),fuel,bindings,aliases),u =>
        S.bind(Cmp,Cmp,compare_in(fuel,arg,C.Reference{token,index,type_id},bindings,aliases),+order =>
          S.choose(Result<S.Error,Cmp>,equal(order),u => columns(tail,rest,U32.add(index,1),fuel,bindings,aliases),u => Done{order})))
    case _ _: C.internal(Cmp,"descent-call-arity")
