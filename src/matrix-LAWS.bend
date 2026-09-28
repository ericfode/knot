import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./patterns.bend as P
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

# Inhabits lowering-LAWS irrefutable_first_row_selected: the overlapping
# Off/Off row is shadowed at every leaf of the two-level lowering.
def wild() -> S.Node: S.Variable{token("_")}
def bound(body: S.Node) -> S.Node: S.Alias{token("_"),0,1,S.Alias{token("_"),1,1,body}}
def off(column: String, yes: S.Node, no: S.Node) -> S.Node: S.Decision{token("match"),S.Variable{token(column)},ctor("Off"),yes,no}

law irrefutable_first_row_witness:
  {M.expand(64n,S.Matrix{token("match"),[S.Variable{token("x")},S.Variable{token("y")}],
      [row(wild(),wild(),"On"),row(ctor("Off"),ctor("Off"),"Off")],4096},[flag()],parameters(),4096) ==
    Done{M.Expansion{off("x",off("y",bound(ctor("On")),bound(ctor("On"))),bound(ctor("On"))),4088}} : Result<S.Error,M.Expansion>}

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
  {M.alias(E.Scope{[C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]},alias,1,2) ==
    Done{E.Scope{[C.Binding{alias,1,0,0,True{},known},C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]}} : Result<S.Error,E.Scope>}

law alias_preserves_descent_and_identity:
  for +name: S.Token
  for +alias: S.Token
  {M.alias(E.Scope{[C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]},alias,1,1) ==
    Done{E.Scope{[C.Binding{alias,1,1,0,True{},None{}},C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]}} : Result<S.Error,E.Scope>}

# A `+` row raises a lambda-case binder with every alias of its level, and
# never raises a let binder: under any row mark, the let and its alias stay affine.
law parameter_alias_promotes:
  for +name: S.Token
  for +alias: S.Token
  {M.alias(E.Scope{[C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]},alias,1,2) ==
    Done{E.Scope{[C.Binding{alias,1,2,0,True{},None{}},C.Binding{name,1,2,0,True{},None{}}],2,[1],True{},[1]}} : Result<S.Error,E.Scope>}

law let_alias_keeps_quantity:
  for +name: S.Token
  for +alias: S.Token
  for +mark: U32
  for +known: Maybe<&2,C.Term>
  {M.alias(E.Scope{[C.Binding{name,0,1,0,False{},known}],1,Nil{},True{},Nil{}},alias,0,mark) ==
    Done{E.Scope{[C.Binding{alias,0,1,0,False{},known},C.Binding{name,0,1,0,False{},known}],1,Nil{},True{},Nil{}}} : Result<S.Error,E.Scope>}

# A `+` binder's kind is judged where the frontier binds it: never by a match
# on the binder itself, but by a match on a later binder or at a leaf body.
def mode() -> C.Datatype:
  C.Datatype{token("Mode"),False{},[C.Constructor{token("Lo"),Nil{}},C.Constructor{token("Hi"),Nil{}}]}
def promoted(name: S.Token) -> C.Binding: C.Binding{name,0,2,0,True{},None{}}
def frontier(name: S.Token, other: S.Token) -> E.Scope:
  E.Scope{[C.Binding{other,1,1,0,True{},None{}},promoted(name)],2,[0,1],True{},Nil{}}

law destructured_promotion_is_unbound:
  for +name: S.Token
  for +other: S.Token
  {P.advance(frontier(name,other),0,[mode()]) == Done{Unit{}} : Result<S.Error,Unit>}

law later_match_binds_promotion:
  for +name: S.Token
  for +other: S.Token
  {P.advance(frontier(name,other),1,[mode()]) == Fail{S.Invalid{"check","reusable-type",S.at(name)}} : Result<S.Error,Unit>}

law leaf_binds_promotion:
  for +name: S.Token
  {P.close(E.Scope{[promoted(name)],1,[0],True{},Nil{}},[mode()]) ==
    Fail{S.Invalid{"check","reusable-type",S.at(name)}} : Result<S.Error,E.Scope>}

