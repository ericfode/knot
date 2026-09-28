import Base
import ./syntax.bend as S
import ./core.bend as C

type TypeRef is Data:
  TypeRef{index: U32, definition: C.Datatype}
type FunctionRef is Data:
  FunctionRef{index: U32, signature: C.Signature}
type ConstructorRef is Data:
  ConstructorRef{type_id: U32, tag: U32}

def named(tokens: List<&2,S.Token>, +name: S.Token) -> Bool:
  match tokens:
    case Nil{}: False{}
    case Con{h,t}: Bool.or(String.eq(S.text(h),S.text(name)),named(t,name))

def names(nodes: List<&2,S.Node>, +seen: List<&2,S.Token>) -> Result<S.Error,Unit>:
  match nodes:
    case Nil{}: Done{Unit{}}
    case Con{S.Datatype{+name,data,ctors},+tail}:
      S.choose(Result<S.Error,Unit>,named(seen,name),u => C.invalid(Unit,"duplicate-global",name),u => names(tail,Con{name,seen}))
    case Con{S.Function{+name,params,result,body},+tail}:
      S.choose(Result<S.Error,Unit>,named(seen,name),u => C.invalid(Unit,"duplicate-global",name),u => names(tail,Con{name,seen}))
    case Con{S.Generic{name,params,kind,ctors},tail}: C.unsupported(Unit,"generic-datatype",name)
    case Con{S.TypedFunction{name,params,result,body},tail}: C.unsupported(Unit,"type-expression",name)
    case _: C.internal(Unit,"declaration-node")

def find_type(types: List<&2,C.Datatype>, +name: S.Token, +index: U32) -> Result<S.Error,TypeRef>:
  match types:
    case Nil{}: C.invalid(TypeRef,"unknown-type",name)
    case Con{+head,+tail}:
      match head:
        case C.Datatype{token,data,ctors}:
          S.choose(Result<S.Error,TypeRef>,String.eq(S.text(token),S.text(name)),u =>
            Done{TypeRef{index,head}},u => find_type(tail,name,U32.add(index,1)))

def find_function(sigs: List<&2,C.Signature>, +name: S.Token, +index: U32) -> Result<S.Error,FunctionRef>:
  match sigs:
    case Nil{}: C.invalid(FunctionRef,"unknown-function",name)
    case Con{+head,+tail}:
      match head:
        case C.Signature{token,params,result}:
          S.choose(Result<S.Error,FunctionRef>,String.eq(S.text(token),S.text(name)),u =>
            Done{FunctionRef{index,head}},u => find_function(tail,name,U32.add(index,1)))

def constructor_tag(tokens: List<&2,C.Constructor>, +name: S.Token, +index: U32) -> Maybe<&2,U32>:
  match tokens:
    case Nil{}: None{}
    case Con{C.Constructor{h,fields},+t}:
      S.choose(Maybe<&2,U32>,String.eq(S.text(h),S.text(name)),u => Some{index},u => constructor_tag(t,name,U32.add(index,1)))

def constructor_next(tag: Maybe<&2,U32>, +index: U32, next: Unit -> Result<S.Error,ConstructorRef>) -> Result<S.Error,ConstructorRef>:
  match tag:
    case None{}: next(Unit{})
    case Some{value}: Done{ConstructorRef{index,value}}

def find_constructor(types: List<&2,C.Datatype>, +name: S.Token, +index: U32) -> Result<S.Error,ConstructorRef>:
  match types:
    case Nil{}: C.invalid(ConstructorRef,"unknown-constructor",name)
    case Con{C.Datatype{token,data,ctors},+tail}:
      constructor_next(constructor_tag(ctors,name,0),index,u => find_constructor(tail,name,U32.add(index,1)))

def constructors(nodes: List<&2,S.Node>, +seen: List<&2,S.Token>, +count: U32) -> Result<S.Error,List<&2,C.Constructor>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Constructor{+token,fields},+tail}:
      S.choose(Result<S.Error,List<&2,C.Constructor>>,U32.is_eq(count,256),u => C.exhausted(List<&2,C.Constructor>,token),u =>
        S.choose(Result<S.Error,List<&2,C.Constructor>>,named(seen,token),u => C.invalid(List<&2,C.Constructor>,"duplicate-constructor",token),u =>
          S.bind(List<&2,C.Constructor>,List<&2,C.Constructor>,constructors(tail,Con{token,seen},U32.add(count,1)),rest => Done{Con{C.Constructor{token,Nil{}},rest}})))
    case _: C.internal(List<&2,C.Constructor>,"constructor-declaration-node")

def nonempty(tokens: List<&2,C.Constructor>, +name: S.Token, data: Bool) -> Result<S.Error,C.Datatype>:
  match tokens:
    case Nil{}: C.invalid(C.Datatype,"empty-datatype",name)
    case Con{h,t}: Done{C.Datatype{name,data,Con{h,t}}}

