<!-- prechecks packet v1; rule=clause-vs-delta; increment=generics; head=78c4942e642a; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/LAWS.bend@78c4942e sha256=10f1684116f8035597113700ec874f5c0ab3ddea109689e074dc265c3a960902; src/PROOF.bend@78c4942e sha256=b53ae9d0324369ecf7975d90da44f82c1987d186a64b535d4c964820923825df; src/generics.bend@78c4942e sha256=07cc22dbc54b4cef6ebb1e09811f6b7dffa15def868e34fca8e992aa031b1211; tests/compiler-classification/check.py@78c4942e sha256=97fb6ff46842a0dc36fc2cfd797e7702dd8fd49002c272258fba1adc0d552613; tests/compiler-generics/README.md@78c4942e sha256=999b7380af0124c9f490763d0f76eeed8add81585d171b13ea67d5135032946f -->
# Claim
Invariance clause (tests/compiler-generics/README.md):

> Main's classify-2 pins for `Name<...>` in parameter, return and binding types conflict with the same capability, and two of its laws fail on the generic parser. They are unchanged here; see [Review round 1](#review-round-1) for the proposed supersession.

# Evidence
Evidence: the governed diff hunks (base to head).
```
diff --git a/src/LAWS.bend b/src/LAWS.bend
index da862b42..335257ff 100644
--- a/src/LAWS.bend
+++ b/src/LAWS.bend
@@ -22,10 +22,14 @@ law no_parser_budget:
   {P.parse(0n,tokens) == Fail{S.Exhausted{"parse",S.here(tokens)}} : Result<S.Error,P.Parsed>}
 
-# Prefix classification does not validate the unconsumed suffix.
+# Parser-only header acceptance; the catalog separately requires constructors.
 law generic_header:
   for +at: S.At
-  for +rest: List<&2,S.Token>
-  {P.run(1n,P.Header{S.Token{"type",at},S.Token{"Box",at}},Con{S.Token{"<",at},rest})
-    == Fail{S.Unsupported{"parse","generic-datatype",at}} : Result<S.Error,P.Parsed>}
+  {P.run(32n,P.Header{S.Token{"type",at},S.Token{"Box",at}},
+      [S.Token{"<",at},S.Token{"-",at},S.Token{"A",at},S.Token{":",at},S.Token{"Type",at},
+       S.Token{">",at},S.Token{"is",at},S.Token{"Type",at},S.Token{":",at},S.Token{"<eof>",at}])
+    == Done{P.Parsed{S.Generic{S.Token{"Box",at},
+      [S.TypedParameter{S.Token{"A",at},0,S.TypeKind{S.Token{"Type",at},S.Quantity{S.Token{"Type",at},1}}}],
+      S.TypeKind{S.Token{"Type",at},S.Quantity{S.Token{"Type",at},1}},Nil{}},[S.Token{"<eof>",at}]}}
+    : Result<S.Error,P.Parsed>}
 
 law multiple_scrutinees:

@@ -76,16 +80,15 @@ law parameter_type_application:
     == Fail{S.Unsupported{"parse","parameter-type",at}} : Result<S.Error,P.Parsed>}
 
+# A result type application is no longer a classified prefix; it enters the
+# typed-result grammar, which parses the whole type expression.
 law return_type_application:
+  for +n: Nat
   for +at: S.At
   for +rest: List<&2,S.Token>
-  {P.run(1n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
+  {P.run(1n+n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
     Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
-    == Fail{S.Unsupported{"parse","type-application",at}} : Result<S.Error,P.Parsed>}
-
-law binding_type_application:
-  for +at: S.At
-  for +rest: List<&2,S.Token>
-  {P.run(1n,P.AnnotatedBinding{S.Token{"xs",at},1,2},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}})
-    == Fail{S.Unsupported{"parse","type-application",at}} : Result<S.Error,P.Parsed>}
+    == P.run(n,P.TypedResult{S.Token{"main",at},S.Sequence{Nil{}}},
+    Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
+    : Result<S.Error,P.Parsed>}
 
 law local_import:

@@ -49,8 +49,5 @@ def L.parameter_type_application(at,rest):
   {==}
 
-def L.return_type_application(at,rest):
-  {==}
-
-def L.binding_type_application(at,rest):
+def L.return_type_application(n,at,rest):
   {==}
 

`src/generics.bend:325-331` (added)
  325  def rebuilt(value: Checked, token: S.Token, +typ: T.Expr, tag: U32, params: List<&2,C.Parameter>) -> Result<S.Error,Checked>:
  326    match value:
  327      case Checked{C.Sequence{args},ignored,uses}: Done{Checked{C.Construct{token,R.type_id(typ),tag,params,args},typ,uses}}
  328      case _: C.internal(Checked,"generic-rebuild-result")
  329  
  330  # Types are checked in their own environment; only their erased projection
  331  # crosses into the runtime IR. All recursive checker work spends depth.

`src/generics.bend:332-396` (added)
  332  def run(fuel: Nat, mode: Mode, +catalog: G.Catalog, +current: U32, +env: Environment) -> Result<S.Error,Checked>:
  333    match fuel mode catalog env:
  334      case 0n _ _ _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
  335      case 1n+ +n Expression{S.Variable{+token},+wanted} G.Catalog{families,sigs} _:
  336        S.bind(Binding,Checked,E.term_name(Binding,G.Named,lookup(env,token),token,name => G.family_named(families,name,0)),binding =>
  337          S.bind(Checked,Checked,occurrence(binding,token,env,term => typ => run(n,Rebuild{term,typ},catalog,current,env)),value => expected(token,wanted,value)))
  338      case 1n+ +n Expression{S.Constructor{+token,+args},+wanted} G.Catalog{+families,sigs} _:
  339        S.bind(G.ConstructorRef,Checked,G.constructor_named(families,token,0),+reference =>
  340          constructor_type(wanted,reference,token,+typ => +tag => +params =>
  341            S.choose(Result<S.Error,Checked>,Nat.is_eq(List.length(&2,S.Node,args),List.length(&2,G.Parameter,params)),u =>
  342              constructor_family(reference,families,+family =>
  343                S.bind(Checked,Checked,run(n,Arguments{args,params,Nil{},0,typ,token},catalog,current,env),value => constructor_result(value,token,typ,tag,params,generic(family)))),u => C.invalid(Checked,"constructor-arity",token))))
  344      case 1n+ +n Expression{S.Call{+token,+args},+wanted} G.Catalog{families,sigs} _:
  345        S.bind(G.FunctionRef,Checked,G.function_named(sigs,token,0),reference =>
  346          S.bind(G.FunctionRef,Checked,callable(reference,token,current,env),call =>
  347            call_body(call,token,wanted,current,env,params => result => run(n,Arguments{args,params,Nil{},0,result,token},catalog,current,env))))
  348      case 1n+ +n Expression{S.Binding{token,q,ann,value,body},wanted} _ _:
  349        run(n,Expression{S.TypedBinding{token,q,old_annotation(ann),value,body},wanted},catalog,current,env)
  350      case 1n+ +n Expression{S.TypedBinding{+token,+q,+ann,+value,+body},+wanted} G.Catalog{+families,sigs} _:
  351        S.bind(Maybe<&2,T.Expr>,Checked,annotation(binding_annotation(ann),families,env,n,token),target =>
  352          S.bind(Checked,Checked,run(n,Expression{value,target},catalog,current,live_scope(env,q)),initial =>
  353            let_body(initial,token,q,families,env,bound => run(n,Expression{body,wanted},catalog,current,bound))))
  354      case 1n+ +n Expression{S.Match{+token,+value,+arms},+wanted} G.Catalog{+families,sigs} _:
  355        S.bind(Unit,Checked,constructor_patterns(arms),u =>
  356          S.bind(Binding,Checked,scrutinee(value,env),+binding =>
  357            matched(binding,token,wanted,families,env,family => typ => run(n,Arms{arms,binding,family,typ,Nil{},token},catalog,current,env))))
  358      case 1n+n Expression{S.TypeApply{token,args,q},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
  359      case 1n+n Expression{S.Quantity{token,q},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
  360      case 1n+n Expression{S.TypeKind{token,q},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
  361      case 1n+n Expression{S.QuantType{token},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
  362      case 1n+n Expression{S.Meet{token,left,right},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
  363      case 1n+n Expression{node,wanted} _ _: C.internal(Checked,"generic-expression-node")
  364      case 1n+n Arguments{Nil{},Nil{},substitutions,index,result,token} _ _:
  365        Done{Checked{C.Sequence{Nil{}},G.replace(result,substitutions),Nil{}}}
  366      case 1n+ +n Arguments{Con{+head,+tail},Con{G.Parameter{name,+q,typ},+rest},+substitutions,+index,+result,+token} G.Catalog{+families,sigs} _:
  367        +target = G.replace(typ,substitutions)
  368        S.choose(Result<S.Error,Checked>,Bool.or(G.is_sort(target),G.is_quant(target)),u =>
  369          S.choose(Result<S.Error,Checked>,U32.is_ne(q,0),u => C.unsupported(Checked,"live-type-argument",token),u =>
  370          S.bind(G.Typed,Checked,G.expression(n,head,families,context(env)),value =>
  371            static_argument(value,target,token,actual =>
  372              S.bind(Checked,Checked,run(n,Arguments{tail,rest,Con{T.Binding{index,actual},substitutions},U32.add(index,1),result,token},catalog,current,env),remaining => static_result(remaining,token))))),u =>
  373          S.bind(Checked,Checked,run(n,Expression{head,Some{target}},catalog,current,live_scope(env,q)),checked =>
  374            S.bind(Checked,Checked,run(n,Arguments{tail,rest,substitutions,U32.add(index,1),result,token},catalog,current,env),remaining => prepend_argument(checked,remaining,token))))
  375      case 1n+n Arguments{nodes,params,substitutions,index,result,token} _ _: C.invalid(Checked,"call-arity",token)
  376      case 1n+n Arms{Nil{},binding,family,wanted,seen,token} _ _: complete(family,seen,wanted,token)
  377      case 1n+ +n Arms{Con{S.Arm{+arm,S.Constructor{+name,+nodes},+body},+tail},+binding,+family,+wanted,+seen,+token} G.Catalog{+families,sigs} _:
  378        S.bind(G.ConstructorRef,Checked,G.constructor_named(families,name,0),reference =>
  379          pattern(reference,binding,seen,arm,+tag => params =>
  380            S.bind(Fields,Checked,field_scope(binding,tag,params,nodes,generic(family),families,env),opened =>
  381              arm_body(opened,bound => +fields =>
  382                S.bind(Checked,Checked,run(n,Expression{body,Some{wanted}},catalog,current,bound),checked =>
  383                  S.bind(Checked,Checked,run(n,Arms{tail,binding,family,wanted,Con{tag,seen},token},catalog,current,env),remaining => prepend_arm(checked,remaining,tag,fields,name,generic(family))))))))
  384      case 1n+n Arms{nodes,binding,family,wanted,seen,token} _ _: C.internal(Checked,"generic-arm-node")
  385      case 1n+n Rebuild{C.Value{token,id,tag},typ} _ _: Done{Checked{C.Value{token,id,tag},typ,Nil{}}}
  386      case 1n+ +n Rebuild{C.Reference{+token,level,id},typ} _ Environment{bindings,next,open,live,smaller,root}:
  387        S.bind(Binding,Checked,find_level(bindings,level),binding => occurrence(binding,token,env,term => domain => run(n,Rebuild{term,domain},catalog,current,env)))
  388      case 1n+ +n Rebuild{C.Construct{+token,id,+tag,+params,args},+typ} _ _:
  389        S.bind(Checked,Checked,run(n,RebuildArguments{args,params,token},catalog,current,env),value => rebuilt(value,token,typ,tag,params))
  390      case 1n+n Rebuild{term,typ} _ _: C.internal(Checked,"generic-refinement-node")
  391      case 1n+n RebuildArguments{Nil{},Nil{},token} _ _: Done{Checked{C.Sequence{Nil{}},T.QuantType{},Nil{}}}
  392      case 1n+ +n RebuildArguments{Con{head,+tail},Con{C.Parameter{name,q,typ},+rest},+token} _ _:
  393        S.bind(Checked,Checked,run(n,Rebuild{head,T.Family{typ}},catalog,current,live_scope(env,q)),checked =>
  394          S.bind(Checked,Checked,run(n,RebuildArguments{tail,rest,token},catalog,current,env),remaining => prepend_argument(checked,remaining,token)))
  395      case 1n+n RebuildArguments{terms,params,token} _ _: C.internal(Checked,"generic-refinement-arity")
  396  

@@ -53,9 +53,12 @@ def main():
                 require(reference[stream].replace(str(ROOT), '$ROOT') == expected[stream], reference)
             actual = run(['bun', output, path])
-            classified(actual, case['knot'])
+            expected = expectation(case, 'parse')
+            observed(actual, expected)
             record['fixtures'].append({'file': case['file'], 'reference': reference,
-                                       'expected': case['knot'], 'lanes': {'bun': actual}})
+                                       'expected': expected, 'lanes': {'bun': actual}})
 
         # Each mutant changes an outcome, not syntax, typing, budgets, or tests.
+        # The three type-application mutants were retired with their anchors:
+        # generics parses Name<...> in parameter, return and binding types.
         mutations = [
             ('nonleading-template', 'Bool.and(parameters,starts(t,"~"))', 'False{}',

@@ -65,10 +68,4 @@ def main():
             ('arrow-as-binding', 'Bool.or(starts(tail,"="),starts(tail,">"))',
              'starts(tail,"=")', 'destructure-arrow', 'Unsupported\tparse\tdestructuring-binding'),
-            ('parameter-application-invalid', 'unsupported(rest,"parameter-type")',
-             'invalid(rest,"parameter-type")', 'application-parameter', 'Invalid\tparse\tparameter-type'),
-            ('return-application-invalid', 'unsupported(Con{colon,body},"type-application")',
-             'invalid(Con{colon,body},"type-application")', 'application-return', 'Invalid\tparse\ttype-application'),
-            ('binding-application-invalid', 'unsupported(tail,"type-application")',
-             'invalid(tail,"type-application")', 'application-binding', 'Invalid\tparse\ttype-application'),
         ]
         for name, before, after, witness, wrong in mutations:
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
