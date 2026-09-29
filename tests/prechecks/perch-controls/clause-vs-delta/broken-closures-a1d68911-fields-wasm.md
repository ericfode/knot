<!-- prechecks packet v1; rule=clause-vs-delta; increment=closures; head=a1d68911d5fa; base=fa31fec064ba; builder=scripts/prechecks/packets@40e325337e4a; sources: src/CONTRACT.json@a1d68911 sha256=cfb3530115e505e1e1b8cfcd2420d33b351c12c39fb48bc6246a754063a1e10c; src/catalog.bend@a1d68911 sha256=63ae5138855d8fe70dd05f2bb83d80afe0ed11b7a42112ff53be9076c8e8e55f; src/check.bend@a1d68911 sha256=e74f6449394f7b2f919a01759177c30b32c68d257960a2d6814889b0b24868cb; src/checked-display.bend@a1d68911 sha256=8fa67b838a44b1643799ddfdaaa4aa66206de623fb430610fc2732932639d459; src/closure-LAWS.bend@a1d68911 sha256=e42d0b0f77801fbf9b01cda68d1b6dafeddc00473b5ae215ff7bb967c5f4facf; src/closure-PROOF.bend@a1d68911 sha256=be31b24e6376c7a01e3fc4ecb7d4f1332b923119a68347f41ed555f4427840de; src/closure-check-LAWS.bend@a1d68911 sha256=0ad2e499a3c09883a6a9f3bf1528a35298c59b668da946c68fd69cfce2bff3df -->
# Claim
Invariance clause (src/CONTRACT.json):

> All original functions at unchanged indices; per-arrow dispatchers and allocator appended and unexported; no memory or global exports.

