import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./matrix.bend as M
import ./check.bend as K

# Independent observation: row identities only, with no generated fields,
# aliases, scopes or bodies. Specialization must be a stable selection.
def identities(rows: List<&2,S.Node>) -> List<&2,S.Token>:
  match rows:
    case Nil{}: Nil{}
    case Con{S.Arm{token,pattern,body},tail}: Con{token,identities(tail)}
    case Con{other,tail}: identities(tail)

def selected(rows: List<&2,S.Node>, +ctor: S.Token) -> List<&2,S.Token>:
  match rows:
    case Nil{}: Nil{}
    case Con{S.Arm{+arm,S.Sequence{Con{S.Constructor{token,args},rest}},body},+tail}:
      S.choose(List<&2,S.Token>,String.eq(S.text(token),S.text(ctor)),u => Con{arm,selected(tail,ctor)},u => selected(tail,ctor))
    case Con{S.Arm{arm,S.Sequence{Con{S.Variable{token},rest}},body},tail}: Con{arm,selected(tail,ctor)}
    case Con{S.Arm{arm,S.Sequence{Con{S.Promotion{token},rest}},body},tail}: Con{arm,selected(tail,ctor)}
    case Con{other,tail}: selected(tail,ctor)

# Auxiliary congruence, inhabited on either choice of keep.
law selection_congruence:
  for +keep: Bool
  for +arm: S.Token
  for pattern: S.Node
  for body: S.Node
  for +tail: List<&2,S.Node>
  for +wanted: List<&2,S.Token>
  for proof: {identities(tail) == wanted : List<&2,S.Token>}
  {identities(S.choose(List<&2,S.Node>,keep,u => Con{S.Arm{arm,pattern,body},tail},u => tail)) ==
    S.choose(List<&2,S.Token>,keep,u => Con{arm,wanted},u => wanted) : List<&2,S.Token>}

law specialization_preserves_first_match:
  for +rows: List<&2,S.Node>
  for +ctor: S.Token
  for +fields: List<&2,S.Node>
  for +level: U32
  {identities(M.specialize(rows,ctor,fields,level)) == selected(rows,ctor) : List<&2,S.Token>}

# Irrefutable heads survive both forms of column elimination at the head;
# once no columns remain the lowering selects that row's body.
law irrefutable_specialization:
  for +arm: S.Token
  for +name: S.Token
  for +rest: List<&2,S.Node>
  for +body: S.Node
  for +rows: List<&2,S.Node>
  for +ctor: S.Token
  for +fields: List<&2,S.Node>
  for +level: U32
  {M.specialize(Con{S.Arm{arm,S.Sequence{Con{S.Variable{name},rest}},body},rows},ctor,fields,level) ==
    Con{S.Arm{arm,S.Sequence{List.append(&2,S.Node,fields,rest)},M.bind_body(body,name,level,1)},M.specialize(rows,ctor,fields,level)} : List<&2,S.Node>}

law irrefutable_default:
  for +arm: S.Token
  for +name: S.Token
  for +rest: List<&2,S.Node>
  for +body: S.Node
  for +rows: List<&2,S.Node>
  for +level: U32
  {M.default_rows(Con{S.Arm{arm,S.Sequence{Con{S.Variable{name},rest}},body},rows},level) ==
    Con{S.Arm{arm,S.Sequence{rest},M.bind_body(body,name,level,1)},M.default_rows(rows,level)} : List<&2,S.Node>}

law first_row_selected:
  for token: S.Token
  for arm: S.Token
  for +body: S.Node
  for rows: List<&2,S.Node>
  for types: List<&2,C.Datatype>
  for scope: E.Scope
  {M.step(token,Nil{},Con{S.Arm{arm,S.Sequence{Nil{}},body},rows},1,types,scope) == Done{body} : Result<S.Error,S.Node>}

law lowering_work_exhaustion:
  for +token: S.Token
  for columns: List<&2,S.Node>
  for rows: List<&2,S.Node>
  for types: List<&2,C.Datatype>
  for scope: E.Scope
  {M.step(token,columns,rows,0,types,scope) == Fail{S.Exhausted{"check",S.at(token)}} : Result<S.Error,S.Node>}

# A literal inhabited two-constructor catalog supports complete lowering laws.
# These normalizations include checking, quantities and the emitted core tree.
def token(text: String) -> S.Token: S.Token{text,S.At{0,0,1,0}}
def flag() -> C.Datatype:
  C.Datatype{token("Flag"),True{},[C.Constructor{token("Off"),Nil{}},C.Constructor{token("On"),Nil{}}]}
def ctor(name: String) -> S.Node: S.Constructor{token(name),Nil{}}
def parameters() -> E.Scope:
  E.parameters([C.Parameter{token("x"),1,0},C.Parameter{token("y"),1,0}],0,Nil{})
def row(a: S.Node, b: S.Node, result: String) -> S.Node:
  S.Arm{token("case"),S.Sequence{[a,b]},ctor(result)}
def lower(rows: List<&2,S.Node>) -> Result<S.Error,C.Checked>:
  K.run(128n,K.Expression{S.Match{token("match"),S.Sequence{[S.Variable{token("x")},S.Variable{token("y")}]},rows},Some{0}},
    C.Catalog{[flag()],Nil{}},0,parameters())
def branches(off: U32, on: U32) -> List<&2,C.Term>:
  [C.Branch{0,Nil{},C.Value{token("Off"),0,off}},C.Branch{1,Nil{},C.Value{token("On"),0,on}}]

