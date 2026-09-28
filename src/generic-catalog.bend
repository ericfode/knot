import Base
import ./syntax.bend as S
import ./core.bend as C
import ./types.bend as T

type Parameter is Data:
  Parameter{token: S.Token, quantity: U32, domain: T.Expr}
type Symbol is Data:
  Symbol{token: S.Token, index: U32, domain: T.Expr}
type Constructor is Data:
  Constructor{token: S.Token, fields: List<&2,Parameter>}
type Family is Data:
  Family{token: S.Token, parameters: List<&2,Parameter>, kind: T.Expr, constructors: List<&2,Constructor>, generic: Bool}
type Signature is Data:
  Signature{token: S.Token, parameters: List<&2,Parameter>, result: T.Expr, body: S.Node}
type Catalog is Data:
  Catalog{families: List<&2,Family>, signatures: List<&2,Signature>}
type Typed is Data:
  Typed{value: T.Expr, kind: T.Expr}
type Named is Data:
  Named{index: U32, family: Family}
type FunctionRef is Data:
  FunctionRef{index: U32, signature: Signature}
type ConstructorRef is Data:
  ConstructorRef{family: U32, tag: U32, constructor: Constructor}
type Mode is Data:
  Expression{node: S.Node}
  Arguments{nodes: List<&2,S.Node>, parameters: List<&2,Parameter>, substitutions: List<&2,T.Binding>, index: U32, value: T.Expr, kind: T.Expr, token: S.Token}

def one() -> T.Expr: T.Quantity{T.QOne{}}
def many() -> T.Expr: T.Quantity{T.QMany{}}
def universe() -> T.Expr: T.Sort{one()}
def data() -> T.Expr: T.Sort{many()}

def replace(value: T.Expr, substitutions: List<&2,T.Binding>) -> T.Expr:
  T.normalize(T.subst(value,substitutions))

def is_quant(value: T.Expr) -> Bool:
  match value:
    case T.QuantType{}: True{}
    case _: False{}

def is_sort(value: T.Expr) -> Bool:
  match value:
    case T.Sort{q}: True{}
    case _: False{}

# Kind comparison identifies &0 and &1, but datatype arguments stay invariant.
def dominates(+actual: T.Expr, +wanted: T.Expr) -> Bool:
  match actual wanted:
    case _ T.Quantity{T.QZero{}}: True{}
    case _ T.Quantity{T.QOne{}}: True{}
    case T.Quantity{T.QMany{}} _: True{}
    case T.Meet{+a,+b} _:
      Bool.and(dominates(a,wanted),dominates(b,wanted))
    case _ T.Meet{+a,+b}:
      Bool.or(dominates(actual,a),dominates(actual,b))
    case _ _: T.equal(actual,wanted)

def fits(actual: T.Expr, wanted: T.Expr) -> Bool:
  match actual wanted:
    case T.Sort{a} T.Sort{b}: dominates(T.normalize(a),T.normalize(b))
    case +a +b: T.equal(T.normalize(a),T.normalize(b))

def demand(+token: S.Token, q: U32, +kind: T.Expr) -> Result<S.Error,Unit>:
  S.choose(Result<S.Error,Unit>,U32.is_eq(q,2),u =>
    S.choose(Result<S.Error,Unit>,fits(kind,data()),u => Done{Unit{}},u => C.invalid(Unit,"reusable-type",token)),u => Done{Unit{}})

def named(symbols: List<&2,Symbol>, +token: S.Token) -> Maybe<&2,Symbol>:
  match symbols:
    case Nil{}: None{}
    case Con{+head,+tail}:
      match head:
        case Symbol{name,index,domain}:
          S.choose(Maybe<&2,Symbol>,String.eq(S.text(name),S.text(token)),u => Some{head},u => named(tail,token))

def bound(symbols: List<&2,Symbol>, +index: U32) -> Result<S.Error,T.Expr>:
  match symbols:
    case Nil{}: C.internal(T.Expr,"type-variable")
    case Con{Symbol{token,id,+domain},+tail}:
      S.choose(Result<S.Error,T.Expr>,U32.is_eq(index,id),u => Done{domain},u => bound(tail,index))

