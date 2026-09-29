<!-- prechecks packet v1; rule=clause-vs-delta; increment=generics; head=edfad8b95061; base=c0bd08d03942; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/LAWS.bend@edfad8b9 sha256=f625392c2e859e7195f5a48574a0acced51211537dd077886a62606a865a9167; src/generic-catalog.bend@edfad8b9 sha256=4c4339611277b94a57a6c67cb6d5bf1ddd8b88eb99637434a32c81c1e1129ac5; src/type-erasure-PROOF.bend@edfad8b9 sha256=ea1b44ec65b25ba7d38d21aa52ee68e26eed13ec64563ade9357588292d8719d; tests/compiler-classification/README.md@edfad8b9 sha256=7589522cff5bd43614551c76c14b764edcfbe70f861de18dd574c494bd95e649; tests/compiler-classification/check.py@edfad8b9 sha256=623264b405a568820a6e2d8521037a35ce6707212f6f34b267a76a866a41ecdb; tests/compiler-generics/check.py@edfad8b9 sha256=81a570f962bf98f6585349e6b007fa78ab8048f7d68599ed5f68f21f4c80e5e3 -->
# Claim
Invariance clause (tests/compiler-classification/README.md):

> The parameter mutant keeps its original anchor, `unsupported(rest,"parameter-type")`; only its witness moved, as in the frontend gate's `parameter-type-invalid`.