# Evidence
Evidence: the governed diff hunks (base to head).
```
@@ -58,4 +57,5 @@ def find_constructor(types: List<&2,C.Datatype>, +name: S.Token, +index: U32) ->
     case Con{C.Datatype{token,data,ctors},+tail}:
       constructor_next(constructor_tag(ctors,name,0),index,u => find_constructor(tail,name,U32.add(index,1)))
+    case Con{C.Arrow{token,domain,result},tail}: find_constructor(tail,name,U32.add(index,1))
 
 def constructors(nodes: List<&2,S.Node>, +seen: List<&2,S.Token>, +count: U32) -> Result<S.Error,List<&2,C.Constructor>>:

@@ -95,4 +95,5 @@ def unique_constructors(types: List<&2,C.Datatype>, seen: List<&2,S.Token>) -> R
     case Con{C.Datatype{name,data,tokens},+tail}:
       S.bind(List<&2,S.Token>,Unit,distinct_constructors(tokens,seen),next => unique_constructors(tail,next))
+    case Con{C.Arrow{name,domain,result},tail}: unique_constructors(tail,seen)
 
 def quantity(+token: S.Token, +q: U32, definition: C.Datatype) -> Result<S.Error,Unit>:

@@ -101,4 +102,7 @@ def quantity(+token: S.Token, +q: U32, definition: C.Datatype) -> Result<S.Error
       S.choose(Result<S.Error,Unit>,U32.is_gt(q,2),u => C.internal(Unit,"quantity-range"),u =>
         S.choose(Result<S.Error,Unit>,Bool.and(U32.is_eq(q,2),Bool.not(data)),u => C.invalid(Unit,"reusable-type",token),u => Done{Unit{}}))
+    case C.Arrow{name,domain,result}:
+      S.choose(Result<S.Error,Unit>,U32.is_gt(q,2),u => C.internal(Unit,"quantity-range"),u =>
+        S.choose(Result<S.Error,Unit>,U32.is_eq(q,2),u => C.invalid(Unit,"reusable-type",token),u => Done{Unit{}}))
 
 def parameter_type(+token: S.Token, +q: U32, reference: TypeRef) -> Result<S.Error,C.Parameter>:

@@ -207,4 +212,5 @@ def definition_fields(definition: C.Datatype, tag: U32) -> Result<S.Error,List<&
   match definition:
     case C.Datatype{token,data,ctors}: fields_at(ctors,tag)
+    case C.Arrow{token,domain,result}: C.internal(List<&2,C.Parameter>,"function-constructor")
 
 def field_signature(reference: ConstructorRef, types: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Parameter>>:

@@ -223,2 +229,6 @@ def constructor_named(types: List<&2,C.Datatype>, +name: S.Token) -> Bool:
     case Con{C.Datatype{token,data,ctors},tail}:
       Bool.or(has_tag(constructor_tag(ctors,name,0)),constructor_named(tail,name))
+    case Con{C.Arrow{token,domain,result},tail}: constructor_named(tail,name)
+
+def arrow_id(types: List<&2,C.Datatype>, domain: U32, result: U32) -> Result<S.Error,U32>:
+  F.arrow_id(types,domain,result)

@@ -116,4 +119,5 @@ def complete_arms(definition: C.Datatype, seen: List<&2,U32>, +token: S.Token) -
     case C.Datatype{name,data,tokens}:
       S.choose(Result<S.Error,Unit>,Nat.is_eq(List.length(&2,C.Constructor,tokens),List.length(&2,U32,seen)),u => Done{Unit{}},u => C.invalid(Unit,"missing-arm",token))
+    case C.Arrow{name,domain,result}: C.invalid(Unit,"unmatchable-binder",token)
 
 def patterns(nodes: List<&2,S.Node>, +types: List<&2,C.Datatype>, +type_id: U32, +seen: List<&2,U32>, +token: S.Token) -> Result<S.Error,Unit>:

@@ -263,4 +327,5 @@ def enum_profile(types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
     case Con{C.Datatype{token,data,ctors},tail}:
       S.bind(Unit,Unit,enum_constructors(ctors),u => enum_profile(tail))
+    case Con{C.Arrow{token,domain,result},tail}: enum_profile(tail)
 
 def resolved(+catalog: C.Catalog, nodes: List<&2,S.Node>, depth: Nat) -> Result<S.Error,C.Book>:

diff --git a/src/checked-display.bend b/src/checked-display.bend
index 90a0d86b..57caf033 100644
--- a/src/checked-display.bend
+++ b/src/checked-display.bend
@@ -20,4 +20,8 @@ def term(fuel: Nat, value: C.Term) -> Result<S.Error,String>:
     case 1n+ +n C.Application{token,index,type_id,args}:
       D.concat([Done{"call"},Done{U32.show(index)},Done{"("},term(n,C.Sequence{args}),Done{")"}])
+    case 1n+ +n C.Closure{token,site,type_id,level,q,domain,captures,body}:
+      D.concat([Done{"close"},Done{U32.show(site)},Done{":"},Done{U32.show(type_id)},Done{"["},Done{binders(captures)},Done{"] "},Done{U32.show(q)},Done{" $"},Done{U32.show(level)},Done{"=>"},term(n,body)])
+    case 1n+ +n C.Invoke{token,arrow,type_id,function,argument}:
+      D.concat([Done{"apply"},Done{U32.show(arrow)},Done{"("},term(n,function),Done{";"},term(n,argument),Done{")"}])
     case 1n+ +n C.Let{token,level,q,type_id,value,body}:
       D.concat([Done{"let"},Done{U32.show(q)},Done{" $"},Done{U32.show(level)},Done{":"},Done{U32.show(type_id)},Done{"="},term(n,value),Done{" in "},term(n,body)])

`src/closure-LAWS.bend:37-40` (added)
   37  law outer_levels_are_unchanged:
   38    for +id: U32
   39    {F.level(F.Same{},id) == id : U32}
   40  

`src/closure-PROOF.bend:15-15` (added)
   15  def L.outer_levels_are_unchanged(id): {==}

`src/closure-check-LAWS.bend:44-53` (added)
   44  law affine_capture_cannot_be_consumed_twice:
   45    for +token: S.Token
   46    for function: C.Term
   47    for argument: C.Term
   48    for arrow: U32
   49    for domain: U32
   50    for result: U32
   51    {H.invoke(C.Checked{function,arrow,[3]},C.Checked{argument,domain,[3]},token,result) ==
   52      Fail{S.Invalid{"check","affine-reuse",S.at(token)}} : Result<S.Error,C.Checked>}
   53  

`src/closure-check-PROOF.bend:8-8` (added)
    8  def L.affine_capture_cannot_be_consumed_twice(token,function,argument,arrow,domain,result): {==}

`src/closure-check-PROOF.bend:13-13` (added)
   13  def L.apply_evaluates_the_function_first(token,arrow,typ,function,argument,caller,frames,book): {==}

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

@@ -270,14 +325,25 @@ def present(types: List<&2,U32>) -> Bool:
     case Con{head,tail}: True{}
 
-def profiled(+heap: List<&2,U32>, +functions: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
+def assembled(+heap: List<&2,U32>, +functions: List<&2,C.Function>, +exports: U32, +tails: Bool, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
   +size = U32.from_nat(List.length(&2,C.Function,functions))
   S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,U32.add(size,Bool.pick(U32,present(heap),1,0))),+count =>
-    S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,size),exports =>
-      S.bind(Sections,List<&2,U32>,entries(functions,0,heap,functions,depth,cap,Sections{count,count,exports,count}),parts => finish(parts,present(heap),size,cap))))
+    S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,exports),names =>
+      S.bind(Sections,List<&2,U32>,entries(functions,0,exports,tails,heap,functions,depth,cap,Sections{count,count,names,count}),parts => finish(parts,present(heap),size,cap))))
+
+def profiled(heap: List<&2,U32>, +functions: List<&2,C.Function>, depth: Nat, cap: U32) -> Result<S.Error,List<&2,U32>>:
+  assembled(heap,functions,U32.from_nat(List.length(&2,C.Function,functions)),False{},depth,cap)
+
+def lowered(plan: F.Plan, profile: Profile, depth: Nat, cap: U32) -> Result<S.Error,List<&2,U32>>:
+  match plan profile:
+    case F.Plan{C.Book{types,functions},exports,heap,False{}} _: profiled(heap_types(types,0),functions,depth,cap)
+    case F.Plan{book,exports,heap,True{}} Enum{}: Fail{S.Unsupported{"compile","closures",S.At{0,0,0,0}}}
+    case F.Plan{C.Book{types,functions},exports,heap,True{}} Fields{}:
+      assembled(List.append(&2,U32,heap,heap_types(types,0)),functions,exports,True{},depth,cap)
 
 def emit_profile(+profile: Profile, book: C.Book, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
   match book:
     case C.Book{+types,+functions}:
-      S.bind(Unit,List<&2,U32>,capability(profile,types),u => profiled(heap_types(types,0),functions,depth,cap))
+      S.bind(Unit,List<&2,U32>,capability(profile,types),u =>
+        S.bind(F.Plan,List<&2,U32>,F.run(C.Book{types,functions},depth),plan => lowered(plan,profile,depth,cap)))
 
 # The original entry retains its enum-only capability and byte contract.
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