def family_at(families: List<&2,Family>, +index: U32) -> Result<S.Error,Family>:
  match families:
    case Nil{}: C.internal(Family,"generic-family-index")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,Family>,U32.is_eq(index,0),u => Done{head},u => family_at(tail,U32.sub(index,1)))

def family_named(families: List<&2,Family>, +token: S.Token, +index: U32) -> Result<S.Error,Named>:
  match families:
    case Nil{}: C.invalid(Named,"unknown-type",token)
    case Con{+head,+tail}:
      match head:
        case Family{name,params,kind,ctors,generic}:
          S.choose(Result<S.Error,Named>,String.eq(S.text(name),S.text(token)),u => Done{Named{index,head}},u => family_named(tail,token,U32.add(index,1)))

def function_named(signatures: List<&2,Signature>, +token: S.Token, +index: U32) -> Result<S.Error,FunctionRef>:
  match signatures:
    case Nil{}: C.invalid(FunctionRef,"unknown-function",token)
    case Con{+head,+tail}:
      match head:
        case Signature{name,params,result,body}:
          S.choose(Result<S.Error,FunctionRef>,String.eq(S.text(name),S.text(token)),u => Done{FunctionRef{index,head}},u => function_named(tail,token,U32.add(index,1)))

def constructor_tag(constructors: List<&2,Constructor>, +token: S.Token, +index: U32) -> Maybe<&2,ConstructorRef>:
  match constructors:
    case Nil{}: None{}
    case Con{+head,+tail}:
      match head:
        case Constructor{name,fields}:
          S.choose(Maybe<&2,ConstructorRef>,String.eq(S.text(name),S.text(token)),u => Some{ConstructorRef{0,index,head}},u => constructor_tag(tail,token,U32.add(index,1)))

def constructor_next(found: Maybe<&2,ConstructorRef>, index: U32, next: Unit -> Result<S.Error,ConstructorRef>) -> Result<S.Error,ConstructorRef>:
  match found:
    case None{}: next(Unit{})
    case Some{ConstructorRef{ignored,tag,ctor}}: Done{ConstructorRef{index,tag,ctor}}

def constructor_named(families: List<&2,Family>, +token: S.Token, +index: U32) -> Result<S.Error,ConstructorRef>:
  match families:
    case Nil{}: C.invalid(ConstructorRef,"unknown-constructor",token)
    case Con{Family{name,params,kind,ctors,generic},+tail}:
      constructor_next(constructor_tag(ctors,token,0),index,u => constructor_named(tail,token,U32.add(index,1)))

def constructor_present(found: Maybe<&2,ConstructorRef>) -> Bool:
  match found:
    case None{}: False{}
    case Some{reference}: True{}

def has_constructor(families: List<&2,Family>, +token: S.Token) -> Bool:
  match families:
    case Nil{}: False{}
    case Con{Family{name,params,kind,ctors,generic},tail}:
      Bool.or(constructor_present(constructor_tag(ctors,token,0)),has_constructor(tail,token))

def positional(values: List<&2,T.Expr>, +index: U32) -> List<&2,T.Binding>:
  match values:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{T.Binding{index,head},positional(tail,U32.add(index,1))}

def family_kind(family: Family, args: List<&2,T.Expr>) -> Result<S.Error,T.Expr>:
  match family:
    case Family{token,params,kind,ctors,generic}: Done{replace(kind,positional(args,0))}

def kind_spine(expr: T.Expr, +args: List<&2,T.Expr>, +families: List<&2,Family>, +symbols: List<&2,Symbol>) -> Result<S.Error,T.Expr>:
  match expr:
    case T.Bound{index}: bound(symbols,index)
    case T.Family{index}:
      S.bind(Family,T.Expr,family_at(families,index),family => family_kind(family,args))
    case T.Apply{head,arg}: kind_spine(head,Con{arg,args},families,symbols)
    case T.Sort{q}: Done{universe()}
    case T.QuantType{}: Done{universe()}
    case T.Quantity{q}: Done{T.QuantType{}}
    case T.Meet{a,b}: Done{T.QuantType{}}

