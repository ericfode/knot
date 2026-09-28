import Base
import ./syntax.bend as S
import ./core.bend as C
import ./types.bend as T
import ./generic-catalog.bend as G
import ./type-erasure.bend as E
import ./eval.bend as V
import ./wasm.bend as W

# The generic catalog keeps the monomorphic catalog's empty-datatype boundary.
law empty_family:
  for token: S.Token
  for q: T.Expr
  for kind: T.Expr
  for params: List<&2,G.Parameter>
  for generic: Bool
  {G.header_kind(G.Typed{T.Sort{q},kind},token,params,Nil{},generic)
    == Fail{S.Unsupported{"check","empty-datatype",S.at(token)}} : Result<S.Error,G.Family>}

# A type name that resolves to a definition computes a type: Unsupported,
# whatever families the book declares.
law type_level_definition:
  for fuel: Nat
  for +token: S.Token
  for name: S.Token
  for families: List<&2,G.Family>
  for symbols: List<&2,G.Symbol>
  for found: {G.named(symbols,token) == Some{G.Definition{name}} : Maybe<&2,G.Symbol>}
  {G.resolve(1n+fuel,G.Expression{S.Variable{token}},families,symbols)
    == Fail{S.Unsupported{"check","type-level-definition",S.at(token)}} : Result<S.Error,G.Typed>}

law nominal_identity:
  for +index: U32
  {E.type_id(T.Family{index}) == index : U32}

law application_erases_argument:
  for +function: T.Expr
  for argument: T.Expr
  {E.type_id(T.Apply{function,argument}) == E.type_id(function) : U32}

law parameter_retains_quantity:
  for +token: S.Token
  for +q: U32
  for +typ: T.Expr
  {E.parameter(G.Parameter{token,q,typ}) == C.Parameter{token,q,E.type_id(typ)} : C.Parameter}

law plain_fields:
  for token: S.Token
  for +params: List<&2,G.Parameter>
  {E.fields(token,params,False{}) == E.parameters(params) : List<&2,C.Parameter>}

law plain_arguments:
  for token: S.Token
  for +args: List<&2,C.Term>
  {E.arguments(token,args,False{}) == args : List<&2,C.Term>}

law plain_bindings:
  for token: S.Token
  for +params: List<&2,C.Binding>
  {E.bindings(token,params,False{}) == params : List<&2,C.Binding>}

law generic_fields:
  for +token: S.Token
  for +params: List<&2,G.Parameter>
  {E.fields(token,params,True{}) ==
   List.append(&2,C.Parameter,E.parameters(params),[C.Parameter{token,0,0}]) : List<&2,C.Parameter>}

law generic_arguments:
  for +token: S.Token
  for +args: List<&2,C.Term>
  {E.arguments(token,args,True{}) ==
   List.append(&2,C.Term,args,[C.Value{token,0,0}]) : List<&2,C.Term>}

law generic_bindings:
  for +token: S.Token
  for +params: List<&2,C.Binding>
  {E.bindings(token,params,True{}) ==
   List.append(&2,C.Binding,params,[C.Binding{token,0,0,0,False{},None{}}]) : List<&2,C.Binding>}

law generic_nullary_is_boxed:
  for +token: S.Token
  for +typ: T.Expr
  for +tag: U32
  {E.construct(token,typ,tag,Nil{},Nil{},True{}) ==
   C.Construct{token,E.type_id(typ),tag,[C.Parameter{token,0,0}],[C.Value{token,0,0}]} : C.Term}

law plain_nullary_is_ordinal:
  for +token: S.Token
  for +typ: T.Expr
  for +tag: U32
  {E.construct(token,typ,tag,Nil{},Nil{},False{}) == C.Value{token,E.type_id(typ),tag} : C.Term}

law generic_constructor_uses_memory:
  for +token: S.Token
  for params: List<&2,G.Parameter>
  {W.fielded([C.Constructor{token,E.fields(token,params,True{})}]) == True{} : Bool}

law generic_branch_uses_memory:
  for token: S.Token
  for params: List<&2,C.Binding>
  for tag: U32
  for body: C.Term
  {W.fielded_arms([C.Branch{tag,E.bindings(token,params,True{}),body}]) == True{} : Bool}

law marker_retains_live_signature:
  for +token: S.Token
  for +params: List<&2,G.Parameter>
  {W.live_types(E.fields(token,params,True{})) == W.live_types(E.parameters(params)) : List<&2,U32>}

law erased_argument_commutes:
  for +fuel: Nat
  for token: S.Token
  for typ: U32
  for +params: List<&2,C.Parameter>
  for head: C.Term
  for +args: List<&2,C.Term>
  for +level: U32
  for +caller: List<&2,V.Entry>
  for +callee: List<&2,V.Entry>
  for +body: C.Term
  for +frames: List<&2,V.Frame>
  for +book: C.Book
  {V.run(1n+fuel,V.Arguments{Con{C.Parameter{token,0,typ},params},Con{head,args},level,caller,callee,body,frames},book) ==
   V.run(fuel,V.Arguments{params,args,U32.add(level,1),caller,callee,body,frames},book) : Result<S.Error,V.Value>}

law erased_field_commutes:
  for +fuel: Nat
  for +type_id: U32
  for +tag: U32
  for token: S.Token
  for typ: U32
  for +params: List<&2,C.Parameter>
  for head: C.Term
  for +args: List<&2,C.Term>
  for +env: List<&2,V.Entry>
  for +values: List<&2,V.Value>
  for +frames: List<&2,V.Frame>
  for +book: C.Book
  {V.run(1n+fuel,V.Fields{type_id,tag,Con{C.Parameter{token,0,typ},params},Con{head,args},env,values,frames},book) ==
   V.run(fuel,V.Fields{type_id,tag,params,args,env,values,frames},book) : Result<S.Error,V.Value>}

law erased_pattern_commutes:
  for +fuel: Nat
  for token: S.Token
  for level: U32
  for typ: U32
  for parameter: Bool
  for known: Maybe<&2,C.Term>
  for +params: List<&2,C.Binding>
  for +values: List<&2,V.Value>
  for +env: List<&2,V.Entry>
  for +body: C.Term
  for +frames: List<&2,V.Frame>
  for +book: C.Book
  {V.run(1n+fuel,V.Unpack{Con{C.Binding{token,level,0,typ,parameter,known},params},values,env,body,frames},book) ==
   V.run(fuel,V.Unpack{params,values,env,body,frames},book) : Result<S.Error,V.Value>}
