<!-- prechecks packet v1; rule=required-laws-met; increment=closures; head=a1d68911d5fa; base=fa31fec064ba; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/closure-LAWS.bend@a1d68911 sha256=e42d0b0f77801fbf9b01cda68d1b6dafeddc00473b5ae215ff7bb967c5f4facf; src/closure-check-LAWS.bend@a1d68911 sha256=0ad2e499a3c09883a6a9f3bf1528a35298c59b668da946c68fd69cfce2bff3df; src/closure-types-LAWS.bend@a1d68911 sha256=b28a454e06ea535e79e5362317812db3fc9a7e506235e5b8863ed7e70ab93815 -->
# Claim
Required laws (verbatim from the increment manifest):

- Checked laws state capture, type identity, lowering and evaluator-step equations.

# Evidence
Operation-to-law matrix computed from the sources:

| file | law | for-binders | PROOF filled | statement |
|---|---|---|---|---|
| src/closure-LAWS.bend | capture_arity | 2 | yes | {List.length(&2,C.Term,F.capture_args(captures,rename)) == List.length(&2,C.Binding,captures) : Nat} |
| src/closure-LAWS.bend | capture_quantity | 7 | yes | {F.capture_params(Con{C.Binding{token,level,quantity,typ,parameter,known},tail}) == Con{C.Parameter{token,quan |
| src/closure-LAWS.bend | close_has_one_cell | 5 | yes | {F.pack(token,tag,typ,captures,rename) == C.Construct{token,typ,tag,F.capture_params(captures),F.capture_args( |
| src/closure-LAWS.bend | invoke_has_one_dispatch | 5 | yes | {F.apply(token,index,result,function,argument) == C.Application{token,index,result,[function,argument]} : C.Te |
| src/closure-LAWS.bend | outer_levels_are_unchanged | 1 | yes | {F.level(F.Same{},id) == id : U32} |
| src/closure-LAWS.bend | rewrite_exhaustion | 3 | yes | {F.rewrite(0n,term,rename,table) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,C.Term>} |
| src/closure-check-LAWS.bend | discard_is_not_a_reference | 6 | yes | {E.lookup(E.Scope{bindings,level,open,live,smaller},S.Token{"_",at}) == Fail{S.Invalid{"check","free-name",at} |
| src/closure-check-LAWS.bend | closure_application_is_a_computed_scrutinee | 4 | yes | {E.scrutinee(S.Apply{token,function,args},scope) == Fail{S.Invalid{"check","computed-scrutinee",S.at(token)}}  |
| src/closure-check-LAWS.bend | lambda_is_a_computed_scrutinee | 4 | yes | {E.scrutinee(S.Lambda{token,quantity,body},scope) == Fail{S.Invalid{"check","computed-scrutinee",S.at(token)}} |
| src/closure-check-LAWS.bend | affine_capture_is_transferred | 5 | yes | {H.close(C.Checked{C.Reference{token,3,domain},domain,[3]},token,site,typ,9,1,domain, [C.Binding{token,3,1,dom |
| src/closure-check-LAWS.bend | affine_capture_cannot_be_consumed_twice | 6 | yes | {H.invoke(C.Checked{function,arrow,[3]},C.Checked{argument,domain,[3]},token,result) == Fail{S.Invalid{"check" |
| src/closure-check-LAWS.bend | erased_argument_has_no_live_read | 3 | yes | {H.scan(3n,H.Arguments{[C.Reference{token,3,typ}],[C.Parameter{token,0,typ}],True{}},sigs) == Done{H.Reads{[3] |
| src/closure-check-LAWS.bend | erased_read_has_no_live_capture | 5 | yes | {H.captures([C.Binding{token,3,q,typ,parameter,known}],H.Reads{[3],Nil{}}) == [C.Binding{token,3,0,typ,False{} |
| src/closure-check-LAWS.bend | close_starts_with_an_empty_environment | 11 | yes | {V.step(V.Evaluate{C.Closure{token,site,typ,level,q,domain,captures,body},caller,frames},book) == Done{V.Captu |
| src/closure-check-LAWS.bend | erased_capture_skips_lookup | 14 | yes | {V.step(V.Capture{site,typ,level,Con{C.Binding{token,id,0,domain,parameter,known},tail},body,caller,env,frames |
| src/closure-check-LAWS.bend | apply_evaluates_the_function_first | 8 | yes | {V.step(V.Evaluate{C.Invoke{token,arrow,typ,function,argument},caller,frames},book) == Done{V.Evaluate{functio |
| src/closure-check-LAWS.bend | apply_closure_retains_its_environment | 8 | yes | {V.apply_argument(V.Closure{site,typ,level,body,env},argument,caller,frames) == Done{V.Evaluate{argument,calle |
| src/closure-check-LAWS.bend | apply_enters_the_body_without_a_return_frame | 6 | yes | {V.step(V.Return{value,Con{V.ApplyBody{level,body,env},frames}},book) == Done{V.Evaluate{body,Con{V.Entry{leve |
| src/closure-types-LAWS.bend | arrow_location | 2 | yes | {S.at(S.Arrow{domain,result}) == S.at(domain) : S.At} |
| src/closure-types-LAWS.bend | arrow_kind | 3 | yes | {F.reusable(C.Arrow{token,domain,result}) == False{} : Bool} |
| src/closure-types-LAWS.bend | signature_end | 1 | yes | {F.signature(Nil{},result) == result : S.Token} |
| src/closure-types-LAWS.bend | signature_step | 5 | yes | {F.signature(Con{S.Parameter{name,quantity,domain},tail},result) == S.Arrow{domain,F.signature(tail,result)} : |
| src/closure-types-LAWS.bend | interned_arrow_is_stable | 5 | yes | {F.append(Some{index},types,name,domain,result) == Done{F.Interned{types,index}} : Result<S.Error,F.Interned>} |
| src/closure-types-LAWS.bend | no_type_budget | 3 | yes | {F.read(0n,mode,tokens,code) == Fail{S.Exhausted{"parse",S.here(tokens)}} : Result<S.Error,F.Read>} |

Recorded obligations and limits:

(none recorded)

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
