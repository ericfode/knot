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
  Sequence{items: List<&2,Shape>}
type Inspection is Data:
  Inspect{term: C.Term}
  InspectMany{terms: List<&2,C.Term>}
type Comparison is Data:
  Compare{argument: Shape, column: Shape}
  Fields{arguments: List<&2,Shape>, columns: List<&2,Shape>, index: U32, order: Cmp}
  Inside{argument: Shape, columns: List<&2,Shape>, failed: Maybe<&2,U32>, index: U32}
type Product is Data:
  Product{order: Cmp, failed: Maybe<&2,U32>}

def equal(order: Cmp) -> Bool:
  match order:
    case EQ{}: True{}
    case _: False{}

def smaller(order: Cmp) -> Bool:
  match order:
    case LT{}: True{}
    case _: False{}

def greater(order: Cmp) -> Bool:
  match order:
    case GT{}: True{}
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

def reference(value: Maybe<&2,C.Term>, level: U32, next: C.Term -> Result<S.Error,Shape>) -> Result<S.Error,Shape>:
  match value:
    case None{}: Done{Variable{level}}
    case Some{term}: next(term)

def prepend(head: Shape, tail: Shape) -> Result<S.Error,Shape>:
  match tail:
    case Sequence{items}: Done{Sequence{Con{head,items}}}
    case _: C.internal(Shape,"descent-shape-list")

def constructed(value: Shape, type_id: U32, tag: U32) -> Result<S.Error,Shape>:
  match value:
    case Sequence{items}: Done{Constructor{type_id,tag,items}}
    case _: C.internal(Shape,"descent-shape-fields")

def inspect(fuel: Nat, mode: Inspection, +bindings: List<&2,C.Binding>, +aliases: List<&2,Alias>) -> Result<S.Error,Shape>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ +n Inspect{C.Reference{token,+level,type_id}}:
      reference(origin(aliases,bindings,level),level,value => inspect(n,Inspect{value},bindings,aliases))
    case 1n+ n Inspect{C.Value{token,type_id,tag}}: Done{Constructor{type_id,tag,Nil{}}}
    case 1n+ +n Inspect{C.Construct{token,+type_id,+tag,params,args}}:
      S.bind(Shape,Shape,inspect(n,InspectMany{args},bindings,aliases),value => constructed(value,type_id,tag))
    case 1n+ n Inspect{term}: Done{Opaque{}}
    case 1n+ n InspectMany{Nil{}}: Done{Sequence{Nil{}}}
    case 1n+ +n InspectMany{Con{head,+tail}}:
      S.bind(Shape,Shape,inspect(n,Inspect{head},bindings,aliases),+value =>
        S.bind(Shape,Shape,inspect(n,InspectMany{tail},bindings,aliases),rest => prepend(value,rest)))

def shape(fuel: Nat, term: C.Term, bindings: List<&2,C.Binding>, aliases: List<&2,Alias>) -> Result<S.Error,Shape>:
  inspect(fuel,Inspect{term},bindings,aliases)

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

def fallback(result: Product, next: U32 -> Result<S.Error,Product>) -> Result<S.Error,Product>:
  match result:
    case Product{order,None{}}: Done{Product{order,None{}}}
    case Product{order,Some{index}}: next(index)

def field(result: Product, +index: U32, +order: Cmp,
  next: Cmp -> Result<S.Error,Product>) -> Result<S.Error,Product>:
  match result:
    case Product{GT{},failed}: Done{Product{GT{},Some{index}}}
    case Product{actual,failed}: next(join(order,actual))

def order(result: Product) -> Cmp:
  match result:
    case Product{value,failed}: value

def run(fuel: Nat, mode: Comparison) -> Result<S.Error,Product>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ n Compare{arg,Variable{level}}: Done{Product{variable(arg,level),None{}}}
    case 1n+ +n Compare{+arg,Constructor{+type_id,+tag,+cols}}:
      S.choose(Result<S.Error,Product>,aligned(arg,type_id,tag,cols),u =>
        S.bind(Product,Product,run(n,Fields{arguments(arg),cols,0,EQ{}}),result =>
          fallback(result,index => run(n,Inside{arg,cols,Some{index},0}))),u =>
        run(n,Inside{arg,cols,None{},0}))
    case 1n+ n Compare{arg,col}: Done{Product{GT{},None{}}}
    case 1n+ n Fields{Nil{},Nil{},index,value}: Done{Product{value,None{}}}
    case 1n+ +n Fields{Con{arg,+tail},Con{col,+rest},+index,+value}:
      S.bind(Product,Product,run(n,Compare{arg,col}),result =>
        field(result,index,value,actual => run(n,Fields{tail,rest,U32.add(index,1),actual})))
    case 1n+ n Fields{args,cols,index,value}: C.internal(Product,"descent-product-arity")
    case 1n+ n Inside{arg,Nil{},failed,index}: Done{Product{GT{},None{}}}
    case 1n+ +n Inside{+arg,Con{+col,+tail},+failed,+index}:
      S.choose(Result<S.Error,Product>,skipped(failed,index),u => run(n,Inside{arg,tail,failed,U32.add(index,1)}),u =>
        S.bind(Product,Product,run(n,Compare{arg,col}),result =>
          S.choose(Result<S.Error,Product>,greater(order(result)),u => run(n,Inside{arg,tail,failed,U32.add(index,1)}),u => Done{Product{LT{},None{}}})))

def compare(fuel: Nat, arg: Shape, col: Shape) -> Result<S.Error,Cmp>:
  S.bind(Product,Cmp,run(fuel,Compare{arg,col}),result => Done{order(result)})

def columns(params: List<&2,C.Parameter>, args: List<&2,C.Term>, +index: U32, +fuel: Nat,
  +bindings: List<&2,C.Binding>, +aliases: List<&2,Alias>) -> Result<S.Error,Cmp>:
  match params args:
    case Nil{} Nil{}: Done{EQ{}}
    case Con{C.Parameter{+token,q,+type_id},+tail} Con{+arg,+rest}:
      S.choose(Result<S.Error,Cmp>,U32.is_eq(q,0),u => columns(tail,rest,U32.add(index,1),fuel,bindings,aliases),u =>
        S.bind(Shape,Cmp,shape(fuel,arg,bindings,aliases),+actual =>
          S.bind(Shape,Cmp,shape(fuel,C.Reference{token,index,type_id},bindings,aliases),col =>
            S.bind(Cmp,Cmp,compare(fuel,actual,col),+order =>
              S.choose(Result<S.Error,Cmp>,equal(order),u => columns(tail,rest,U32.add(index,1),fuel,bindings,aliases),u => Done{order})))))
    case _ _: C.internal(Cmp,"descent-call-arity")
