<!-- prechecks packet v1; rule=required-laws-met; increment=generics; head=78c4942e642a; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/LAWS.bend@78c4942e sha256=10f1684116f8035597113700ec874f5c0ab3ddea109689e074dc265c3a960902; src/type-erasure-LAWS.bend@78c4942e sha256=aeb9420e29e361ac03c60aea2cf097a68de588e6345c85d20f0a700c4c9be3f9; src/types-LAWS.bend@78c4942e sha256=4ca28bccb97831e118050b939e727aab92b0da430c13ba5ed4c6f672bbf286ab -->
# Claim
Required laws (verbatim from the increment manifest):

- Universal raw substitution composition, finite quantity meet laws and erased evaluator steps with explicit fuel; differential corpus agreement is finite, not compiler soundness.

# Evidence
Operation-to-law matrix computed from the sources:

| file | law | for-binders | PROOF filled | statement |
|---|---|---|---|---|
| src/LAWS.bend | empty_source | 1 | yes | {L.tokenize(fuel,"") == Done{[S.Token{"<eof>",S.At{0,0,1,0}}]} : Result<S.Error,List<&2,S.Token>>} |
| src/LAWS.bend | word_source | 1 | yes | {L.tokenize(1n+extra,"a") == Done{[S.Token{"a",S.At{0,1,1,0}},S.Token{"<eof>",S.At{1,1,1,1}}]} : Result<S.Erro |
| src/LAWS.bend | no_character_budget | 2 | yes | {L.tokenize(0n,SCon{c,tail}) == Fail{S.Exhausted{"lex",S.At{0,0,1,0}}} : Result<S.Error,List<&2,S.Token>>} |
| src/LAWS.bend | no_parser_budget | 1 | yes | {P.parse(0n,tokens) == Fail{S.Exhausted{"parse",S.here(tokens)}} : Result<S.Error,P.Parsed>} # Parser-only hea |
| src/LAWS.bend | generic_header | 1 | yes | {P.run(32n,P.Header{S.Token{"type",at},S.Token{"Box",at}}, [S.Token{"<",at},S.Token{"-",at},S.Token{"A",at},S. |
| src/LAWS.bend | multiple_scrutinees | 2 | yes | {P.run(1n,P.MatchTail{S.Token{"match",at},S.Variable{S.Token{"a",at}},0},Con{S.Token{"b",at},rest}) == Fail{S. |
| src/LAWS.bend | template_binder | 2 | yes | {P.run(1n,P.Parameters{")"},Con{S.Token{"~",at},Con{S.Token{"x",at},Con{S.Token{":",at},rest}}}) == Fail{S.Uns |
| src/LAWS.bend | nonleading_template_binder | 3 | yes | {P.run(1n,P.ListTail{")",head,True{},False{}},Con{S.Token{",",at},Con{S.Token{"~",at},rest}}) == Fail{S.Invali |
| src/LAWS.bend | destructuring_binding | 4 | yes | {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},rest}) == Fail{S.Unsupported{"parse","de |
| src/LAWS.bend | equality_is_not_binding | 3 | yes | {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},Con{S.Token{"=",at},rest}}) == Fail{S.In |
| src/LAWS.bend | arrow_is_not_binding | 3 | yes | {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},Con{S.Token{">",at},rest}}) == Fail{S.In |
| src/LAWS.bend | parameter_type_application | 2 | yes | {P.parameter(Con{S.Token{"xs",at},Con{S.Token{":",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}}) ==  |
| src/LAWS.bend | return_type_application | 3 | yes | {P.run(1n+n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}}, Con{S.Token{"-",at},Con{S.Token{">",at},Con{ |
| src/LAWS.bend | local_import | 2 | yes | {P.run(1n,P.Header{S.Token{"import",at},S.Token{".",at}},Con{S.Token{"/",at},rest}) == Fail{S.Unsupported{"par |
| src/LAWS.bend | hash_import | 2 | yes | {P.run(1n,P.Header{S.Token{"import",at},S.Token{"0x77a1a37baca5d86f62241cab956a1fb1",at}},Con{S.Token{"/",at}, |
| src/type-erasure-LAWS.bend | nominal_identity | 1 | yes | {E.type_id(T.Family{index}) == index : U32} |
| src/type-erasure-LAWS.bend | application_erases_argument | 2 | yes | {E.type_id(T.Apply{function,argument}) == E.type_id(function) : U32} |
| src/type-erasure-LAWS.bend | parameter_retains_quantity | 3 | yes | {E.parameter(G.Parameter{token,q,typ}) == C.Parameter{token,q,E.type_id(typ)} : C.Parameter} |
| src/type-erasure-LAWS.bend | plain_fields | 2 | yes | {E.fields(token,params,False{}) == E.parameters(params) : List<&2,C.Parameter>} |
| src/type-erasure-LAWS.bend | plain_arguments | 2 | yes | {E.arguments(token,args,False{}) == args : List<&2,C.Term>} |
| src/type-erasure-LAWS.bend | plain_bindings | 2 | yes | {E.bindings(token,params,False{}) == params : List<&2,C.Binding>} |
| src/type-erasure-LAWS.bend | generic_fields | 2 | yes | {E.fields(token,params,True{}) == List.append(&2,C.Parameter,E.parameters(params),[C.Parameter{token,0,0}]) :  |
| src/type-erasure-LAWS.bend | generic_arguments | 2 | yes | {E.arguments(token,args,True{}) == List.append(&2,C.Term,args,[C.Value{token,0,0}]) : List<&2,C.Term>} |
| src/type-erasure-LAWS.bend | generic_bindings | 2 | yes | {E.bindings(token,params,True{}) == List.append(&2,C.Binding,params,[C.Binding{token,0,0,0,False{},None{}}]) : |
| src/type-erasure-LAWS.bend | generic_nullary_is_boxed | 3 | yes | {E.construct(token,typ,tag,Nil{},Nil{},True{}) == C.Construct{token,E.type_id(typ),tag,[C.Parameter{token,0,0} |
| src/type-erasure-LAWS.bend | plain_nullary_is_ordinal | 3 | yes | {E.construct(token,typ,tag,Nil{},Nil{},False{}) == C.Value{token,E.type_id(typ),tag} : C.Term} |
| src/type-erasure-LAWS.bend | generic_constructor_uses_memory | 2 | yes | {W.fielded([C.Constructor{token,E.fields(token,params,True{})}]) == True{} : Bool} |
| src/type-erasure-LAWS.bend | generic_branch_uses_memory | 4 | yes | {W.fielded_arms([C.Branch{tag,E.bindings(token,params,True{}),body}]) == True{} : Bool} |
| src/type-erasure-LAWS.bend | marker_retains_live_signature | 2 | yes | {W.live_types(E.fields(token,params,True{})) == W.live_types(E.parameters(params)) : List<&2,U32>} |
| src/type-erasure-LAWS.bend | erased_argument_commutes | 12 | yes | {V.run(1n+fuel,V.Arguments{Con{C.Parameter{token,0,typ},params},Con{head,args},level,caller,callee,body,frames |
| src/type-erasure-LAWS.bend | erased_field_commutes | 12 | yes | {V.run(1n+fuel,V.Fields{type_id,tag,Con{C.Parameter{token,0,typ},params},Con{head,args},env,values,frames},boo |
| src/type-erasure-LAWS.bend | erased_pattern_commutes | 12 | yes | {V.run(1n+fuel,V.Unpack{Con{C.Binding{token,level,0,typ,parameter,known},params},values,env,body,frames},book) |
| src/types-LAWS.bend | meet_associative | 3 | yes | {T.meet(T.meet(a,b),c) == T.meet(a,T.meet(b,c)) : T.Q} |
| src/types-LAWS.bend | meet_commutative | 2 | yes | {T.meet(a,b) == T.meet(b,a) : T.Q} |
| src/types-LAWS.bend | meet_idempotent | 1 | yes | {T.meet(a,a) == a : T.Q} |
| src/types-LAWS.bend | substitution_choice | 4 | yes | {T.subst(Bool.pick(T.Expr,condition,a,b),env) == Bool.pick(T.Expr,condition,T.subst(a,env),T.subst(b,env)) : T |
| src/types-LAWS.bend | lookup_composes | 3 | yes | {T.lookup(T.compose(first,second),index) == T.subst(T.lookup(first,index),second) : T.Expr} |
| src/types-LAWS.bend | substitution_composes | 3 | yes | {T.subst(T.subst(expr,first),second) == T.subst(expr,T.compose(first,second)) : T.Expr} |
| src/types-LAWS.bend | substitution_identity | 1 | yes | {T.subst(expr,Nil{}) == expr : T.Expr} |
| src/types-LAWS.bend | literal_meet_normalizes | 2 | yes | {T.normalize(T.Meet{T.Quantity{a},T.Quantity{b}}) == T.Quantity{T.meet(a,b)} : T.Expr} |
| src/types-LAWS.bend | meet_zero_left | 1 | yes | {T.reduce(T.Quantity{T.QZero{}},expr) == T.Quantity{T.QZero{}} : T.Expr} |
| src/types-LAWS.bend | meet_zero_right | 1 | yes | {T.reduce(expr,T.Quantity{T.QZero{}}) == T.Quantity{T.QZero{}} : T.Expr} |
| src/types-LAWS.bend | meet_many_left | 1 | yes | {T.reduce(T.Quantity{T.QMany{}},expr) == expr : T.Expr} |
| src/types-LAWS.bend | meet_many_right | 1 | yes | {T.reduce(expr,T.Quantity{T.QMany{}}) == expr : T.Expr} |

Recorded obligations and limits:

(none recorded)

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