law leaf_closes_frontier:
  for +name: S.Token
  {P.close(E.Scope{[promoted(name)],1,[0],True{},Nil{}},[flag()]) ==
    Done{E.Scope{[promoted(name)],1,Nil{},True{},Nil{}}} : Result<S.Error,E.Scope>}

# The whole checker at a Type kind. Destructuring a promoted binder, as a
# parameter or a field, leaves it unbound; returning it, a later matrix split
# and a later zero-row match each bind it, which is rejected.
def modes(types: List<&2,C.Datatype>, params: List<&2,C.Parameter>, body: S.Node) -> Result<S.Error,C.Checked>:
  K.run(64n,K.Expression{body,Some{0}},C.Catalog{Con{mode(),types},Nil{}},0,E.parameters(params,0,Nil{}))
def parameter(name: String, type_id: U32) -> C.Parameter: C.Parameter{token(name),1,type_id}
def named(name: String) -> S.Node: S.Variable{token(name)}
def plus(name: String) -> S.Node: S.Promotion{token(name)}
def arm(pattern: S.Node, body: S.Node) -> S.Node: S.Arm{token("case"),pattern,body}
def on(value: S.Node, arms: List<&2,S.Node>) -> S.Node: S.Match{token("match"),value,arms}
def promoting(body: S.Node) -> S.Node: on(named("m"),[arm(plus("y"),body)])
def mode_arms() -> List<&2,S.Node>: [arm(ctor("Lo"),ctor("Lo")),arm(ctor("Hi"),ctor("Hi"))]
def cased(level: U32, arms: List<&2,C.Term>) -> C.Term: C.Case{token("match"),level,0,arms}
def mode_branches() -> List<&2,C.Term>:
  [C.Branch{0,Nil{},C.Value{token("Lo"),0,0}},C.Branch{1,Nil{},C.Value{token("Hi"),0,1}}]
def wrap() -> C.Datatype: C.Datatype{token("Wrap"),False{},[C.Constructor{token("W"),[parameter("b",0)]}]}
def wrapped(field: S.Node) -> S.Node: S.Constructor{token("W"),[field]}
def raised_field() -> C.Binding: C.Binding{token("b"),1,2,0,True{},None{}}
def uninhabited() -> C.Datatype: C.Datatype{token("Void"),False{},Nil{}}
def rejected() -> Result<S.Error,C.Checked>: Fail{S.Invalid{"check","reusable-type",S.At{0,0,1,0}}}

law destructured_promotion_witness:
  {modes(Nil{},[parameter("m",0)],promoting(on(named("y"),mode_arms()))) ==
    Done{C.Checked{cased(0,mode_branches()),0,Nil{}}} : Result<S.Error,C.Checked>}

law destructured_field_promotion_witness:
  {modes([wrap()],[parameter("w",1)],on(named("w"),[arm(wrapped(plus("b")),on(named("b"),mode_arms()))])) ==
    Done{C.Checked{cased(0,[C.Branch{0,[raised_field()],cased(1,mode_branches())}]),0,[0]}} : Result<S.Error,C.Checked>}

law bound_promotion_witness:
  {modes(Nil{},[parameter("m",0)],promoting(named("y"))) == rejected() : Result<S.Error,C.Checked>}

law split_binds_promotion_witness:
  {modes(Nil{},[parameter("m",0),parameter("w",0)],on(S.Sequence{[named("m"),named("w")]},
    [arm(S.Sequence{[plus("y"),ctor("Lo")]},ctor("Lo")),arm(S.Sequence{[plus("y"),ctor("Hi")]},ctor("Hi"))])) ==
    rejected() : Result<S.Error,C.Checked>}

law empty_match_binds_promotion_witness:
  {modes([uninhabited()],[parameter("m",0),parameter("v",1)],promoting(on(named("v"),Nil{}))) == rejected() : Result<S.Error,C.Checked>}

