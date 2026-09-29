<!-- prechecks packet v1; rule=required-laws-met; increment=generics; head=edfad8b95061; base=c0bd08d03942; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/LAWS.bend@edfad8b9 sha256=f625392c2e859e7195f5a48574a0acced51211537dd077886a62606a865a9167; src/catalog-LAWS.bend@edfad8b9 sha256=d8312b56bcd24c7331b849c6f36df4076c1d28123ec204cdd09c3823c9b69235; src/check-LAWS.bend@edfad8b9 sha256=267fbccdac610172180cd96894c003373ee65d7bf88c886c32eb711fbdea9c34; src/type-erasure-LAWS.bend@edfad8b9 sha256=c06de11c7885ff22bf64485f554a663ff0b060e7a8f625ca82fcd83f4fd307bf; src/types-LAWS.bend@edfad8b9 sha256=4ca28bccb97831e118050b939e727aab92b0da430c13ba5ed4c6f672bbf286ab -->
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
| src/LAWS.bend | term_argument | 6 | yes | {T.run(1n+n,T.ItemTail{head},Con{token,rest}) == Fail{S.Unsupported{"parse","term-argument",S.at(token)}} : Re |
| src/LAWS.bend | marked_binder | 7 | yes | {T.parameter_parts(fuel,True{},q,Con{name,Con{S.Token{",",at},rest}}) == Fail{S.Invalid{"parse","parameter",at |
| src/LAWS.bend | local_import | 2 | yes | {P.run(1n,P.Header{S.Token{"import",at},S.Token{".",at}},Con{S.Token{"/",at},rest}) == Fail{S.Unsupported{"par |
| src/LAWS.bend | hash_import | 2 | yes | {P.run(1n,P.Header{S.Token{"import",at},S.Token{"0x77a1a37baca5d86f62241cab956a1fb1",at}},Con{S.Token{"/",at}, |
| src/catalog-LAWS.bend | erased_field_has_no_kind_obligation | 2 | yes | {G.field_kind(data,0,child) == True{} : Bool} |
| src/catalog-LAWS.bend | data_live_field_requires_data | 0 | yes | {G.field_kind(True{},1,False{}) == False{} : Bool} |
| src/catalog-LAWS.bend | reusable_field_requires_data | 1 | yes | {G.field_kind(data,2,False{}) == False{} : Bool} |
| src/catalog-LAWS.bend | data_field_preserves_metadata | 5 | yes | {G.field_type(token,2,data,G.TypeRef{index,C.Datatype{name,True{},ctors}}) == Done{C.Parameter{token,2,index}} |
| src/catalog-LAWS.bend | empty_datatype | 2 | yes | {G.nonempty(Nil{},name,data) == Fail{S.Unsupported{"check","empty-datatype",S.at(name)}} : Result<S.Error,C.Da |
| src/catalog-LAWS.bend | field_capability_is_not_acceptance | 4 | yes | {K.enum_constructors(Con{C.Constructor{token,Con{head,tail}},rest}) == Fail{S.Unsupported{"check","constructor |
| src/check-LAWS.bend | empty_sequence_preserves_uses | 2 | yes | {E.sequential(Nil{},uses,token) == Done{uses} : Result<S.Error,List<&2,U32>>} |
| src/check-LAWS.bend | repeated_affine_level | 1 | yes | {E.sequential([0],[0],token) == Fail{S.Invalid{"check","affine-reuse",S.at(token)}} : Result<S.Error,List<&2,U |
| src/check-LAWS.bend | live_erased_occurrence | 3 | yes | {E.occurrence(None{},token,level,0,type_id,True{}) == Fail{S.Invalid{"check","erased-live",S.at(token)}} : Res |
| src/check-LAWS.bend | erased_occurrence_preserves_identity | 3 | yes | {E.occurrence(None{},token,level,0,type_id,False{}) == Done{C.Checked{C.Reference{token,level,type_id},type_id |
| src/check-LAWS.bend | refined_constructor_is_fresh | 3 | yes | {E.occurrence(Some{C.Value{token,type_id,tag}},token,0,1,type_id,True{}) == Done{C.Checked{C.Value{token,type_ |
| src/check-LAWS.bend | nearest_binding_wins | 2 | yes | {E.find(Con{C.Binding{S.Token{"x",S.At{0,1,1,0}},level,1,0,True{},None{}},tail},S.Token{"x",S.At{7,8,2,0}}) == |
| src/check-LAWS.bend | def_reference | 10 | yes | {E.term_name(C.Binding,R,F,Fail{error},token,datatype,function) == Fail{S.Unsupported{"check","def-reference", |
| src/check-LAWS.bend | no_checker_budget | 1 | yes | {K.check(0n,node) == Fail{S.Exhausted{"check",S.At{0,0,0,0}}} : Result<S.Error,C.Book>} |
| src/type-erasure-LAWS.bend | empty_family | 5 | yes | {G.header_kind(G.Typed{T.Sort{q},kind},token,params,Nil{},generic) == Fail{S.Unsupported{"check","empty-dataty |
| src/type-erasure-LAWS.bend | type_level_definition | 6 | yes | {G.resolve(1n+fuel,G.Expression{S.Variable{token}},families,symbols) == Fail{S.Unsupported{"check","type-level |
| src/type-erasure-LAWS.bend | pattern_order | 5 | yes | {G.pattern_constructor(families,token) == Fail{S.Invalid{"check","unknown-constructor",S.at(token)}} : Result< |
| src/type-erasure-LAWS.bend | spaced_quantity | 4 | yes | {P.read_quantity(token,Con{value,rest}) == Fail{S.Unsupported{"parse","spacing",S.at(value)}} : Result<S.Error |
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
