<!-- prechecks packet v1; rule=clause-vs-delta; increment=closures; head=a1d68911d5fa; base=fa31fec064ba; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/SPEC.md@a1d68911 sha256=0f71a64265446cfed950ee9a5d04ec1d1e6431a6cb0f79f746fe2761f584be49; src/catalog.bend@a1d68911 sha256=63ae5138855d8fe70dd05f2bb83d80afe0ed11b7a42112ff53be9076c8e8e55f; src/check.bend@a1d68911 sha256=e74f6449394f7b2f919a01759177c30b32c68d257960a2d6814889b0b24868cb; src/closure-LAWS.bend@a1d68911 sha256=e42d0b0f77801fbf9b01cda68d1b6dafeddc00473b5ae215ff7bb967c5f4facf; src/closure.bend@a1d68911 sha256=95d7e5478f08ae801725be5d0ca2b8fb9d41af4e92cd8368445aeed4c2efa56a; src/eval.bend@a1d68911 sha256=ff2c67c7b8f93ed31cd4f779931a2c0112d01f75dec9b848f53ca79443596bde; src/wasm.bend@a1d68911 sha256=9110e98faa4c26edf0273c9d08c41f8d8b967fb260d4d317b87e4aac247fff10 -->
# Claim
Invariance clause (src/SPEC.md):

> All original function indices and exports are retained. Closure dispatchers and the allocator are appended and unexported. **Host precondition:** invoke only functions whose live parameters and result have enum-only datatypes, supplying each parameter's valid constructor ordinal.