# An unannotated let of a matched binder, through the whole checker. Where a
# positive branch has refined the binder, flat or in a matrix, the let needs an
# annotation; a residual binder and an annotated let are accepted.
def accepted(result: Result<S.Error,C.Checked>) -> Bool: Result.is_done(&1,&1,S.Error,C.Checked,result)
def unannotated() -> Result<S.Error,C.Checked>: Fail{S.Invalid{"check","annotation-required",S.At{0,0,1,0}}}
def mode_annotation() -> Maybe<&2,S.Token>: Some{token("Mode")}
def let_v(annotation: Maybe<&2,S.Token>, value: S.Node) -> S.Node: S.Binding{token("v"),1,annotation,value,named("v")}
def flat_let(annotation: Maybe<&2,S.Token>) -> Result<S.Error,C.Checked>:
  modes(Nil{},[parameter("m",0)],on(named("m"),[arm(ctor("Lo"),let_v(annotation,named("m"))),arm(ctor("Hi"),ctor("Hi"))]))
def matrix_let(annotation: Maybe<&2,S.Token>) -> Result<S.Error,C.Checked>:
  modes(Nil{},[parameter("m",0),parameter("n",0)],on(S.Sequence{[named("m"),named("n")]},
    [arm(S.Sequence{[ctor("Lo"),ctor("Lo")]},let_v(annotation,named("n"))),arm(S.Sequence{[wild(),wild()]},ctor("Hi"))]))
def residual_let() -> Result<S.Error,C.Checked>:
  modes(Nil{},[parameter("m",0),parameter("n",0)],on(S.Sequence{[named("m"),named("n")]},
    [arm(S.Sequence{[ctor("Lo"),wild()]},ctor("Lo")),arm(S.Sequence{[wild(),wild()]},let_v(None{},named("m")))]))

law refined_flat_let_witness:
  {flat_let(None{}) == unannotated() : Result<S.Error,C.Checked>}

law refined_matrix_let_witness:
  {matrix_let(None{}) == unannotated() : Result<S.Error,C.Checked>}

law residual_let_witness:
  {accepted(residual_let()) == True{} : Bool}

law annotated_let_witness:
  {[accepted(flat_let(mode_annotation())),accepted(matrix_let(mode_annotation()))] == [True{},True{}] : List<&2,Bool>}

# Exhaustiveness at each split: the positive matrix takes the split
# constructor, the remainder keeps every other available constructor in order,
# and the negative matrix drops only rows headed by the split constructor.
law remainder_omits_split:
  for +head: S.Token
  for +tail: List<&2,S.Token>
  for +ctor: S.Token
  for split: {S.matches(head,S.text(ctor)) == True{} : Bool}
  {M.remaining(Con{head,tail},ctor) == M.remaining(tail,ctor) : List<&2,S.Token>}

law remainder_keeps_other:
  for +head: S.Token
  for +tail: List<&2,S.Token>
  for +ctor: S.Token
  for other: {S.matches(head,S.text(ctor)) == False{} : Bool}
  {M.remaining(Con{head,tail},ctor) == Con{head,M.remaining(tail,ctor)} : List<&2,S.Token>}

law remainder_drops_split_rows:
  for +arm: S.Token
  for +token: S.Token
  for +args: List<&2,S.Node>
  for +rest: List<&2,S.Node>
  for +body: S.Node
  for +rows: List<&2,S.Node>
  for +ctor: S.Token
  for split: {S.matches(token,S.text(ctor)) == True{} : Bool}
  {M.without(Con{S.Arm{arm,S.Sequence{Con{S.Constructor{token,args},rest}},body},rows},ctor) == M.without(rows,ctor) : List<&2,S.Node>}

law irrefutable_remainder:
  for +arm: S.Token
  for +name: S.Token
  for +rest: List<&2,S.Node>
  for +body: S.Node
  for +rows: List<&2,S.Node>
  for +ctor: S.Token
  {M.without(Con{S.Arm{arm,S.Sequence{Con{S.Variable{name},rest}},body},rows},ctor) ==
    Con{S.Arm{arm,S.Sequence{Con{S.Variable{name},rest}},body},M.without(rows,ctor)} : List<&2,S.Node>}

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

# Dead code needs a live binder in context with an empty constructor set.
# A binder still pending at or after the scrutinee is not in context.
law pending_binder_witnesses_nothing:
  for +token: S.Token
  for +level: U32
  for +q: U32
  for +type_id: U32
  for +param: Bool
  for +known: Maybe<&2,C.Term>
  for +tail: List<&2,C.Binding>
  for +types: List<&2,C.Datatype>
  for +pending: List<&2,U32>
  for inside: {E.contains(pending,level) == True{} : Bool}
  {E.witnessed(Con{C.Binding{token,level,q,type_id,param,known},tail},types,pending) == E.witnessed(tail,types,pending) : Bool}