def kind(expr: T.Expr, families: List<&2,Family>, symbols: List<&2,Symbol>) -> Result<S.Error,T.Expr>:
  kind_spine(expr,Nil{},families,symbols)

def family_id(expr: T.Expr) -> Maybe<&2,U32>:
  match expr:
    case T.Family{index}: Some{index}
    case T.Apply{head,arg}: family_id(head)
    case _: None{}

def arguments(expr: T.Expr, tail: List<&2,T.Expr>) -> List<&2,T.Expr>:
  match expr:
    case T.Apply{head,arg}: arguments(head,Con{arg,tail})
    case _: tail

def instantiated(expr: T.Expr) -> List<&2,T.Binding>:
  positional(arguments(expr,Nil{}),0)

def source_offset(token: S.Token) -> U32:
  match token:
    case S.Token{text,S.At{start,end,line,column}}: start

def quantity_prefix(params: List<&2,Parameter>) -> U32:
  match params:
    case Con{Parameter{token,q,T.QuantType{}},tail}: U32.add(1,quantity_prefix(tail))
    case _: 0

def defaults(fuel: Nat, +token: S.Token, +q: U32, rest: List<&2,S.Node>) -> List<&2,S.Node>:
  match fuel:
    case 0n: rest
    case 1n+n: Con{S.Quantity{token,q},defaults(n,token,q,rest)}

def application_arguments(+token: S.Token, +nodes: List<&2,S.Node>, +params: List<&2,Parameter>, name: S.Token, +q: U32) -> Result<S.Error,List<&2,S.Node>>:
  +actual = U32.from_nat(List.length(&2,S.Node,nodes))
  +arity = U32.from_nat(List.length(&2,Parameter,params))
  +omitted = quantity_prefix(params)
  +visible = U32.is_ge(source_offset(token),source_offset(name))
  S.choose(Result<S.Error,List<&2,S.Node>>,Bool.and(U32.is_eq(q,2),Bool.or(U32.is_eq(omitted,0),Bool.not(visible))),u =>
    C.invalid(List<&2,S.Node>,"quantity-prefix",token),u =>
    S.choose(Result<S.Error,List<&2,S.Node>>,U32.is_eq(actual,arity),u =>
      Done{S.choose(List<&2,S.Node>,U32.is_eq(q,2),u =>
        defaults(U32.to_nat(omitted),token,2,List.drop(&2,S.Node,nodes,U32.to_nat(omitted))),u => nodes)},u =>
      S.choose(Result<S.Error,List<&2,S.Node>>,Bool.and(U32.is_eq(U32.add(actual,omitted),arity),visible),u =>
        Done{defaults(U32.to_nat(omitted),token,q,nodes)},u => C.invalid(List<&2,S.Node>,"type-arity",token))))

def named_type(found: Maybe<&2,Symbol>, +token: S.Token, next: Unit -> Result<S.Error,Typed>) -> Result<S.Error,Typed>:
  match found:
    case None{}: next(Unit{})
    case Some{Symbol{name,index,+domain}}:
      S.choose(Result<S.Error,Typed>,Bool.or(is_sort(domain),is_quant(domain)),u => Done{Typed{T.Bound{index},domain}},u => C.unsupported(Typed,"dependent-type",token))

def applied_name(found: Maybe<&2,Symbol>, token: S.Token, next: Unit -> Result<S.Error,Typed>) -> Result<S.Error,Typed>:
  match found:
    case None{}: next(Unit{})
    case Some{symbol}: C.unsupported(Typed,"type-variable-application",token)

def type_argument(+value: Typed, wanted: T.Expr, +token: S.Token) -> Result<S.Error,Typed>:
  match value:
    case Typed{term,actual}:
      S.choose(Result<S.Error,Typed>,fits(actual,wanted),u => Done{value},u => C.invalid(Typed,"kind-mismatch",token))

