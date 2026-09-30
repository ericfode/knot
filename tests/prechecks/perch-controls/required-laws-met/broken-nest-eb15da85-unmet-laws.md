<!-- prechecks packet v1; rule=required-laws-met; increment=nest; head=eb15da857dc7; base=3c25d9bede00; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/LAWS.bend@eb15da85 sha256=b3238f190ca95a3acaaec8af3232e9a78d326de714f2ec0a4dd350f9a5a573f9; src/catalog-LAWS.bend@eb15da85 sha256=b29691c14ea3927fa3390c715f9616c89c75b43973ae550192ae351915d98bf3; src/matrix-LAWS.bend@eb15da85 sha256=a22183685e186faff5db14691a81639ec176143296afe6f27281132512678f02 -->
# Claim
Required laws (verbatim from the increment manifest):

- General irrefutable-first-row lowering theorem
- General exhaustive-matrix/no-missing-branch lowering theorem

# Evidence
Operation-to-law matrix computed from the sources:

| file | law | for-binders | PROOF filled | statement |
|---|---|---|---|---|
| src/LAWS.bend | empty_source | 1 | yes | {L.tokenize(fuel,"") == Done{[S.Token{"<eof>",S.At{0,0,1,0}}]} : Result<S.Error,List<&2,S.Token>>} |
| src/LAWS.bend | word_source | 1 | yes | {L.tokenize(1n+extra,"a") == Done{[S.Token{"a",S.At{0,1,1,0}},S.Token{"<eof>",S.At{1,1,1,1}}]} : Result<S.Erro |
| src/LAWS.bend | no_character_budget | 2 | yes | {L.tokenize(0n,SCon{c,tail}) == Fail{S.Exhausted{"lex",S.At{0,0,1,0}}} : Result<S.Error,List<&2,S.Token>>} |
| src/LAWS.bend | no_parser_budget | 1 | yes | {P.parse(0n,tokens) == Fail{S.Exhausted{"parse",S.here(tokens)}} : Result<S.Error,P.Parsed>} # Prefix classifi |
| src/LAWS.bend | generic_header | 2 | yes | {P.run(1n,P.Header{S.Token{"type",at},S.Token{"Box",at}},Con{S.Token{"<",at},rest}) == Fail{S.Unsupported{"par |
| src/LAWS.bend | multiple_scrutinees | 1 | yes | {P.run(4n,P.MatchTail{S.Token{"match",at},S.Variable{S.Token{"a",at}},0}, [S.Token{"b",at},S.Token{":",at},S.T |
| src/LAWS.bend | comma_scrutinees | 1 | yes | {P.run(4n,P.MatchTail{S.Token{"match",at},S.Variable{S.Token{"a",at}},0}, [S.Token{",",at},S.Token{"b",at},S.T |
| src/LAWS.bend | template_binder | 2 | yes | {P.run(1n,P.Parameters{")"},Con{S.Token{"~",at},Con{S.Token{"x",at},Con{S.Token{":",at},rest}}}) == Fail{S.Uns |
| src/LAWS.bend | nonleading_template_binder | 3 | yes | {P.run(1n,P.ListTail{")",head,True{},False{}},Con{S.Token{",",at},Con{S.Token{"~",at},rest}}) == Fail{S.Invali |
| src/LAWS.bend | destructuring_binding | 4 | yes | {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},rest}) == Fail{S.Unsupported{"parse","de |
| src/LAWS.bend | equality_is_not_binding | 3 | yes | {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},Con{S.Token{"=",at},rest}}) == Fail{S.In |
| src/LAWS.bend | arrow_is_not_binding | 3 | yes | {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},Con{S.Token{">",at},rest}}) == Fail{S.In |
| src/LAWS.bend | parameter_type_application | 2 | yes | {P.parameter(Con{S.Token{"xs",at},Con{S.Token{":",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}}) ==  |
| src/LAWS.bend | return_type_application | 2 | yes | {P.run(1n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}}, Con{S.Token{"-",at},Con{S.Token{">",at},Con{S. |
| src/LAWS.bend | binding_type_application | 2 | yes | {P.run(1n,P.AnnotatedBinding{S.Token{"xs",at},1,2},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}) == Fail{ |
| src/LAWS.bend | local_import | 2 | yes | {P.run(1n,P.Header{S.Token{"import",at},S.Token{".",at}},Con{S.Token{"/",at},rest}) == Fail{S.Unsupported{"par |
| src/LAWS.bend | hash_import | 2 | yes | {P.run(1n,P.Header{S.Token{"import",at},S.Token{"0x77a1a37baca5d86f62241cab956a1fb1",at}},Con{S.Token{"/",at}, |
| src/catalog-LAWS.bend | erased_field_has_no_kind_obligation | 2 | yes | {G.field_kind(data,0,child) == True{} : Bool} |
| src/catalog-LAWS.bend | data_live_field_requires_data | 0 | yes | {G.field_kind(True{},1,False{}) == False{} : Bool} |
| src/catalog-LAWS.bend | reusable_field_requires_data | 1 | yes | {G.field_kind(data,2,False{}) == False{} : Bool} |
| src/catalog-LAWS.bend | data_field_preserves_metadata | 5 | yes | {G.field_type(token,2,data,G.TypeRef{index,C.Datatype{name,True{},ctors}}) == Done{C.Parameter{token,2,index}} |
| src/catalog-LAWS.bend | field_capability_is_not_acceptance | 4 | yes | {K.enum_constructors(Con{C.Constructor{token,Con{head,tail}},rest}) == Fail{S.Unsupported{"check","constructor |
| src/catalog-LAWS.bend | empty_datatype | 2 | yes | {G.datatype(Nil{},name,data) == Done{C.Datatype{name,data,Nil{}}} : Result<S.Error,C.Datatype>} |
| src/matrix-LAWS.bend | selection_congruence | 7 | yes | {identities(S.choose(List<&2,S.Node>,keep,u => Con{S.Arm{arm,pattern,body},tail},u => tail)) == S.choose(List< |
| src/matrix-LAWS.bend | specialization_preserves_first_match | 4 | yes | {identities(M.specialize(rows,ctor,fields,level)) == selected(rows,ctor) : List<&2,S.Token>} # Irrefutable hea |
| src/matrix-LAWS.bend | irrefutable_specialization | 8 | yes | {M.specialize(Con{S.Arm{arm,S.Sequence{Con{S.Variable{name},rest}},body},rows},ctor,fields,level) == Con{S.Arm |
| src/matrix-LAWS.bend | irrefutable_default | 6 | yes | {M.default_rows(Con{S.Arm{arm,S.Sequence{Con{S.Variable{name},rest}},body},rows},level) == Con{S.Arm{arm,S.Seq |
| src/matrix-LAWS.bend | first_row_selected | 6 | yes | {M.step(token,Nil{},Con{S.Arm{arm,S.Sequence{Nil{}},body},rows},1,types,scope) == Done{body} : Result<S.Error, |
| src/matrix-LAWS.bend | lowering_work_exhaustion | 5 | yes | {M.step(token,columns,rows,0,types,scope) == Fail{S.Exhausted{"check",S.at(token)}} : Result<S.Error,S.Node>}  |
| src/matrix-LAWS.bend | irrefutable_lowering_witness | 0 | yes | {lower([row(S.Variable{token("_")},S.Variable{token("_")},"On"), row(ctor("Off"),ctor("Off"),"Off")]) == Done{ |
| src/matrix-LAWS.bend | exhaustive_matrix_witness | 0 | yes | {lower([row(ctor("Off"),ctor("Off"),"Off"),row(ctor("Off"),ctor("On"),"On"), row(ctor("On"),ctor("Off"),"On"), |
| src/matrix-LAWS.bend | erased_alias_stays_erased | 3 | yes | {M.alias(E.Scope{[C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]},alias,1,2,[flag()]) == Done{E.Scope{[C |
| src/matrix-LAWS.bend | alias_preserves_descent_and_identity | 2 | yes | {M.alias(E.Scope{[C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]},alias,1,1,[flag()]) == Done{E.Scope{[ |
| src/matrix-LAWS.bend | default_completes_missing_branch | 5 | yes | {M.defaults(Con{C.Constructor{name,fields},ctors},explicit) == Con{name,M.defaults(ctors,explicit)} : List<&2, |
| src/matrix-LAWS.bend | default_does_not_repeat_explicit_branch | 5 | yes | {M.defaults(Con{C.Constructor{name,fields},ctors},explicit) == M.defaults(ctors,explicit) : List<&2,S.Token>} |
| src/matrix-LAWS.bend | default_completion_witness | 0 | yes | {M.signature(flag(),[token("Off")],True{}) == [token("Off"),token("On")] : List<&2,S.Token>} |
| src/matrix-LAWS.bend | anonymous_reference_is_free | 2 | yes | {E.lookup(scope,S.Token{"_",at}) == Fail{S.Invalid{"check","free-name",at}} : Result<S.Error,C.Binding>} |
| src/matrix-LAWS.bend | default_reference_stays_live | 5 | yes | {E.occurrence(Some{C.Reference{name,level,type_id}},name,level,q,type_id,live) == E.unknown(name,level,q,type_ |
| src/matrix-LAWS.bend | empty_reference_stays_live | 5 | yes | {E.occurrence(Some{C.Case{name,level,type_id,Nil{}}},name,level,q,type_id,live) == E.unknown(name,level,q,type |
| src/matrix-LAWS.bend | erased_empty_is_not_dead | 1 | yes | {E.dead(E.Scope{[C.Binding{name,0,0,0,True{},Some{C.Case{name,0,0,Nil{}}}}],1,[0],True{},Nil{}}) == False{} :  |
| src/matrix-LAWS.bend | live_empty_is_dead | 1 | yes | {E.dead(E.Scope{[C.Binding{name,0,1,0,True{},Some{C.Case{name,0,0,Nil{}}}}],1,[0],True{},Nil{}}) == True{} : B |
| src/matrix-LAWS.bend | let_alias_available | 2 | yes | {M.variable_column(C.Binding{name,0,1,0,False{},None{}}, E.Scope{[C.Binding{name,0,1,0,False{},None{}}],1,Nil{ |
| src/matrix-LAWS.bend | terminal_expansion_preserves_budget | 4 | yes | {M.expand(1n,S.Variable{name},types,scope,work) == Done{M.Expansion{S.Variable{name},work}} : Result<S.Error,M |
| src/matrix-LAWS.bend | leaf_expansion_spends_one | 5 | yes | {M.expand(2n,S.Matrix{token,Nil{},[S.Arm{arm,S.Sequence{Nil{}},S.Variable{name}}],1},types,scope,1) == Done{M. |

Recorded obligations and limits:

(none recorded)

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