# Evidence
Evidence: the governed diff hunks (base to head).
```
@@ -76,16 +83,40 @@ law parameter_type_application:
     == Fail{S.Unsupported{"parse","parameter-type",at}} : Result<S.Error,P.Parsed>}
 
+# A result type application is no longer a classified prefix; it enters the
+# typed-result grammar, which parses the whole type expression.
 law return_type_application:
+  for +n: Nat
   for +at: S.At
   for +rest: List<&2,S.Token>
-  {P.run(1n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
+  {P.run(1n+n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
+    Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
+    == P.run(n,P.TypedResult{S.Token{"main",at},S.Sequence{Nil{}}},
     Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
-    == Fail{S.Unsupported{"parse","type-application",at}} : Result<S.Error,P.Parsed>}
+    : Result<S.Error,P.Parsed>}
 
-law binding_type_application:
+# After a type argument only `,` and `>` continue the list. Any other token
+# makes the argument a term (`Tag<On{}>`): Unsupported, never Invalid.
+law term_argument:
+  for +n: Nat
+  for +head: S.Node
+  for +token: S.Token
+  for +rest: List<&2,S.Token>
+  for close: {S.matches(token,">") == False{} : Bool}
+  for comma: {S.matches(token,",") == False{} : Bool}
+  {T.run(1n+n,T.ItemTail{head},Con{token,rest})
+    == Fail{S.Unsupported{"parse","term-argument",S.at(token)}} : Result<S.Error,T.Parsed>}
+
+# A marked bare binder is a parameter missing its type, never a quantity:
+# rejected at the separator, where the seed expects `:`.
+law marked_binder:
+  for +fuel: Nat
+  for +q: U32
+  for +name: S.Token
   for +at: S.At
   for +rest: List<&2,S.Token>
-  {P.run(1n,P.AnnotatedBinding{S.Token{"xs",at},1,2},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}})
-    == Fail{S.Unsupported{"parse","type-application",at}} : Result<S.Error,P.Parsed>}
+  for word: {S.identifier(name) == True{} : Bool}
+  for marked: {U32.is_eq(q,1) == False{} : Bool}
+  {T.parameter_parts(fuel,True{},q,Con{name,Con{S.Token{",",at},rest}})
+    == Fail{S.Invalid{"parse","parameter",at}} : Result<S.Error,T.Parsed>}
 
 law local_import:

`src/generic-catalog.bend:6-9` (added)
    6  type Parameter is Data:
    7    Parameter{token: S.Token, quantity: U32, domain: T.Expr}
    8  # A type scope binds type variables over the book's definitions. A type
    9  # position that names a definition computes a type: Unsupported.

`src/type-erasure-PROOF.bend:37-37` (added)
   37  def L.parameter_retains_quantity(token,q,typ): {==}

@@ -53,29 +54,46 @@ def main():
                 require(reference[stream].replace(str(ROOT), '$ROOT') == expected[stream], reference)
             actual = run(['bun', output, path])
-            classified(actual, case['knot'])
+            expected = expectation(case, 'parse')
+            observed(actual, expected)
             record['fixtures'].append({'file': case['file'], 'reference': reference,
-                                       'expected': case['knot'], 'lanes': {'bun': actual}})
+                                       'expected': expected, 'lanes': {'bun': actual}})
 
         # Each mutant changes an outcome, not syntax, typing, budgets, or tests.
+        # A witness is a frozen manifest case. The kill is the mutant's code at
+        # the witness's own span, or at a literal span for an accepted witness.
+        # Generics removed the classify-2 type-application prefixes: the
+        # parameter mutant keeps its anchor through the generics witness
+        # function-parameter, the malformed twins witness the type grammar's
+        # Unsupported fallback, and the accepted applications witness the
+        # routes into that grammar.
         mutations = [
-            ('nonleading-template', 'Bool.and(parameters,starts(t,"~"))', 'False{}',
-             'template-nonleading', 'Unsupported\tparse\ttemplate-binder'),
-            ('equality-as-binding', 'Bool.or(starts(tail,"="),starts(tail,">"))',
-             'starts(tail,">")', 'destructure-equality', 'Unsupported\tparse\tdestructuring-binding'),
-            ('arrow-as-binding', 'Bool.or(starts(tail,"="),starts(tail,">"))',
-             'starts(tail,"=")', 'destructure-arrow', 'Unsupported\tparse\tdestructuring-binding'),
-            ('parameter-application-invalid', 'unsupported(rest,"parameter-type")',
-             'invalid(rest,"parameter-type")', 'application-parameter', 'Invalid\tparse\tparameter-type'),
-            ('return-application-invalid', 'unsupported(Con{colon,body},"type-application")',
-             'invalid(Con{colon,body},"type-application")', 'application-return', 'Invalid\tparse\ttype-application'),
-            ('binding-application-invalid', 'unsupported(tail,"type-application")',
-             'invalid(tail,"type-application")', 'application-binding', 'Invalid\tparse\ttype-application'),
+            ('nonleading-template', 'parse.bend', 'Bool.and(parameters,starts(t,"~"))', 'False{}',
+             ['template-nonleading'], 'Unsupported\tparse\ttemplate-binder'),
+            ('equality-as-binding', 'parse.bend', 'Bool.or(starts(tail,"="),starts(tail,">"))',
+             'starts(tail,">")', ['destructure-equality'], 'Unsupported\tparse\tdestructuring-binding'),
+            ('arrow-as-binding', 'parse.bend', 'Bool.or(starts(tail,"="),starts(tail,">"))',
+             'starts(tail,"=")', ['destructure-arrow'], 'Unsupported\tparse\tdestructuring-binding'),
+            ('parameter-application-invalid', 'parse.bend', 'unsupported(rest,"parameter-type")',
+             'invalid(rest,"parameter-type")', ['function-parameter'], 'Invalid\tparse\tparameter-type'),
+            ('type-expression-invalid', 'type-parse.bend',
+             'Fail{S.Unsupported{"parse","type-expression",S.at(h)}}',
+             'Fail{S.Invalid{"parse","type-expression",S.at(h)}}',
+             ['application-parameter-after-prefix', 'application-return-after-prefix',
+              'application-binding-after-prefix'], 'Invalid\tparse\ttype-expression'),
+            ('return-application-untyped', 'parse.bend',
+             'S.choose(Result<S.Error,Parsed>,typed_result(tokens),u =>',
+             'S.choose(Result<S.Error,Parsed>,False{},u =>',
+             ['application-return'], 'Invalid\tparse\tfunction-result\t46:47:5:11'),
+            ('binding-application-untyped', 'parse.bend',
+             'Bool.and(S.identifier(typ),starts(tail,"="))', 'S.identifier(typ)',
+             ['application-binding'], 'Invalid\tparse\texpected-=\t65:66:6:10'),
         ]
-        for name, before, after, witness, wrong in mutations:
+        manifest = {Path(c['file']).stem: c for c in json.loads(MANIFEST.read_text())['cases']}
+        for name, file, before, after, witnesses, wrong in mutations:
             directory = BUILD / name
             directory.mkdir(exist_ok=True)
             for source in sources:
                 shutil.copyfile(source, directory / source.name)
-            target = directory / 'parse.bend'
+            target = directory / file
             source = target.read_text()
             require(source.count(before) == 1, f'Mutation anchor: {name}')

`tests/compiler-generics/check.py:60-132` (added)
   60  MUTANTS = (
   61      {'name': 'skipped-substitution', 'file': 'generic-catalog.bend',
   62       'old': 'T.normalize(T.subst(value,substitutions))',
   63       'new': 'T.normalize(value)',
   64       'witness': 'box-unbox', 'phase': 'check',
   65       'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\ttype-mismatch\t'}},
   66      {'name': 'erased-argument-live', 'file': 'type-erasure.bend',
   67       'old': 'case G.Parameter{token,q,typ}: C.Parameter{token,q,type_id(typ)}',
   68       'new': 'case G.Parameter{token,+q,typ}: C.Parameter{token,Bool.pick(U32,U32.is_eq(q,0),1,q),type_id(typ)}',
   69       'witness': 'box-unbox', 'phase': 'abi', 'exports': ['unbox'],
   70       'actual': {'exit': 0, 'arities': {'unbox': 2}}},
   71      {'name': 'wrong-quantity-meet', 'file': 'types.bend',
   72       'old': 'case QMany{}: b', 'new': 'case QMany{}: QMany{}',
   73       'witness': 'meet-not-reusable', 'phase': 'check',
   74       'actual': {'exit': 0, 'contains': 'Checked\n'}},
   75      {'name': 'missing-arity-check', 'file': 'generic-catalog.bend',
   76       'old': 'C.invalid(List<&2,S.Node>,"type-arity",token)',
   77       'new': 'Done{List.take(&2,S.Node,nodes,U32.to_nat(arity))}',
   78       'witness': 'type-arity', 'phase': 'check',
   79       'actual': {'exit': 0, 'contains': 'Checked\n'}},
   80      {'name': 'bare-quantity-default', 'file': 'generic-catalog.bend',
   81       'old': 'reference => bare(reference,token,',
   82       'new': 'reference => apply_start(reference,token,Nil{},1,',
   83       'witness': 'bare-family-parameter', 'phase': 'check',
   84       'actual': {'exit': 0, 'contains': 'Checked\n'}},
   85      {'name': 'term-argument-invalid', 'file': 'type-parse.bend',
   86       'old': 'Fail{S.Unsupported{"parse","term-argument",S.at(h)}}',
   87       'new': 'Fail{S.Invalid{"parse","term-argument",S.at(h)}}',
   88       'witness': 'value-argument-parameter', 'phase': 'check',
   89       'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\tterm-argument\t'}},
   90      {'name': 'empty-family-invalid', 'file': 'generic-catalog.bend',
   91       'old': 'C.unsupported(Family,"empty-datatype",token)',
   92       'new': 'C.invalid(Family,"empty-datatype",token)',
   93       'witness': 'empty-generic-absurd', 'phase': 'check',
   94       'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tempty-datatype\t'}},
   95      {'name': 'empty-datatype-invalid', 'file': 'catalog.bend',
   96       'old': 'C.unsupported(C.Datatype,"empty-datatype",name)',
   97       'new': 'C.invalid(C.Datatype,"empty-datatype",name)',
   98       'witness': 'empty-type', 'phase': 'check',
   99       'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tempty-datatype\t'}},
  100      {'name': 'def-reference-free', 'file': 'scope.bend',
  101       'old': 'unbound(B,F,function(token),token,"def-reference",Fail{error})',
  102       'new': 'Fail{error}',
  103       'witness': 'def-reference-live', 'phase': 'check',
  104       'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tfree-name\t'}},
  105      {'name': 'type-level-definition-unknown', 'file': 'generic-catalog.bend',
  106       'old': 'dependent-type",token))\n    case Some{Definition{name}}: C.unsupported(Typed,"type-level-definition",token)',
  107       'new': 'dependent-type",token))\n    case Some{Definition{name}}: next(Unit{})',
  108       'witness': 'definition-field-later', 'phase': 'check',
  109       'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tunknown-type\t'}},
  110      {'name': 'marked-binder-quantity', 'file': 'type-parse.bend',
  111       'old': 'S.choose(Result<S.Error,Parsed>,U32.is_eq(quantity,1),u =>',
  112       'new': 'S.choose(Result<S.Error,Parsed>,True{},u =>',
  113       'witness': 'marked-reusable-binder', 'phase': 'check',
  114       'actual': {'exit': 0, 'contains': 'Checked\n'}},
  115      {'name': 'pattern-order-forward', 'file': 'generic-catalog.bend',
  116       'old': 'S.choose(Result<S.Error,ConstructorRef>,visible(token,declaration(reference)),u =>',
  117       'new': 'S.choose(Result<S.Error,ConstructorRef>,True{},u =>',
  118       'witness': 'later-family-parameter', 'phase': 'check',
  119       'actual': {'exit': 0, 'contains': 'Checked\n'}},
  120      {'name': 'quantity-gap-glued', 'file': 'type-parse.bend',
  121       'old': 'glued(token,value)', 'new': 'True{}',
  122       'witness': 'quantity-gap-argument', 'phase': 'check',
  123       'actual': {'exit': 0, 'contains': 'Checked\n'}},
  124      {'name': 'meet-gap-glued', 'file': 'type-parse.bend',
  125       'old': 'Bool.and(glued(a,b),glued(b,c))', 'new': 'True{}',
  126       'witness': 'meet-gap', 'phase': 'check',
  127       'actual': {'exit': 0, 'contains': 'Checked\n'}},
  128      {'name': 'close-gap-glued', 'file': 'type-parse.bend',
  129       'old': 'u => Bool.not(flush(from,h))', 'new': 'u => False{}',
  130       'witness': 'close-gap-parameter', 'phase': 'check',
  131       'actual': {'exit': 0, 'contains': 'Checked\n'}},
  132  )
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