def type_value(value: Typed, +token: S.Token) -> Result<S.Error,T.Expr>:
  match value:
    case Typed{+term,domain}:
      S.choose(Result<S.Error,T.Expr>,is_sort(domain),u => Done{term},u => C.invalid(T.Expr,"expected-type",token))

def result_type(value: Typed, +token: S.Token) -> Result<S.Error,T.Expr>:
  S.bind(T.Expr,T.Expr,type_value(value,token),+domain =>
    S.choose(Result<S.Error,T.Expr>,Bool.or(is_sort(domain),is_quant(domain)),u =>
      C.unsupported(T.Expr,"type-level-definition",token),u => Done{domain}))

def quantum(+q: U32, +token: S.Token) -> Result<S.Error,Typed>:
  S.choose(Result<S.Error,Typed>,U32.is_eq(q,0),u => Done{Typed{T.Quantity{T.QZero{}},T.QuantType{}}},u =>
  S.choose(Result<S.Error,Typed>,U32.is_eq(q,1),u => Done{Typed{one(),T.QuantType{}}},u =>
  S.choose(Result<S.Error,Typed>,U32.is_eq(q,2),u => Done{Typed{many(),T.QuantType{}}},u => C.invalid(Typed,"quantity",token))))

def sort_value(value: Typed) -> Typed:
  match value:
    case Typed{term,domain}: Typed{T.Sort{term},universe()}

def meet_value(left: Typed, right: Typed) -> Typed:
  match left right:
    case Typed{a,x} Typed{b,y}: Typed{T.normalize(T.Meet{a,b}),T.QuantType{}}

def apply_start(reference: Named, +token: S.Token, nodes: List<&2,S.Node>, q: U32, next: Mode -> Result<S.Error,Typed>) -> Result<S.Error,Typed>:
  match reference:
    case Named{index,Family{name,+params,+kind,ctors,generic}}:
      S.bind(List<&2,S.Node>,Typed,application_arguments(token,nodes,params,name,q),args =>
        next(Arguments{args,params,Nil{},0,T.Family{index},kind,token}))

# Quantity defaults belong to an explicit Name<..>; a bare name has no arguments.
def bare(reference: Named, token: S.Token, next: Mode -> Result<S.Error,Typed>) -> Result<S.Error,Typed>:
  match reference:
    case Named{index,Family{name,Nil{},kind,ctors,generic}}:
      next(Arguments{Nil{},Nil{},Nil{},0,T.Family{index},kind,token})
    case _: C.invalid(Typed,"type-arity",token)

def apply_argument(value: Typed, tail: List<&2,S.Node>, rest: List<&2,Parameter>, substitutions: List<&2,T.Binding>, +index: U32, head: T.Expr, kind: T.Expr, token: S.Token, next: Mode -> Result<S.Error,Typed>) -> Result<S.Error,Typed>:
  match value:
    case Typed{+term,domain}:
      next(Arguments{tail,rest,Con{T.Binding{index,term},substitutions},U32.add(index,1),T.Apply{head,term},kind,token})

