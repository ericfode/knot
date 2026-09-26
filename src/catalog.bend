import Base
import ./syntax.bend as S
import ./core.bend as C

type TypeRef is Data:
  TypeRef{index: U32, definition: C.Enum}
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
    case _: C.internal(Unit,"declaration-node")

def find_type(types: List<&2,C.Enum>, +name: S.Token, +index: U32) -> Result<S.Error,TypeRef>:
  match types:
    case Nil{}: C.invalid(TypeRef,"unknown-type",name)
    case Con{+head,+tail}:
      match head:
        case C.Enum{token,data,ctors}:
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

def constructor_tag(tokens: List<&2,S.Token>, +name: S.Token, +index: U32) -> Maybe<&2,U32>:
  match tokens:
    case Nil{}: None{}
    case Con{h,+t}:
      S.choose(Maybe<&2,U32>,String.eq(S.text(h),S.text(name)),u => Some{index},u => constructor_tag(t,name,U32.add(index,1)))

def constructor_next(tag: Maybe<&2,U32>, +index: U32, next: Unit -> Result<S.Error,ConstructorRef>) -> Result<S.Error,ConstructorRef>:
  match tag:
    case None{}: next(Unit{})
    case Some{value}: Done{ConstructorRef{index,value}}

def find_constructor(types: List<&2,C.Enum>, +name: S.Token, +index: U32) -> Result<S.Error,ConstructorRef>:
  match types:
    case Nil{}: C.invalid(ConstructorRef,"unknown-constructor",name)
    case Con{C.Enum{token,data,ctors},+tail}:
      constructor_next(constructor_tag(ctors,name,0),index,u => find_constructor(tail,name,U32.add(index,1)))

def constructors(nodes: List<&2,S.Node>, +seen: List<&2,S.Token>, +count: U32) -> Result<S.Error,List<&2,S.Token>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Constructor{+token,Nil{}},+tail}:
      S.choose(Result<S.Error,List<&2,S.Token>>,U32.is_eq(count,256),u => C.exhausted(List<&2,S.Token>,token),u =>
        S.choose(Result<S.Error,List<&2,S.Token>>,named(seen,token),u => C.invalid(List<&2,S.Token>,"duplicate-constructor",token),u =>
          S.bind(List<&2,S.Token>,List<&2,S.Token>,constructors(tail,Con{token,seen},U32.add(count,1)),rest => Done{Con{token,rest}})))
    case _: C.internal(List<&2,S.Token>,"constructor-declaration-node")

def nonempty(tokens: List<&2,S.Token>, +name: S.Token, data: Bool) -> Result<S.Error,C.Enum>:
  match tokens:
    case Nil{}: C.invalid(C.Enum,"empty-datatype",name)
    case Con{h,t}: Done{C.Enum{name,data,Con{h,t}}}

def collect_types(nodes: List<&2,S.Node>, +count: U32) -> Result<S.Error,List<&2,C.Enum>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Datatype{+name,+data,+ctors},+tail}:
      S.choose(Result<S.Error,List<&2,C.Enum>>,U32.is_eq(count,256),u => C.exhausted(List<&2,C.Enum>,name),u =>
        S.bind(List<&2,S.Token>,List<&2,C.Enum>,constructors(ctors,Nil{},0),cs =>
          S.bind(C.Enum,List<&2,C.Enum>,nonempty(cs,name,data),head =>
            S.bind(List<&2,C.Enum>,List<&2,C.Enum>,collect_types(tail,U32.add(count,1)),rest => Done{Con{head,rest}}))))
    case Con{S.Function{name,params,result,body},tail}: collect_types(tail,count)
    case _: C.internal(List<&2,C.Enum>,"type-declaration-node")

def distinct_constructors(tokens: List<&2,S.Token>, +seen: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  match tokens:
    case Nil{}: Done{seen}
    case Con{+h,+t}:
      S.choose(Result<S.Error,List<&2,S.Token>>,named(seen,h),u => C.invalid(List<&2,S.Token>,"duplicate-constructor",h),u => distinct_constructors(t,Con{h,seen}))

def unique_constructors(types: List<&2,C.Enum>, seen: List<&2,S.Token>) -> Result<S.Error,Unit>:
  match types:
    case Nil{}: Done{Unit{}}
    case Con{C.Enum{name,data,tokens},+tail}:
      S.bind(List<&2,S.Token>,Unit,distinct_constructors(tokens,seen),next => unique_constructors(tail,next))

def quantity(+token: S.Token, +q: U32, definition: C.Enum) -> Result<S.Error,Unit>:
  match definition:
    case C.Enum{name,data,ctors}:
      S.choose(Result<S.Error,Unit>,U32.is_gt(q,2),u => C.internal(Unit,"quantity-range"),u =>
        S.choose(Result<S.Error,Unit>,Bool.and(U32.is_eq(q,2),Bool.not(data)),u => C.invalid(Unit,"reusable-type",token),u => Done{Unit{}}))

def parameter_type(+token: S.Token, +q: U32, reference: TypeRef) -> Result<S.Error,C.Parameter>:
  match reference:
    case TypeRef{+index,definition}:
      S.bind(Unit,C.Parameter,quantity(token,q,definition),u => Done{C.Parameter{token,q,index}})

def parameters(nodes: List<&2,S.Node>, +types: List<&2,C.Enum>, +count: U32) -> Result<S.Error,List<&2,C.Parameter>>:
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

def collect_signatures(nodes: List<&2,S.Node>, +types: List<&2,C.Enum>, +count: U32) -> Result<S.Error,List<&2,C.Signature>>:
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

def catalog(root: S.Node) -> Result<S.Error,C.Catalog>:
  match root:
    case S.Sequence{+nodes}:
      S.bind(Unit,C.Catalog,names(nodes,Nil{}),u =>
        S.bind(List<&2,C.Enum>,C.Catalog,collect_types(nodes,0),+types =>
          S.bind(Unit,C.Catalog,unique_constructors(types,Nil{}),u =>
            S.bind(List<&2,C.Signature>,C.Catalog,collect_signatures(nodes,types,0),sigs => Done{C.Catalog{types,sigs}}))))
    case _: C.internal(C.Catalog,"book-node")