def collect_types(nodes: List<&2,S.Node>, +count: U32) -> Result<S.Error,List<&2,C.Datatype>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Datatype{+name,+data,+ctors},+tail}:
      S.choose(Result<S.Error,List<&2,C.Datatype>>,U32.is_eq(count,256),u => C.exhausted(List<&2,C.Datatype>,name),u =>
        S.bind(List<&2,C.Constructor>,List<&2,C.Datatype>,constructors(ctors,Nil{},0),cs =>
          S.bind(C.Datatype,List<&2,C.Datatype>,nonempty(cs,name,data),head =>
            S.bind(List<&2,C.Datatype>,List<&2,C.Datatype>,collect_types(tail,U32.add(count,1)),rest => Done{Con{head,rest}}))))
    case Con{S.Function{name,params,result,body},tail}: collect_types(tail,count)
    case _: C.internal(List<&2,C.Datatype>,"type-declaration-node")

def distinct_constructors(tokens: List<&2,C.Constructor>, +seen: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  match tokens:
    case Nil{}: Done{seen}
    case Con{C.Constructor{+h,fields},+t}:
      S.choose(Result<S.Error,List<&2,S.Token>>,named(seen,h),u => C.invalid(List<&2,S.Token>,"duplicate-constructor",h),u => distinct_constructors(t,Con{h,seen}))

def unique_constructors(types: List<&2,C.Datatype>, seen: List<&2,S.Token>) -> Result<S.Error,Unit>:
  match types:
    case Nil{}: Done{Unit{}}
    case Con{C.Datatype{name,data,tokens},+tail}:
      S.bind(List<&2,S.Token>,Unit,distinct_constructors(tokens,seen),next => unique_constructors(tail,next))

def quantity(+token: S.Token, +q: U32, definition: C.Datatype) -> Result<S.Error,Unit>:
  match definition:
    case C.Datatype{name,data,ctors}:
      S.choose(Result<S.Error,Unit>,U32.is_gt(q,2),u => C.internal(Unit,"quantity-range"),u =>
        S.choose(Result<S.Error,Unit>,Bool.and(U32.is_eq(q,2),Bool.not(data)),u => C.invalid(Unit,"reusable-type",token),u => Done{Unit{}}))

def parameter_type(+token: S.Token, +q: U32, reference: TypeRef) -> Result<S.Error,C.Parameter>:
  match reference:
    case TypeRef{+index,definition}:
      S.bind(Unit,C.Parameter,quantity(token,q,definition),u => Done{C.Parameter{token,q,index}})

def parameters(nodes: List<&2,S.Node>, +types: List<&2,C.Datatype>, +count: U32) -> Result<S.Error,List<&2,C.Parameter>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Parameter{+name,+q,+type_name},+tail}:
      S.choose(Result<S.Error,List<&2,C.Parameter>>,U32.is_eq(count,256),u => C.exhausted(List<&2,C.Parameter>,name),u =>
        S.bind(TypeRef,List<&2,C.Parameter>,find_type(types,type_name,0),reference =>
          S.bind(C.Parameter,List<&2,C.Parameter>,parameter_type(name,q,reference),head =>
            S.bind(List<&2,C.Parameter>,List<&2,C.Parameter>,parameters(tail,types,U32.add(count,1)),rest => Done{Con{head,rest}}))))
    case _: C.internal(List<&2,C.Parameter>,"parameter-node")

def signature(token: S.Token, params: List<&2,C.Parameter>, reference: TypeRef) -> C.Signature:
  match reference:
    case TypeRef{index,definition}: C.Signature{token,params,index}

def collect_signatures(nodes: List<&2,S.Node>, +types: List<&2,C.Datatype>, +count: U32) -> Result<S.Error,List<&2,C.Signature>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Function{+name,+params,+result,body},+tail}:
      S.choose(Result<S.Error,List<&2,C.Signature>>,U32.is_eq(count,256),u => C.exhausted(List<&2,C.Signature>,name),u =>
        S.bind(List<&2,C.Parameter>,List<&2,C.Signature>,parameters(params,types,0),ps =>
          S.bind(TypeRef,List<&2,C.Signature>,find_type(types,result,0),reference =>
            S.bind(List<&2,C.Signature>,List<&2,C.Signature>,collect_signatures(tail,types,U32.add(count,1)),rest =>
              Done{Con{signature(name,ps,reference),rest}}))))
    case Con{S.Datatype{name,data,ctors},tail}: collect_signatures(tail,types,count)
    case _: C.internal(List<&2,C.Signature>,"function-declaration-node")

# Field ownership depends on the declared datatype kind, not on inhabitation.
# Quantity validity is checked separately; an erased Type field is permitted.
def field_kind(+data: Bool, +q: U32, +child: Bool) -> Bool:
  Bool.and(Bool.or(U32.is_ne(q,2),child),
    Bool.or(Bool.not(data),Bool.or(U32.is_eq(q,0),child)))

def field_type(+token: S.Token, +q: U32, +data: Bool, reference: TypeRef) -> Result<S.Error,C.Parameter>:
  match reference:
    case TypeRef{+index,+definition}:
      match definition:
        case C.Datatype{name,+child,ctors}:
          S.bind(Unit,C.Parameter,quantity(token,q,definition),u =>
            S.choose(Result<S.Error,C.Parameter>,field_kind(data,q,child),u =>
              Done{C.Parameter{token,q,index}},u => C.invalid(C.Parameter,"data-field-kind",token)))