def resolve(fuel: Nat, mode: Mode, +families: List<&2,Family>, +symbols: List<&2,Symbol>) -> Result<S.Error,Typed>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ +n Expression{S.Variable{+token}}:
      named_type(named(symbols,token),token,u =>
        S.bind(Named,Typed,family_named(families,token,0),reference => bare(reference,token,mode => resolve(n,mode,families,symbols))))
    case 1n+ +n Expression{S.TypeApply{+token,+args,+q}}:
      applied_name(named(symbols,token),token,u =>
        S.bind(Named,Typed,family_named(families,token,0),reference => apply_start(reference,token,args,q,mode => resolve(n,mode,families,symbols))))
    case 1n+n Expression{S.Quantity{token,q}}: quantum(q,token)
    case 1n+n Expression{S.QuantType{token}}: Done{Typed{T.QuantType{},universe()}}
    case 1n+ +n Expression{S.TypeKind{+token,q}}:
      S.bind(Typed,Typed,resolve(n,Expression{q},families,symbols),value =>
        S.bind(Typed,Typed,type_argument(value,T.QuantType{},token),typed => Done{sort_value(typed)}))
    case 1n+ +n Expression{S.Meet{+token,a,+b}}:
      S.bind(Typed,Typed,resolve(n,Expression{a},families,symbols),value =>
        S.bind(Typed,Typed,type_argument(value,T.QuantType{},token),left =>
          S.bind(Typed,Typed,resolve(n,Expression{b},families,symbols),value =>
            S.bind(Typed,Typed,type_argument(value,T.QuantType{},token),right => Done{meet_value(left,right)}))))
    case 1n+n Expression{S.Call{token,args}}: C.unsupported(Typed,"type-level-definition",token)
    case 1n+n Expression{S.Constructor{token,args}}: C.unsupported(Typed,"type-expression",token)
    case 1n+n Expression{S.Promotion{token}}: C.unsupported(Typed,"type-expression",token)
    case 1n+n Expression{S.Binding{token,q,ann,value,body}}: C.unsupported(Typed,"type-expression",token)
    case 1n+n Expression{S.TypedBinding{token,q,ann,value,body}}: C.unsupported(Typed,"type-expression",token)
    case 1n+n Expression{S.Match{token,value,arms}}: C.unsupported(Typed,"type-expression",token)
    case 1n+n Expression{other}: C.internal(Typed,"type-expression-node")
    case 1n+n Arguments{Nil{},Nil{},substitutions,index,value,kind,token}:
      Done{Typed{value,replace(kind,substitutions)}}
    case 1n+ +n Arguments{Con{head,+tail},Con{Parameter{name,q,domain},+rest},+substitutions,+index,+value,+kind,+token}:
      S.bind(Typed,Typed,resolve(n,Expression{head},families,symbols),arg =>
        S.bind(Typed,Typed,type_argument(arg,replace(domain,substitutions),token),typed =>
          apply_argument(typed,tail,rest,substitutions,index,value,kind,token,mode => resolve(n,mode,families,symbols))))
    case 1n+n Arguments{nodes,params,substitutions,index,value,kind,token}: C.invalid(Typed,"type-arity",token)

def expression(depth: Nat, node: S.Node, families: List<&2,Family>, symbols: List<&2,Symbol>) -> Result<S.Error,Typed>:
  resolve(depth,Expression{node},families,symbols)

def symbols(params: List<&2,Parameter>, +index: U32, env: List<&2,Symbol>) -> List<&2,Symbol>:
  match params:
    case Nil{}: env
    case Con{Parameter{token,q,domain},tail}: symbols(tail,U32.add(index,1),Con{Symbol{token,index,domain},env})

def parameter_node(node: S.Node, next: S.Token -> U32 -> S.Node -> Result<S.Error,List<&2,Parameter>>) -> Result<S.Error,List<&2,Parameter>>:
  match node:
    case S.Parameter{token,q,name}: next(token,q,S.Variable{name})
    case S.TypedParameter{token,q,typ}: next(token,q,typ)
    case _: C.internal(List<&2,Parameter>,"generic-parameter-node")

def parameter_value(typed: Typed, +token: S.Token, +q: U32, next: T.Expr -> Result<S.Error,List<&2,Parameter>>) -> Result<S.Error,List<&2,Parameter>>:
  match typed:
    case Typed{+domain,+kind}:
      S.choose(Result<S.Error,List<&2,Parameter>>,is_sort(kind),u =>
        S.choose(Result<S.Error,List<&2,Parameter>>,Bool.and(U32.is_ne(q,0),Bool.or(is_sort(domain),is_quant(domain))),u =>
          C.unsupported(List<&2,Parameter>,"live-type-parameter",token),u =>
          S.bind(Unit,List<&2,Parameter>,demand(token,q,kind),u => next(domain))),u => C.invalid(List<&2,Parameter>,"expected-type",token))

