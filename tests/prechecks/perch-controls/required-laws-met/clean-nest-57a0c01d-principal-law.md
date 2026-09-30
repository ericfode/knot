<!-- prechecks packet v1; rule=required-laws-met; increment=nest; head=57a0c01df87f; base=d14418b7cb04; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/LAWS.bend@57a0c01d sha256=b7755dbd1da14516ecdb7484edace511e581e4c8671a287f2d23826264502e6d; src/catalog-LAWS.bend@57a0c01d sha256=b29691c14ea3927fa3390c715f9616c89c75b43973ae550192ae351915d98bf3; src/matrix-LAWS.bend@57a0c01d sha256=872942aaf3936e939f50caea516c4305824a737aac7c7791d38e1b6f87bf8d76 -->
# Claim
Required laws (verbatim from the increment manifest):

- identities(M.specialize(rows, ctor, fields, level)) == selected(rows, ctor)

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
| src/LAWS.bend | template_binder | 2 | yes | {P.run(1n,P.Parameters{")"},Con{S.Token{"~",at},Con{S.Token{"x",at},Con{S.Token{":",at},rest}}}) == Fail{S.Uns |
| src/LAWS.bend | destructuring_binding | 3 | yes | {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},rest}) == Fail{S.Unsupported{"parse","de |
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
| src/matrix-LAWS.bend | irrefutable_lowering_selects_first | 0 | yes | {lower([row(S.Variable{token("_")},S.Variable{token("_")},"On"), row(ctor("Off"),ctor("Off"),"Off")]) == Done{ |
| src/matrix-LAWS.bend | exhaustive_matrix_has_no_missing_branch | 0 | yes | {lower([row(ctor("Off"),ctor("Off"),"Off"),row(ctor("Off"),ctor("On"),"On"), row(ctor("On"),ctor("Off"),"On"), |
| src/matrix-LAWS.bend | erased_alias_stays_erased | 3 | yes | {M.alias(E.Scope{[C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]},alias,1,2,[flag()]) == Done{E.Scope{[C |
| src/matrix-LAWS.bend | alias_preserves_descent_and_identity | 2 | yes | {M.alias(E.Scope{[C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]},alias,1,1,[flag()]) == Done{E.Scope{[ |
| src/matrix-LAWS.bend | default_completes_missing_branch | 5 | yes | {M.defaults(Con{C.Constructor{name,fields},ctors},explicit) == Con{name,M.defaults(ctors,explicit)} : List<&2, |
| src/matrix-LAWS.bend | default_does_not_repeat_explicit_branch | 5 | yes | {M.defaults(Con{C.Constructor{name,fields},ctors},explicit) == M.defaults(ctors,explicit) : List<&2,S.Token>} |
| src/matrix-LAWS.bend | default_completion_witness | 0 | yes | {M.signature(flag(),[token("Off")],True{}) == [token("Off"),token("On")] : List<&2,S.Token>} |

Recorded obligations and limits:

(none recorded)

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