def fields(nodes: List<&2,S.Node>, +types: List<&2,C.Datatype>, +data: Bool,
  +seen: List<&2,S.Token>, +count: U32) -> Result<S.Error,List<&2,C.Parameter>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Parameter{+name,+q,+type_name},+tail}:
      S.choose(Result<S.Error,List<&2,C.Parameter>>,U32.is_eq(count,256),u => C.exhausted(List<&2,C.Parameter>,name),u =>
        S.choose(Result<S.Error,List<&2,C.Parameter>>,named(seen,name),u => C.invalid(List<&2,C.Parameter>,"duplicate-field",name),u =>
          S.bind(TypeRef,List<&2,C.Parameter>,find_type(types,type_name,0),reference =>
            S.bind(C.Parameter,List<&2,C.Parameter>,field_type(name,q,data,reference),head =>
              S.bind(List<&2,C.Parameter>,List<&2,C.Parameter>,fields(tail,types,data,Con{name,seen},U32.add(count,1)),rest =>
                Done{Con{head,rest}})))))
    case Con{S.TypedParameter{token,q,typ},tail}: C.unsupported(List<&2,C.Parameter>,"type-expression",token)
    case _: C.internal(List<&2,C.Parameter>,"field-node")

def resolve_constructors(nodes: List<&2,S.Node>, +types: List<&2,C.Datatype>, +data: Bool) -> Result<S.Error,List<&2,C.Constructor>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Constructor{+token,params},tail}:
      S.bind(List<&2,C.Parameter>,List<&2,C.Constructor>,fields(params,types,data,Nil{},0),ps =>
        S.bind(List<&2,C.Constructor>,List<&2,C.Constructor>,resolve_constructors(tail,types,data),rest =>
          Done{Con{C.Constructor{token,ps},rest}}))
    case _: C.internal(List<&2,C.Constructor>,"constructor-declaration-node")

def resolve_types(nodes: List<&2,S.Node>, +headers: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Datatype>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Datatype{+name,+data,ctors},tail}:
      S.bind(List<&2,C.Constructor>,List<&2,C.Datatype>,resolve_constructors(ctors,headers,data),cs =>
        S.bind(List<&2,C.Datatype>,List<&2,C.Datatype>,resolve_types(tail,headers),rest =>
          Done{Con{C.Datatype{name,data,cs},rest}}))
    case Con{S.Function{name,params,result,body},tail}: resolve_types(tail,headers)
    case _: C.internal(List<&2,C.Datatype>,"type-declaration-node")

# The first pass preserves names, kinds and constructor order. Only the second
# pass installs resolved field signatures. Header-only values never escape here.
def catalog(root: S.Node) -> Result<S.Error,C.Catalog>:
  match root:
    case S.Sequence{+nodes}:
      S.bind(Unit,C.Catalog,names(nodes,Nil{}),u =>
        S.bind(List<&2,C.Datatype>,C.Catalog,collect_types(nodes,0),+headers =>
          S.bind(Unit,C.Catalog,unique_constructors(headers,Nil{}),u =>
            S.bind(List<&2,C.Datatype>,C.Catalog,resolve_types(nodes,headers),+types =>
              S.bind(List<&2,C.Signature>,C.Catalog,collect_signatures(nodes,types,0),sigs => Done{C.Catalog{types,sigs}})))))
    case _: C.internal(C.Catalog,"book-node")

def type_at(types: List<&2,C.Datatype>, +index: U32) -> Result<S.Error,C.Datatype>:
  match types:
    case Nil{}: C.internal(C.Datatype,"type-index")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Datatype>,U32.is_eq(index,0),u => Done{head},u => type_at(tail,U32.sub(index,1)))

def fields_at(ctors: List<&2,C.Constructor>, +tag: U32) -> Result<S.Error,List<&2,C.Parameter>>:
  match ctors:
    case Nil{}: C.internal(List<&2,C.Parameter>,"constructor-tag")
    case Con{C.Constructor{token,+fields},+tail}:
      S.choose(Result<S.Error,List<&2,C.Parameter>>,U32.is_eq(tag,0),u => Done{fields},u => fields_at(tail,U32.sub(tag,1)))

def definition_fields(definition: C.Datatype, tag: U32) -> Result<S.Error,List<&2,C.Parameter>>:
  match definition:
    case C.Datatype{token,data,ctors}: fields_at(ctors,tag)

def field_signature(reference: ConstructorRef, types: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Parameter>>:
  match reference:
    case ConstructorRef{type_id,+tag}:
      S.bind(C.Datatype,List<&2,C.Parameter>,type_at(types,type_id),definition => definition_fields(definition,tag))

def has_tag(tag: Maybe<&2,U32>) -> Bool:
  match tag:
    case None{}: False{}
    case Some{value}: True{}

def constructor_named(types: List<&2,C.Datatype>, +name: S.Token) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{C.Datatype{token,data,ctors},tail}:
      Bool.or(has_tag(constructor_tag(ctors,name,0)),constructor_named(tail,name))