def parameters(nodes: List<&2,S.Node>, +families: List<&2,Family>, +env: List<&2,Symbol>, +index: U32, +depth: Nat) -> Result<S.Error,List<&2,Parameter>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{node,+tail}:
      parameter_node(node,+token => +q => typ =>
        S.choose(Result<S.Error,List<&2,Parameter>>,U32.is_ge(index,256),u => C.exhausted(List<&2,Parameter>,token),u =>
          S.bind(Typed,List<&2,Parameter>,expression(depth,typ,families,env),typed =>
            parameter_value(typed,token,q,+domain =>
              S.bind(List<&2,Parameter>,List<&2,Parameter>,parameters(tail,families,Con{Symbol{token,index,domain},env},U32.add(index,1),depth),rest =>
                Done{Con{Parameter{token,q,domain},rest}})))))

def header_parts(node: S.Node, next: S.Token -> List<&2,S.Node> -> S.Node -> List<&2,S.Node> -> Bool -> Result<S.Error,List<&2,Family>>) -> Result<S.Error,List<&2,Family>>:
  match node:
    case S.Datatype{+token,data,ctors}: next(token,Nil{},S.TypeKind{token,S.Quantity{token,Bool.pick(U32,data,2,1)}},ctors,False{})
    case S.Generic{token,+params,kind,ctors}:
      next(token,params,kind,ctors,Bool.not(Nat.is_eq(List.length(&2,S.Node,params),0n)))
    case _: C.internal(List<&2,Family>,"generic-header-node")

def constructor_headers(nodes: List<&2,S.Node>, +count: U32) -> Result<S.Error,List<&2,Constructor>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Constructor{+token,fields},+tail}:
      S.choose(Result<S.Error,List<&2,Constructor>>,U32.is_ge(count,256),u => C.exhausted(List<&2,Constructor>,token),u =>
        S.bind(List<&2,Constructor>,List<&2,Constructor>,constructor_headers(tail,U32.add(count,1)),rest => Done{Con{Constructor{token,Nil{}},rest}}))
    case _: C.internal(List<&2,Constructor>,"generic-constructor-node")

# A family without constructors is Unsupported, like the monomorphic catalog's.
def header_kind(typed: Typed, +token: S.Token, +params: List<&2,Parameter>, +ctors: List<&2,S.Node>, generic: Bool) -> Result<S.Error,Family>:
  match typed:
    case Typed{+kind,domain}:
      S.choose(Result<S.Error,Family>,is_sort(kind),u =>
        S.choose(Result<S.Error,Family>,Nat.is_eq(List.length(&2,S.Node,ctors),0n),u => C.unsupported(Family,"empty-datatype",token),u =>
          S.bind(List<&2,Constructor>,Family,constructor_headers(ctors,0),cs => Done{Family{token,params,kind,cs,generic}})),u => C.unsupported(Family,"dependent-kind",token))

def header_parameters(nodes: List<&2,S.Node>) -> Result<S.Error,Unit>:
  match nodes:
    case Nil{}: Done{Unit{}}
    case Con{S.TypedParameter{token,q,S.TypeKind{mark,kind}},tail}: header_parameters(tail)
    case Con{S.TypedParameter{token,q,S.QuantType{mark}},tail}: header_parameters(tail)
    case Con{S.TypedParameter{token,q,domain},tail}: C.unsupported(Unit,"generic-value-parameter",token)
    case Con{S.Parameter{token,q,domain},tail}: C.unsupported(Unit,"generic-value-parameter",token)
    case _: C.internal(Unit,"generic-parameter-node")

