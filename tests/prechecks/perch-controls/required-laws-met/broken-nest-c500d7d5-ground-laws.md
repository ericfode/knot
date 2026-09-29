<!-- prechecks packet v1; rule=required-laws-met; increment=nest; head=c500d7d5f2b6; base=cc9f2fd23d59; builder=scripts/prechecks/packets@47dbd98ca1c7; sources: src/LAWS.bend@c500d7d5 sha256=6fdeb67295a0844f9f641db951a7f4997b1eaf2c5a234fc45897df1e2e2e978c; src/catalog-LAWS.bend@c500d7d5 sha256=b29691c14ea3927fa3390c715f9616c89c75b43973ae550192ae351915d98bf3; src/lowering-LAWS.bend@c500d7d5 sha256=21faaa4cc6d9854e650251e6360e98b17f04a399d948d7c17b25bf25cb0a03d2; src/matrix-LAWS.bend@c500d7d5 sha256=aef5cc3d9e48ee784a415cc9b905cfe477d1c87546dc657a00af54633d0477cb -->
# Claim
Required laws (verbatim from the increment manifest):

- lowering a matrix whose first row is irrefutable selects that row
- specialization preserves first-match on the rows it keeps
- an exhaustive matrix lowers to a tree with no missing branch

# Evidence
Operation-to-law matrix computed from the sources:

| file | law | for-binders | PROOF filled | statement |
|---|---|---|---|---|
| src/LAWS.bend | empty_source | 1 | yes | {L.tokenize(fuel,"") == Done{[S.Token{"<eof>",S.At{0,0,1,0}}]} : Result<S.Error,List<&2,S.Token>>} |
| src/LAWS.bend | word_source | 1 | yes | {L.tokenize(1n+extra,"a") == Done{[S.Token{"a",S.At{0,1,1,0}},S.Token{"<eof>",S.At{1,1,1,1}}]} : Result<S.Erro |
| src/LAWS.bend | name_words_witness | 0 | yes | {[S.words("a.b_1.c",True{},0),S.words("x.",True{},0),S.words("a..b",True{},0),S.words("a.1",True{},0)] == [3,0 |
| src/LAWS.bend | malformed_word_source | 1 | yes | {L.tokenize(2n+extra,"a.") == Fail{S.Invalid{"lex","name",S.At{0,2,1,0}}} : Result<S.Error,List<&2,S.Token>>} |
| src/LAWS.bend | no_character_budget | 2 | yes | {L.tokenize(0n,SCon{c,tail}) == Fail{S.Exhausted{"lex",S.At{0,0,1,0}}} : Result<S.Error,List<&2,S.Token>>} |
| src/LAWS.bend | no_parser_budget | 1 | yes | {P.parse(0n,tokens) == Fail{S.Exhausted{"parse",S.here(tokens)}} : Result<S.Error,P.Parsed>} # Prefix classifi |
| src/LAWS.bend | generic_header | 2 | yes | {P.run(1n,P.Header{S.Token{"type",at},S.Token{"Box",at}},Con{S.Token{"<",at},rest}) == Fail{S.Unsupported{"par |
| src/LAWS.bend | multiple_scrutinees | 1 | yes | {P.run(4n,P.MatchTail{S.Token{"match",at},S.Variable{S.Token{"a",at}},0}, [S.Token{"b",at},S.Token{":",at},S.T |
| src/LAWS.bend | comma_scrutinees | 1 | yes | {P.run(4n,P.MatchTail{S.Token{"match",at},S.Variable{S.Token{"a",at}},0}, [S.Token{",",at},S.Token{"b",at},S.T |
| src/LAWS.bend | header_joins_lines | 2 | yes | {P.header(Con{S.Token{"\n",at},Con{S.Token{"a",at},Con{S.Token{"\n",at},Con{S.Token{":",at},rest}}}}) == Con{S |
| src/LAWS.bend | line_broken_scrutinees_witness | 0 | yes | {P.run(8n,P.BodyAt{2},[indented("match"),indented("\n"),indented("a"),indented("\n"),indented("b"),indented(": |
| src/LAWS.bend | dotted_pattern_binder | 2 | yes | {P.run(1n,P.Term{True{}},Con{S.Token{"a.b",at},Con{S.Token{":",at},rest}}) == Fail{S.Invalid{"parse","pattern- |
| src/LAWS.bend | dotted_let_binder | 2 | yes | {P.run(1n,P.BindingStart{1,2},Con{S.Token{"a.b",at},Con{S.Token{"=",at},rest}}) == Fail{S.Invalid{"parse","bin |
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
| src/matrix-LAWS.bend | irrefutable_first_row_witness | 0 | yes | {M.expand(64n,S.Matrix{token("match"),[S.Variable{token("x")},S.Variable{token("y")}], [row(wild(),wild(),"On" |
| src/matrix-LAWS.bend | exhaustive_matrix_witness | 0 | yes | {lower([row(ctor("Off"),ctor("Off"),"Off"),row(ctor("Off"),ctor("On"),"On"), row(ctor("On"),ctor("Off"),"On"), |
| src/matrix-LAWS.bend | erased_alias_stays_erased | 3 | yes | {M.alias(E.Scope{[C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]},alias,1,2,[flag()]) == Done{E.Scope{[C |
| src/matrix-LAWS.bend | alias_preserves_descent_and_identity | 2 | yes | {M.alias(E.Scope{[C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]},alias,1,1,[flag()]) == Done{E.Scope{[ |
| src/matrix-LAWS.bend | remainder_omits_split | 4 | yes | {M.remaining(Con{head,tail},ctor) == M.remaining(tail,ctor) : List<&2,S.Token>} |
| src/matrix-LAWS.bend | remainder_keeps_other | 4 | yes | {M.remaining(Con{head,tail},ctor) == Con{head,M.remaining(tail,ctor)} : List<&2,S.Token>} |
| src/matrix-LAWS.bend | remainder_drops_split_rows | 8 | yes | {M.without(Con{S.Arm{arm,S.Sequence{Con{S.Constructor{token,args},rest}},body},rows},ctor) == M.without(rows,c |
| src/matrix-LAWS.bend | irrefutable_remainder | 6 | yes | {M.without(Con{S.Arm{arm,S.Sequence{Con{S.Variable{name},rest}},body},rows},ctor) == Con{S.Arm{arm,S.Sequence{ |
| src/matrix-LAWS.bend | anonymous_reference_is_free | 2 | yes | {E.lookup(scope,S.Token{"_",at}) == Fail{S.Invalid{"check","free-name",at}} : Result<S.Error,C.Binding>} |
| src/matrix-LAWS.bend | default_reference_stays_live | 5 | yes | {E.occurrence(Some{C.Reference{name,level,type_id}},name,level,q,type_id,live) == E.unknown(name,level,q,type_ |
| src/matrix-LAWS.bend | empty_reference_stays_live | 5 | yes | {E.occurrence(Some{C.Case{name,level,type_id,Nil{}}},name,level,q,type_id,live) == E.unknown(name,level,q,type |
| src/matrix-LAWS.bend | pending_binder_witnesses_nothing | 10 | yes | {E.witnessed(Con{C.Binding{token,level,q,type_id,param,known},tail},types,pending) == E.witnessed(tail,types,p |
| src/matrix-LAWS.bend | erased_empty_is_not_dead | 1 | yes | {E.dead(E.Scope{[C.Binding{name,0,0,0,True{},Some{C.Case{name,0,0,Nil{}}}}],2,[0,1],True{},Nil{}},[flag()],1)  |
| src/matrix-LAWS.bend | live_empty_is_dead | 1 | yes | {E.dead(E.Scope{[C.Binding{name,0,1,0,True{},Some{C.Case{name,0,0,Nil{}}}}],2,[0,1],True{},Nil{}},[flag()],1)  |
| src/matrix-LAWS.bend | introduced_empty_witness | 0 | yes | {E.dead(E.parameters([C.Parameter{token("x"),1,1},C.Parameter{token("y"),1,0}],0,Nil{}),[flag(),void()],1) ==  |
| src/matrix-LAWS.bend | pending_empty_witness | 0 | yes | {E.dead(E.parameters([C.Parameter{token("y"),1,0},C.Parameter{token("x"),1,1}],0,Nil{}),[flag(),void()],0) ==  |
| src/matrix-LAWS.bend | let_alias_available | 2 | yes | {M.variable_column(C.Binding{name,0,1,0,False{},None{}}, E.Scope{[C.Binding{name,0,1,0,False{},None{}}],1,Nil{ |
| src/matrix-LAWS.bend | terminal_expansion_preserves_budget | 4 | yes | {M.expand(1n,S.Variable{name},types,scope,work) == Done{M.Expansion{S.Variable{name},work}} : Result<S.Error,M |
| src/matrix-LAWS.bend | leaf_expansion_spends_one | 5 | yes | {M.expand(2n,S.Matrix{token,Nil{},[S.Arm{arm,S.Sequence{Nil{}},S.Variable{name}}],1},types,scope,1) == Done{M. |
| src/matrix-LAWS.bend | reference_is_not_rebuilt | 6 | yes | {E.rebuilt(Con{C.Reference{token,level,type_id},tail},bindings,smaller) == False{} : Bool} # len's third row a |
| src/matrix-LAWS.bend | rebuilt_descendant_witness | 0 | yes | {E.rebuilt([rebuilt_l()],descent(),[3,4,1,2]) == True{} : Bool} |
| src/matrix-LAWS.bend | rebuilt_root_witness | 0 | yes | {E.rebuilt([node([rebuilt_l(),C.Value{token("Off"),0,0}])],descent(),[3,4,1,2]) == False{} : Bool} |
| src/matrix-LAWS.bend | changed_field_witness | 0 | yes | {E.rebuilt([node([ref(3,1),C.Value{token("Off"),0,0}])],descent(),[3,4,1,2]) == False{} : Bool} |
| src/matrix-LAWS.bend | retyped_constant_witness | 0 | yes | {E.rebuilt([C.Value{token("Leaf"),1,0}],descent(),[3,4,1,2]) == False{} : Bool} |
| src/matrix-LAWS.bend | rebuilt_descendant_call_witness | 2 | yes | {K.call_result(C.Checked{C.Sequence{[rebuilt_l()]},0,uses},token,0,0,0,E.Scope{descent(),5,Nil{},True{},[3,4,1 |

Recorded obligations and limits:

(none recorded)

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