law irrefutable_lowering_witness:
  {lower([row(S.Variable{token("_")},S.Variable{token("_")},"On"),
          row(ctor("Off"),ctor("Off"),"Off")]) ==
    Done{C.Checked{C.Case{token("match"),0,0,[
      C.Branch{0,Nil{},C.Case{token("match"),1,0,[C.Branch{0,Nil{},C.Value{token("On"),0,1}},C.Branch{1,Nil{},C.Value{token("On"),0,1}}]}},
      C.Branch{1,Nil{},C.Value{token("On"),0,1}}]},0,[0,1]}} : Result<S.Error,C.Checked>}

law exhaustive_matrix_witness:
  {lower([row(ctor("Off"),ctor("Off"),"Off"),row(ctor("Off"),ctor("On"),"On"),
          row(ctor("On"),ctor("Off"),"On"),row(ctor("On"),ctor("On"),"Off")]) ==
    Done{C.Checked{C.Case{token("match"),0,0,[
      C.Branch{0,Nil{},C.Case{token("match"),1,0,[C.Branch{0,Nil{},C.Value{token("Off"),0,0}},C.Branch{1,Nil{},C.Value{token("On"),0,1}}]}},
      C.Branch{1,Nil{},C.Case{token("match"),1,0,[C.Branch{0,Nil{},C.Value{token("On"),0,1}},C.Branch{1,Nil{},C.Value{token("Off"),0,0}}]}}]},0,[0,1]}} : Result<S.Error,C.Checked>}

law erased_alias_stays_erased:
  for +name: S.Token
  for +alias: S.Token
  for +known: Maybe<&2,C.Term>
  {M.alias(E.Scope{[C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]},alias,1,2,[flag()]) ==
    Done{E.Scope{[C.Binding{alias,1,0,0,True{},known},C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]}} : Result<S.Error,E.Scope>}

law alias_preserves_descent_and_identity:
  for +name: S.Token
  for +alias: S.Token
  {M.alias(E.Scope{[C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]},alias,1,1,[flag()]) ==
    Done{E.Scope{[C.Binding{alias,1,1,0,True{},None{}},C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]}} : Result<S.Error,E.Scope>}

# Exhaustiveness at each split: every declaration absent from the explicit
# column is retained by the default matrix, in declaration order.
law default_completes_missing_branch:
  for +name: S.Token
  for fields: List<&2,C.Parameter>
  for +ctors: List<&2,C.Constructor>
  for +explicit: List<&2,S.Token>
  for absent: {M.named(explicit,name) == False{} : Bool}
  {M.defaults(Con{C.Constructor{name,fields},ctors},explicit) == Con{name,M.defaults(ctors,explicit)} : List<&2,S.Token>}

law default_does_not_repeat_explicit_branch:
  for +name: S.Token
  for fields: List<&2,C.Parameter>
  for +ctors: List<&2,C.Constructor>
  for +explicit: List<&2,S.Token>
  for present: {M.named(explicit,name) == True{} : Bool}
  {M.defaults(Con{C.Constructor{name,fields},ctors},explicit) == M.defaults(ctors,explicit) : List<&2,S.Token>}

law default_completion_witness:
  {M.signature(flag(),[token("Off")],True{}) == [token("Off"),token("On")] : List<&2,S.Token>}

law anonymous_reference_is_free:
  for scope: E.Scope
  for +at: S.At
  {E.lookup(scope,S.Token{"_",at}) == Fail{S.Invalid{"check","free-name",at}} : Result<S.Error,C.Binding>}

law default_reference_stays_live:
  for +name: S.Token
  for +level: U32
  for +q: U32
  for +type_id: U32
  for +live: Bool
  {E.occurrence(Some{C.Reference{name,level,type_id}},name,level,q,type_id,live) ==
    E.unknown(name,level,q,type_id,live) : Result<S.Error,C.Checked>}

law empty_reference_stays_live:
  for +name: S.Token
  for +level: U32
  for +q: U32
  for +type_id: U32
  for +live: Bool
  {E.occurrence(Some{C.Case{name,level,type_id,Nil{}}},name,level,q,type_id,live) ==
    E.unknown(name,level,q,type_id,live) : Result<S.Error,C.Checked>}

law erased_empty_is_not_dead:
  for +name: S.Token
  {E.dead(E.Scope{[C.Binding{name,0,0,0,True{},Some{C.Case{name,0,0,Nil{}}}}],1,[0],True{},Nil{}}) == False{} : Bool}

law live_empty_is_dead:
  for +name: S.Token
  {E.dead(E.Scope{[C.Binding{name,0,1,0,True{},Some{C.Case{name,0,0,Nil{}}}}],1,[0],True{},Nil{}}) == True{} : Bool}

# The most recent let supplies a variable-only column without constructor inspection.
law let_alias_available:
  for +name: S.Token
  for token: S.Token
  {M.variable_column(C.Binding{name,0,1,0,False{},None{}},
      E.Scope{[C.Binding{name,0,1,0,False{},None{}}],1,Nil{},True{},Nil{}},token) ==
    Done{C.Binding{name,0,1,0,False{},None{}}} : Result<S.Error,C.Binding>}

law terminal_expansion_preserves_budget:
  for +name: S.Token
  for types: List<&2,C.Datatype>
  for scope: E.Scope
  for +work: U32
  {M.expand(1n,S.Variable{name},types,scope,work) == Done{M.Expansion{S.Variable{name},work}} : Result<S.Error,M.Expansion>}

law leaf_expansion_spends_one:
  for token: S.Token
  for arm: S.Token
  for +name: S.Token
  for types: List<&2,C.Datatype>
  for scope: E.Scope
  {M.expand(2n,S.Matrix{token,Nil{},[S.Arm{arm,S.Sequence{Nil{}},S.Variable{name}}],1},types,scope,1) ==
    Done{M.Expansion{S.Variable{name},0}} : Result<S.Error,M.Expansion>}