def headers(nodes: List<&2,S.Node>, +index: U32, +depth: Nat) -> Result<S.Error,List<&2,Family>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Function{name,params,result,body},tail}: headers(tail,index,depth)
    case Con{S.TypedFunction{name,params,result,body},tail}: headers(tail,index,depth)
    case Con{node,+tail}:
      header_parts(node,+token => +params => +kind => +ctors => +generic =>
        S.choose(Result<S.Error,List<&2,Family>>,U32.is_ge(index,256),u => C.exhausted(List<&2,Family>,token),u =>
          S.bind(Unit,List<&2,Family>,header_parameters(params),u =>
            S.bind(List<&2,Parameter>,List<&2,Family>,parameters(params,Nil{},Nil{},0,depth),+ps =>
              S.bind(Typed,List<&2,Family>,expression(depth,kind,Nil{},symbols(ps,0,Nil{})),typed =>
                S.bind(Family,List<&2,Family>,header_kind(typed,token,ps,ctors,generic),family =>
                  S.bind(List<&2,Family>,List<&2,Family>,headers(tail,U32.add(index,1),depth),rest => Done{Con{family,rest}})))))))

def token_seen(tokens: List<&2,S.Token>, +token: S.Token) -> Bool:
  match tokens:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(String.eq(S.text(head),S.text(token)),token_seen(tail,token))

def declaration_name(node: S.Node) -> S.Token:
  match node:
    case S.Datatype{token,kind,ctors}: token
    case S.Generic{token,params,kind,ctors}: token
    case S.Function{token,params,result,body}: token
    case S.TypedFunction{token,params,result,body}: token
    case _: S.Token{"",S.At{0,0,0,0}}

def unique_names(nodes: List<&2,S.Node>, +seen: List<&2,S.Token>) -> Result<S.Error,Unit>:
  match nodes:
    case Nil{}: Done{Unit{}}
    case Con{head,+tail}:
      +token = declaration_name(head)
      S.choose(Result<S.Error,Unit>,token_seen(seen,token),u => C.invalid(Unit,"duplicate-global",token),u => unique_names(tail,Con{token,seen}))

def unique_constructors(ctors: List<&2,Constructor>, +seen: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  match ctors:
    case Nil{}: Done{seen}
    case Con{Constructor{+token,params},+tail}:
      S.choose(Result<S.Error,List<&2,S.Token>>,token_seen(seen,token),u => C.invalid(List<&2,S.Token>,"duplicate-constructor",token),u => unique_constructors(tail,Con{token,seen}))

def unique_families(families: List<&2,Family>, seen: List<&2,S.Token>) -> Result<S.Error,Unit>:
  match families:
    case Nil{}: Done{Unit{}}
    case Con{Family{name,params,kind,ctors,generic},+tail}:
      S.bind(List<&2,S.Token>,Unit,unique_constructors(ctors,seen),next => unique_families(tail,next))

def field_kinds(params: List<&2,Parameter>, +parent: T.Expr, +families: List<&2,Family>, +env: List<&2,Symbol>, +seen: List<&2,S.Token>) -> Result<S.Error,Unit>:
  match params:
    case Nil{}: Done{Unit{}}
    case Con{Parameter{+token,+q,+domain},+tail}:
      S.choose(Result<S.Error,Unit>,token_seen(seen,token),u => C.invalid(Unit,"duplicate-field",token),u =>
        S.choose(Result<S.Error,Unit>,Bool.or(is_sort(domain),is_quant(domain)),u => C.unsupported(Unit,"dependent-field",token),u =>
          S.bind(T.Expr,Unit,kind(domain,families,env),child =>
            S.choose(Result<S.Error,Unit>,Bool.or(U32.is_eq(q,0),fits(child,parent)),u => field_kinds(tail,parent,families,env,Con{token,seen}),u => C.invalid(Unit,"data-field-kind",token)))))

def resolve_constructors(nodes: List<&2,S.Node>, +families: List<&2,Family>, +parent: T.Expr, +env: List<&2,Symbol>, +depth: Nat) -> Result<S.Error,List<&2,Constructor>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Constructor{+token,fields},+tail}:
      S.bind(List<&2,Parameter>,List<&2,Constructor>,parameters(fields,families,env,0,depth),+ps =>
        S.bind(Unit,List<&2,Constructor>,field_kinds(ps,parent,families,env,Nil{}),u =>
          S.bind(List<&2,Constructor>,List<&2,Constructor>,resolve_constructors(tail,families,parent,env,depth),rest => Done{Con{Constructor{token,ps},rest}})))
    case _: C.internal(List<&2,Constructor>,"generic-constructor-node")