def void() -> C.Datatype: C.Datatype{token("V"),False{},Nil{}}

law erased_empty_is_not_dead:
  for +name: S.Token
  {E.dead(E.Scope{[C.Binding{name,0,0,0,True{},Some{C.Case{name,0,0,Nil{}}}}],2,[0,1],True{},Nil{}},[flag()],1) == False{} : Bool}

law live_empty_is_dead:
  for +name: S.Token
  {E.dead(E.Scope{[C.Binding{name,0,1,0,True{},Some{C.Case{name,0,0,Nil{}}}}],2,[0,1],True{},Nil{}},[flag()],1) == True{} : Bool}

# f(x: V, y: Flag) matching y is dead; f(y: Flag, x: V) matching y is not.
law introduced_empty_witness:
  {E.dead(E.parameters([C.Parameter{token("x"),1,1},C.Parameter{token("y"),1,0}],0,Nil{}),[flag(),void()],1) == True{} : Bool}

law pending_empty_witness:
  {E.dead(E.parameters([C.Parameter{token("y"),1,0},C.Parameter{token("x"),1,1}],0,Nil{}),[flag(),void()],0) == False{} : Bool}

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

# Descent through rebuilt occurrences. References keep the reference rule;
# only a rebuilt value is compared with the refinements in scope.
law reference_is_not_rebuilt:
  for token: S.Token
  for level: U32
  for type_id: U32
  for tail: List<&2,C.Term>
  for bindings: List<&2,C.Binding>
  for smaller: List<&2,U32>
  {E.rebuilt(Con{C.Reference{token,level,type_id},tail},bindings,smaller) == False{} : Bool}

# len's third row after its second row nested into t's field l: t (level 0)
# and l (1) are refined to Node, t's v (2) to Off and l's v (4) to On;
# l's own field (3) is unrefined. Levels 1 to 4 are strict descendants.
def ref(level: U32, type_id: U32) -> C.Term: C.Reference{token("r"),level,type_id}
def node(args: List<&2,C.Term>) -> C.Term:
  C.Construct{token("Node"),1,1,[C.Parameter{token("l"),1,1},C.Parameter{token("v"),1,0}],args}
def refined(level: U32, type_id: U32, known: Maybe<&2,C.Term>) -> C.Binding: C.Binding{token("x"),level,1,type_id,True{},known}
def descent() -> List<&2,C.Binding>:
  [refined(4,0,Some{C.Value{token("On"),0,1}}),refined(3,1,None{}),refined(2,0,Some{C.Value{token("Off"),0,0}}),
   refined(1,1,Some{node([ref(3,1),ref(4,0)])}),refined(0,1,Some{node([ref(1,1),ref(2,0)])})]
def rebuilt_l() -> C.Term: node([ref(3,1),C.Value{token("On"),0,1}])

law rebuilt_descendant_witness:
  {E.rebuilt([rebuilt_l()],descent(),[3,4,1,2]) == True{} : Bool}

law rebuilt_root_witness:
  {E.rebuilt([node([rebuilt_l(),C.Value{token("Off"),0,0}])],descent(),[3,4,1,2]) == False{} : Bool}

law changed_field_witness:
  {E.rebuilt([node([ref(3,1),C.Value{token("Off"),0,0}])],descent(),[3,4,1,2]) == False{} : Bool}

law retyped_constant_witness:
  {E.rebuilt([C.Value{token("Leaf"),1,0}],descent(),[3,4,1,2]) == False{} : Bool}

law rebuilt_descendant_call_witness:
  for +token: S.Token
  for +uses: List<&2,U32>
  {K.call_result(C.Checked{C.Sequence{[rebuilt_l()]},0,uses},token,0,0,0,E.Scope{descent(),5,Nil{},True{},[3,4,1,2]}) ==
    Done{C.Checked{C.Application{token,0,0,[rebuilt_l()]},0,uses}} : Result<S.Error,C.Checked>}