# Evidence
Evidence: the governed diff hunks (base to head).
```
@@ -207,4 +212,5 @@ def definition_fields(definition: C.Datatype, tag: U32) -> Result<S.Error,List<&
   match definition:
     case C.Datatype{token,data,ctors}: fields_at(ctors,tag)
+    case C.Arrow{token,domain,result}: C.internal(List<&2,C.Parameter>,"function-constructor")
 
 def field_signature(reference: ConstructorRef, types: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Parameter>>:

@@ -172,18 +176,78 @@ def rebuilt(value: C.Checked, token: S.Token, +type_id: U32, tag: U32, params: L
     case _: C.internal(C.Checked,"refined-arguments")
 
+def split_call(parts: H.Prefix, next: List<&2,C.Parameter> -> List<&2,S.Node> -> List<&2,C.Parameter> -> List<&2,S.Node> -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
+  match parts:
+    case H.Prefix{params,args,missing,rest}: next(params,args,missing,rest)
+
+def missing(params: List<&2,C.Parameter>) -> Bool:
+  match params:
+    case Nil{}: False{}
+    case Con{head,tail}: True{}
+
+def apply_type(definition: C.Datatype, next: U32 -> U32 -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
+  match definition:
+    case C.Arrow{token,domain,result}: next(domain,result)
+    case _: C.internal(C.Checked,"application-type")
+
+def function_type(value: C.Checked) -> U32:
+  match value:
+    case C.Checked{term,typ,uses}: typ
+
+def lambda_body(definition: C.Datatype, wanted: Maybe<&2,U32>, scope: E.Scope, +token: S.Token, +q: U32,
+  +current: U32, +types: List<&2,C.Datatype>, +sigs: List<&2,C.Signature>, +fuel: Nat,
+  next: E.Scope -> U32 -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
+  match definition wanted scope:
+    case C.Arrow{name,+domain,+result} Some{+typ} E.Scope{+bindings,+level,open,live,smaller}:
+      S.choose(Result<S.Error,C.Checked>,U32.is_lt(level,4096),u =>
+        S.bind(C.Datatype,C.Checked,G.type_at(types,domain),kind =>
+          S.bind(Unit,C.Checked,G.quantity(token,q,kind),u =>
+            S.bind(C.Checked,C.Checked,next(H.lambda_scope(scope,token,q,domain),result),checked =>
+              H.close(checked,token,H.site(S.at(token),current,0),typ,level,q,domain,bindings,sigs,fuel)))),u => C.exhausted(C.Checked,token))
+    case _ _ _: C.internal(C.Checked,"lambda-type")
+
 def run(fuel: Nat, mode: Mode, +catalog: C.Catalog, +current: U32, +scope: E.Scope) -> Result<S.Error,C.Checked>:
   match fuel mode catalog scope:
     case 0n _ _ _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
-    case 1n+ +n Expression{S.Variable{+token},+wanted} _ _:
-      S.bind(C.Binding,C.Checked,E.lookup(scope,token),binding =>
-        S.bind(C.Checked,C.Checked,variable(binding,token,scope,term => run(n,Rebuild{term},catalog,current,scope)),value => expected(token,wanted,value)))
+    case 1n+ +n Expression{S.Variable{+token},+wanted} C.Catalog{types,+sigs} E.Scope{+bindings,next,open,live,smaller}:
+      S.choose(Result<S.Error,C.Checked>,Bool.and(Bool.not(bound(bindings,token)),H.named(sigs,token)),u =>
+        S.bind(G.FunctionRef,C.Checked,G.find_function(sigs,token,0),reference =>
+          S.bind(G.FunctionRef,C.Checked,callable(reference,token,current,scope),call =>
+            run(n,Named{call,token,Nil{},wanted},catalog,current,scope))),u =>
+        S.bind(C.Binding,C.Checked,E.lookup(scope,token),binding =>
+          S.bind(C.Checked,C.Checked,variable(binding,token,scope,term => run(n,Rebuild{term},catalog,current,scope)),value => expected(token,wanted,value))))
     case 1n+ +n Expression{S.Constructor{+token,+args},+wanted} C.Catalog{+types,sigs} _:
       S.bind(G.ConstructorRef,C.Checked,G.find_constructor(types,token,0),+reference =>
         S.bind(List<&2,C.Parameter>,C.Checked,G.field_signature(reference,types),+params =>
           constructor(reference,args,token,wanted,params,u => run(n,Arguments{args,params,token},catalog,current,scope))))
-    case 1n+ +n Expression{S.Call{+token,+args},+wanted} C.Catalog{types,sigs} _:
-      S.bind(G.FunctionRef,C.Checked,G.find_function(sigs,token,0),reference =>
-        S.bind(G.FunctionRef,C.Checked,callable(reference,token,current,scope),call =>
-          call_body(call,token,wanted,current,scope,params => run(n,Arguments{args,params,token},catalog,current,scope))))
+    case 1n+ +n Expression{S.Call{+token,+args},+wanted} C.Catalog{types,+sigs} E.Scope{bindings,next,open,live,smaller}:
+      S.choose(Result<S.Error,C.Checked>,bound(bindings,token),u =>
+        S.bind(C.Checked,C.Checked,run(n,Expression{S.Variable{token},None{}},catalog,current,scope),function =>
+          S.bind(C.Checked,C.Checked,run(n,Apply{function,args,token},catalog,current,scope),value => expected(token,wanted,value))),u =>
+        S.bind(G.FunctionRef,C.Checked,G.find_function(sigs,token,0),reference =>
+          S.bind(G.FunctionRef,C.Checked,callable(reference,token,current,scope),+call =>
+            S.choose(Result<S.Error,C.Checked>,H.exact_arity(call,args),u =>
+              call_body(call,token,wanted,current,scope,params => run(n,Arguments{args,params,token},catalog,current,scope)),u =>
+              run(n,Named{call,token,args,wanted},catalog,current,scope)))))
+    case 1n+ +n Expression{S.Apply{+token,function,+args},+wanted} _ _:
+      S.bind(C.Checked,C.Checked,run(n,Expression{function,None{}},catalog,current,scope),checked =>
+        S.bind(C.Checked,C.Checked,run(n,Apply{checked,args,token},catalog,current,scope),value => expected(token,wanted,value)))
+    case 1n+ +n Expression{S.Lambda{+token,+q,+body},+wanted} C.Catalog{+types,+sigs} _:
+      S.bind(C.Datatype,C.Checked,H.lambda_type(wanted,token,types),definition =>
+        lambda_body(definition,wanted,scope,token,q,current,types,sigs,1n+n,extended => result =>
+          run(n,Expression{body,Some{result}},catalog,current,extended)))
+    case 1n+ +n Named{G.FunctionRef{+index,C.Signature{name,+params,+result}},+token,+args,+wanted} C.Catalog{+types,sigs} _:
+      split_call(H.prefix(params,args),+first => values => +remaining => +rest =>
+        S.bind(C.Checked,C.Checked,run(n,Arguments{values,first,token},catalog,current,scope),+checked =>
+          S.bind(C.Checked,C.Checked,call_result(checked,token,index,result,current,scope),called =>
+            S.choose(Result<S.Error,C.Checked>,missing(remaining),u =>
+              S.bind(Unit,C.Checked,H.arity(wanted,token,types),u =>
+                S.bind(C.Checked,C.Checked,H.partial(checked,token,index,result,first,remaining,current,scope,catalog,1n+n),value => expected(token,wanted,value))),u =>
+              S.bind(C.Checked,C.Checked,run(n,Apply{called,rest,token},catalog,current,scope),value => expected(token,wanted,value))))))
+    case 1n+ +n Apply{function,Nil{},token} _ _: Done{function}
+    case 1n+ +n Apply{+function,Con{+head,+tail},+token} C.Catalog{types,sigs} _:
+      S.bind(C.Datatype,C.Checked,H.arrow(types,function_type(function),token),definition =>
+        apply_type(definition,domain => +result =>
+          S.bind(C.Checked,C.Checked,run(n,Expression{head,Some{domain}},catalog,current,scope),argument =>
+            S.bind(C.Checked,C.Checked,H.invoke(function,argument,token,result),value => run(n,Apply{value,tail,token},catalog,current,scope)))))
     case 1n+ +n Expression{S.Binding{+token,+q,ann,+value,+body},+wanted} C.Catalog{+types,sigs} E.Scope{bindings,+next,from,live,smaller}:
       S.choose(Result<S.Error,C.Checked>,U32.is_eq(next,4096),u => C.exhausted(C.Checked,token),u =>

`src/closure-LAWS.bend:29-36` (added)
   29  law invoke_has_one_dispatch:
   30    for +token: S.Token
   31    for +index: U32
   32    for +result: U32
   33    for +function: C.Term
   34    for +argument: C.Term
   35    {F.apply(token,index,result,function,argument) == C.Application{token,index,result,[function,argument]} : C.Term}
   36  

`src/closure.bend:220-228` (added)
  220  def prepare(found: Inventory, +original: C.Book, +count: U32, +depth: Nat) -> Result<S.Error,Plan>:
  221    match found original:
  222      case Inventory{sites,Nil{}} book: Done{Plan{book,count,Nil{},False{}}}
  223      case Inventory{+sites,+used} C.Book{+datatypes,+definitions}:
  224        +table = dispatches(datatypes,used,sites,0,count)
  225        S.bind(List<&2,C.Function>,Plan,functions(definitions,depth,table),+originals =>
  226          S.bind(List<&2,C.Function>,Plan,dispatchers(table,sites,depth,table),generated =>
  227            Done{Plan{C.Book{types(datatypes,sites,0),List.append(&2,C.Function,originals,generated)},count,used,True{}}}))
  228  

@@ -116,4 +129,8 @@ def step(state: State, +book: C.Book) -> Result<S.Error,State>:
     case Evaluate{C.Application{token,index,type_id,+args},+env,+frames} C.Book{types,functions}:
       S.bind(C.Function,State,function_at(functions,index),function => Done{enter(function,args,env,frames)})
+    case Evaluate{C.Closure{token,site,typ,level,q,domain,captures,body},env,frames} _:
+      Done{Capture{site,typ,level,captures,body,env,Nil{},frames}}
+    case Evaluate{C.Invoke{token,arrow,typ,function,argument},+env,frames} _:
+      Done{Evaluate{function,env,Con{ApplyArgument{argument,env},frames}}}
     case Evaluate{C.Let{token,+level,q,type_id,+value,+body},+env,+frames} _:
       S.choose(Result<S.Error,State>,U32.is_eq(q,0),u => Done{Evaluate{body,env,frames}},u =>

@@ -221,21 +273,24 @@ def extend_sections(old: Sections, parts: Sections) -> Result<S.Error,Sections>:
             S.bind(B.Builder,Sections,W.join(d,dd),code => Done{Sections{types,funcs,exports,code}}))))
 
-def entry(function: C.Function, +index: U32, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,Sections>:
+def entry(function: C.Function, +index: U32, +exports: U32, +tails: Bool, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,Sections>:
   match function:
-    case C.Function{C.Signature{token,+params,result},term}:
+    case C.Function{C.Signature{+token,+params,result},+term}:
       S.bind(B.Builder,Sections,function_type(cap,live_types(params)),types =>
         S.bind(B.Builder,Sections,W.unsigned(cap,index),funcs =>
-          S.bind(B.Builder,Sections,W.concat(cap,[W.name(cap,S.text(token)),W.bytes(cap,[0]),W.unsigned(cap,index)]),exports =>
-            S.bind(B.Builder,Sections,body(parameters(params,0,0,Nil{}),term,heap,all,depth,cap),code => Done{Sections{types,funcs,exports,code}}))))
+          S.bind(B.Builder,Sections,S.choose(Result<S.Error,B.Builder>,U32.is_lt(index,exports),u =>
+            W.concat(cap,[W.name(cap,S.text(token)),W.bytes(cap,[0]),W.unsigned(cap,index)]),u => Done{B.empty(cap)}),names =>
+            S.bind(B.Builder,Sections,S.choose(Result<S.Error,B.Builder>,tails,u =>
+              closure_body(parameters(params,0,0,Nil{}),term,U32.is_ge(index,exports),heap,all,depth,cap),u =>
+              body(parameters(params,0,0,Nil{}),term,heap,all,depth,cap)),code => Done{Sections{types,funcs,names,code}}))))
 
-def entries(remaining: List<&2,C.Function>, +index: U32, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32, previous: Sections) -> Result<S.Error,Sections>:
+def entries(remaining: List<&2,C.Function>, +index: U32, +exports: U32, +tails: Bool, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32, previous: Sections) -> Result<S.Error,Sections>:
   match remaining:
     case Nil{}: Done{previous}
     case Con{head,+tail}:
-      S.bind(Sections,Sections,entry(head,index,heap,all,depth,cap),parts =>
-        S.bind(Sections,Sections,extend_sections(previous,parts),next => entries(tail,U32.add(index,1),heap,all,depth,cap,next)))
+      S.bind(Sections,Sections,entry(head,index,exports,tails,heap,all,depth,cap),parts =>
+        S.bind(Sections,Sections,extend_sections(previous,parts),next => entries(tail,U32.add(index,1),exports,tails,heap,all,depth,cap,next)))
 
-# The sole unreachable in this profile is the arena guard. Subtract before
-# adding: every successful allocation keeps 0 <= bump <= 65536 without wrap.
+# Subtract before adding: every successful allocation keeps
+# 0 <= bump <= 65536 without wrap.
 def allocator(+cap: U32) -> Result<S.Error,B.Builder>:
   S.bind(B.Builder,B.Builder,W.concat(cap,[local_declarations(cap,1),instruction(cap,35,0),instruction(cap,33,1),
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