def family_body(family: Family, node: S.Node, families: List<&2,Family>, depth: Nat) -> Result<S.Error,Family>:
  match family node:
    case Family{+token,+params,+kind,old,+generic} S.Datatype{name,data,ctors}:
      S.bind(List<&2,Constructor>,Family,resolve_constructors(ctors,families,kind,symbols(params,0,Nil{}),depth),cs => Done{Family{token,params,kind,cs,generic}})
    case Family{+token,+params,+kind,old,+generic} S.Generic{name,ps,k,ctors}:
      S.bind(List<&2,Constructor>,Family,resolve_constructors(ctors,families,kind,symbols(params,0,Nil{}),depth),cs => Done{Family{token,params,kind,cs,generic}})
    case _ _: C.internal(Family,"generic-family-node")

def bodies(nodes: List<&2,S.Node>, remaining: List<&2,Family>, +families: List<&2,Family>, +depth: Nat) -> Result<S.Error,List<&2,Family>>:
  match nodes remaining:
    case Nil{} Nil{}: Done{Nil{}}
    case Con{S.Function{name,params,result,body},tail} _: bodies(tail,remaining,families,depth)
    case Con{S.TypedFunction{name,params,result,body},tail} _: bodies(tail,remaining,families,depth)
    case Con{head,+tail} Con{family,+rest}:
      S.bind(Family,List<&2,Family>,family_body(family,head,families,depth),resolved =>
        S.bind(List<&2,Family>,List<&2,Family>,bodies(tail,rest,families,depth),more => Done{Con{resolved,more}}))
    case _ _: C.internal(List<&2,Family>,"generic-family-alignment")

def function_parts(node: S.Node, next: S.Token -> List<&2,S.Node> -> S.Node -> S.Node -> Result<S.Error,List<&2,Signature>>) -> Result<S.Error,List<&2,Signature>>:
  match node:
    case S.Function{token,params,result,body}: next(token,params,S.Variable{result},body)
    case S.TypedFunction{token,params,result,body}: next(token,params,result,body)
    case _: C.internal(List<&2,Signature>,"generic-function-node")

def signatures(nodes: List<&2,S.Node>, +families: List<&2,Family>, +index: U32, +depth: Nat) -> Result<S.Error,List<&2,Signature>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Datatype{token,kind,ctors},tail}: signatures(tail,families,index,depth)
    case Con{S.Generic{token,params,kind,ctors},tail}: signatures(tail,families,index,depth)
    case Con{node,+tail}:
      function_parts(node,+token => params => +result => +body =>
        S.choose(Result<S.Error,List<&2,Signature>>,U32.is_ge(index,256),u => C.exhausted(List<&2,Signature>,token),u =>
          S.bind(List<&2,Parameter>,List<&2,Signature>,parameters(params,families,Nil{},0,depth),+ps =>
            S.bind(Typed,List<&2,Signature>,expression(depth,result,families,symbols(ps,0,Nil{})),typed =>
              S.bind(T.Expr,List<&2,Signature>,result_type(typed,token),domain =>
                S.bind(List<&2,Signature>,List<&2,Signature>,signatures(tail,families,U32.add(index,1),depth),rest =>
                  Done{Con{Signature{token,ps,domain,body},rest}}))))))

def catalog(+depth: Nat, +nodes: List<&2,S.Node>) -> Result<S.Error,Catalog>:
  S.bind(Unit,Catalog,unique_names(nodes,Nil{}),u =>
    S.bind(List<&2,Family>,Catalog,headers(nodes,0,depth),+heads =>
      S.bind(Unit,Catalog,unique_families(heads,Nil{}),u =>
        S.bind(List<&2,Family>,Catalog,bodies(nodes,heads,heads,depth),+families =>
          S.bind(List<&2,Signature>,Catalog,signatures(nodes,families,0,depth),sigs => Done{Catalog{families,sigs}})))))
