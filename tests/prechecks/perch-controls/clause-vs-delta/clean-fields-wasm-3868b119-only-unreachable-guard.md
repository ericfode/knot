<!-- prechecks packet v1; rule=clause-vs-delta; increment=fields-wasm; head=3868b119f8ba; base=185b7d5ffad5; builder=scripts/prechecks/packets@3a2ef420dff1; sources: scripts/run-wasm.mjs@3868b119 sha256=1b4d183c2de37d1b1b5c756db0be94412b9aa85b6dbe70f416993aee18222737; src/CONTRACT.json@3868b119 sha256=dcf30a4b0ef7e600ce2753b84155b98c9135b087aee6f214676b8e1617edeb3f; src/wasm.bend@3868b119 sha256=efd76356f4dc6bea21b822295e49c1d3d8c1bfc4d9a0101fa6e81d75458178e3; tests/compiler-fields-wasm/LAWS.bend@3868b119 sha256=f5ef175cc720ec4e8d2da95ae42f876fae92f295ed1b0d6dab3c53e10fe26aa9; tests/compiler-fields-wasm/arena.mjs@3868b119 sha256=58ad1dc68e8b763e15eaaf22936596b90782eeee1a7275ddae5862278519088a; tests/compiler-fields-wasm/check.py@3868b119 sha256=544de0f4486cc62c8ec3fe1150bf29561f0e9e3cf1570fecd07e314fe3066d74 -->
# Claim
Invariance clause (src/CONTRACT.json):

> unsigned size > 65536 - bump; only unreachable in the profile

# Evidence
Evidence: the governed diff hunks (base to head).
```
diff --git a/scripts/run-wasm.mjs b/scripts/run-wasm.mjs
index 441afb5f..e3769893 100644
--- a/scripts/run-wasm.mjs
+++ b/scripts/run-wasm.mjs
@@ -2,6 +2,10 @@
 // Host adapter only: file I/O, WebAssembly validation/instantiation, invocation.
 import fs from 'node:fs/promises';
-const [path, name, ...raw] = process.argv.slice(2);
+const argv = process.argv.slice(2);
+const profile = argv[0]?.startsWith('--profile=') ? argv.shift().slice(10) : 'knot-enum-1';
+const [path, name, ...raw] = argv;
+let invoking = false;
 try {
+  if (!['knot-enum-1', 'knot-fields-wasm-1'].includes(profile)) throw new Error('unknown Wasm profile');
   if (!path || !name || raw.some(x => !/^(0|[1-9][0-9]*)$/.test(x))) throw new Error('expected module export [ordinal ...]');
   const args = raw.map(Number);

@@ -10,13 +14,24 @@ try {
   if (!WebAssembly.validate(bytes)) throw new Error('Wasm validation failed');
   const module = await WebAssembly.compile(bytes);
-  if (WebAssembly.Module.imports(module).length !== 0) throw new Error('enum profile requires no imports');
+  if (WebAssembly.Module.imports(module).length !== 0) throw new Error('Knot profiles require no imports');
   const instance = await WebAssembly.instantiate(module);
   const entry = Object.hasOwn(instance.exports, name) ? instance.exports[name] : undefined;
   if (typeof entry !== 'function' || entry.length !== args.length) throw new Error('unknown export or wrong live arity');
+  invoking = true;
   const result = entry(...args);
+  invoking = false;
   if (!Number.isInteger(result) || result < 0 || result > 255) throw new Error('result outside enum-profile bounds');
   console.log(JSON.stringify({validated: true, export: name, arguments: args, result, bytes: bytes.length}));
 } catch (error) {
-  console.error(`HostFailure\twasm\t${error.message}`);
-  process.exitCode = 5;
+  // The fields profile's only unreachable is the bounded arena guard. Profile
+  // selection asserts compiler provenance; this is not an arbitrary-Wasm ABI.
+  const stack = invoking && error instanceof RangeError && /maximum call stack size exceeded/i.test(error.message);
+  const arena = invoking && profile === 'knot-fields-wasm-1' && error instanceof WebAssembly.RuntimeError && error.message === 'unreachable';
+  if (stack || arena) {
+    console.error(`Exhausted\twasm\t${stack ? 'call-stack' : 'arena-overflow'}`);
+    process.exitCode = 4;
+  } else {
+    console.error(`HostFailure\twasm\t${error.message}`);
+    process.exitCode = 5;
+  }
 }

diff --git a/src/wasm.bend b/src/wasm.bend
index 19b1c33a..a70aa30b 100644
--- a/src/wasm.bend
+++ b/src/wasm.bend
@@ -12,8 +12,44 @@ type Environment is Data:
 type Code is Data:
   Code{bytes: B.Builder, next: U32}
+type Profile is Data:
+  Enum{}
+  Fields{}
 type Mode is Data:
   Expression{term: C.Term}
   Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>}
-  Branches{terms: List<&2,C.Term>, index: U32}
+  Cell{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, slots: List<&2,U32>, tag: U32}
+  Branches{terms: List<&2,C.Term>, index: U32, pointer: Maybe<&2,U32>}
+  Arm{term: C.Term, pointer: Maybe<&2,U32>}
+  Unpack{fields: List<&2,C.Binding>, pointer: U32, offset: U32, body: C.Term}
+
+def fielded(constructors: List<&2,C.Constructor>) -> Bool:
+  match constructors:
+    case Nil{}: False{}
+    case Con{C.Constructor{token,Nil{}},tail}: fielded(tail)
+    case Con{C.Constructor{token,Con{head,tail}},rest}: True{}
+
+def heap_types(types: List<&2,C.Datatype>, +index: U32) -> List<&2,U32>:
+  match types:
+    case Nil{}: Nil{}
+    case Con{C.Datatype{token,reusable,constructors},+tail}:
+      S.choose(List<&2,U32>,fielded(constructors),u => Con{index,heap_types(tail,U32.add(index,1))},u => heap_types(tail,U32.add(index,1)))
+
+def boxed(types: List<&2,U32>, +index: U32) -> Bool:
+  match types:
+    case Nil{}: False{}
+    case Con{head,tail}: Bool.or(U32.is_eq(head,index),boxed(tail,index))
+
+# Checked cases are exhaustive; their field signatures describe the scrutinee.
+# Case.type_id describes the result, which may have a different representation.
+def fielded_arms(arms: List<&2,C.Term>) -> Bool:
+  match arms:
+    case Nil{}: False{}
+    case Con{C.Branch{tag,Con{head,tail},body},rest}: True{}
+    case Con{head,tail}: fielded_arms(tail)
+
+def capability(profile: Profile, types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
+  match profile:
+    case Enum{}: K.enum_profile(types)
+    case Fields{}: Done{Unit{}}
 
 def internal(-A: Type, code: String) -> Result<S.Error,A>:

@@ -147,22 +227,59 @@ def entry(function: C.Function, +index: U32, +all: List<&2,C.Function>, +depth:
         S.bind(B.Builder,Sections,W.unsigned(cap,index),funcs =>
           S.bind(B.Builder,Sections,W.concat(cap,[W.name(cap,S.text(token)),W.bytes(cap,[0]),W.unsigned(cap,index)]),exports =>
-            S.bind(B.Builder,Sections,body(parameters(params,0,0,Nil{}),term,all,depth,cap),code => Done{Sections{types,funcs,exports,code}}))))
+            S.bind(B.Builder,Sections,body(parameters(params,0,0,Nil{}),term,heap,all,depth,cap),code => Done{Sections{types,funcs,exports,code}}))))
 
-def entries(remaining: List<&2,C.Function>, +index: U32, +all: List<&2,C.Function>, +depth: Nat, +cap: U32, previous: Sections) -> Result<S.Error,Sections>:
+def entries(remaining: List<&2,C.Function>, +index: U32, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32, previous: Sections) -> Result<S.Error,Sections>:
   match remaining:
     case Nil{}: Done{previous}
     case Con{head,+tail}:
-      S.bind(Sections,Sections,entry(head,index,all,depth,cap),parts =>
-        S.bind(Sections,Sections,extend_sections(previous,parts),next => entries(tail,U32.add(index,1),all,depth,cap,next)))
+      S.bind(Sections,Sections,entry(head,index,heap,all,depth,cap),parts =>
+        S.bind(Sections,Sections,extend_sections(previous,parts),next => entries(tail,U32.add(index,1),heap,all,depth,cap,next)))
+
+# The sole unreachable in this profile is the arena guard. Subtract before
+# adding: every successful allocation keeps 0 <= bump <= 65536 without wrap.
+def allocator(+cap: U32) -> Result<S.Error,B.Builder>:
+  S.bind(B.Builder,B.Builder,W.concat(cap,[local_declarations(cap,1),instruction(cap,35,0),instruction(cap,33,1),
+    instruction(cap,32,0),constant(cap,65536),instruction(cap,35,0),W.bytes(cap,[107,75,4,64,0,11]),
+    instruction(cap,35,0),instruction(cap,32,0),W.bytes(cap,[106]),instruction(cap,36,0),instruction(cap,32,1),W.bytes(cap,[11])]),body => W.sized(cap,body))
+
+def heap_sections(+cap: U32, heap: Bool) -> Result<S.Error,B.Builder>:
+  match heap:
+    case False{}: Done{B.empty(cap)}
+    case True{}:
+      S.bind(B.Builder,B.Builder,W.bytes(cap,[1,1,1,1]),memory =>
+        S.bind(B.Builder,B.Builder,W.bytes(cap,[1,127,1,65,0,11]),global =>
+          W.concat(cap,[W.section(cap,5,memory),W.section(cap,6,global)])))
 
-def module_bytes(parts: Sections, +cap: U32) -> Result<S.Error,List<&2,U32>>:
+def module_bytes(parts: Sections, +heap: Bool, +cap: U32) -> Result<S.Error,List<&2,U32>>:
   match parts:
     case Sections{types,funcs,exports,code}:
-      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[W.bytes(cap,[0,97,115,109,1,0,0,0]),W.section(cap,1,types),W.section(cap,3,funcs),W.section(cap,7,exports),W.section(cap,10,code)]),result => Done{B.finish(result)})
+      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[W.bytes(cap,[0,97,115,109,1,0,0,0]),W.section(cap,1,types),W.section(cap,3,funcs),heap_sections(cap,heap),W.section(cap,7,exports),W.section(cap,10,code)]),result => Done{B.finish(result)})
 
-def emit(book: C.Book, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
+def finish(parts: Sections, heap: Bool, index: U32, +cap: U32) -> Result<S.Error,List<&2,U32>>:
+  match heap:
+    case False{}: module_bytes(parts,False{},cap)
+    case True{}:
+      S.bind(B.Builder,List<&2,U32>,function_type(cap,[127]),types =>
+        S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,index),funcs =>
+          S.bind(B.Builder,List<&2,U32>,allocator(cap),code =>
+            S.bind(Sections,List<&2,U32>,extend_sections(parts,Sections{types,funcs,B.empty(cap),code}),all => module_bytes(all,True{},cap)))))
+
+def present(types: List<&2,U32>) -> Bool:
+  match types:
+    case Nil{}: False{}
+    case Con{head,tail}: True{}
+
+def profiled(+heap: List<&2,U32>, +functions: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
+  +size = U32.from_nat(List.length(&2,C.Function,functions))
+  S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,U32.add(size,Bool.pick(U32,present(heap),1,0))),+count =>
+    S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,size),exports =>
+      S.bind(Sections,List<&2,U32>,entries(functions,0,heap,functions,depth,cap,Sections{count,count,exports,count}),parts => finish(parts,present(heap),size,cap))))
+
+def emit_profile(+profile: Profile, book: C.Book, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
   match book:
-    case C.Book{types,+functions}:
-      S.bind(Unit,List<&2,U32>,K.enum_profile(types),u =>
-      S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,U32.from_nat(List.length(&2,C.Function,functions))),+count =>
-        S.bind(Sections,List<&2,U32>,entries(functions,0,functions,depth,cap,Sections{count,count,count,count}),parts => module_bytes(parts,cap))))
+    case C.Book{+types,+functions}:
+      S.bind(Unit,List<&2,U32>,capability(profile,types),u => profiled(heap_types(types,0),functions,depth,cap))
+
+# The original entry retains its enum-only capability and byte contract.
+def emit(book: C.Book, depth: Nat, cap: U32) -> Result<S.Error,List<&2,U32>>:
+  emit_profile(Enum{},book,depth,cap)

`tests/compiler-fields-wasm/LAWS.bend:7-10` (added)
    7  law enum_capability_preserved:
    8    for +types: List<&2,C.Datatype>
    9    {W.capability(W.Enum{},types) == K.enum_profile(types) : Result<S.Error,Unit>}
   10  

`tests/compiler-fields-wasm/arena.mjs:10-16` (added)
   10  const entry = instance.exports[name];
   11  for (let i = 0; i < count; i++) assert.equal(entry(...args), expected);
   12  for (let i = 0; i < 2; i++) {
   13    assert.throws(() => entry(...args), error => error instanceof WebAssembly.RuntimeError && error.message === 'unreachable');
   14  }
   15  console.log(JSON.stringify({successful: count, overflow: count + 1, repeatedOverflow: true}));
   16  

`tests/compiler-fields-wasm/check.py:20-20` (added)
   20  PROFILE = '--profile=knot-fields-wasm-1'

`tests/compiler-fields-wasm/check.py:80-102` (added)
   80  def instructions(wat, heap):
   81      allowed = {'local.get', 'local.set', 'i32.const', 'call', 'i32.eq', 'if', 'else', 'end'}
   82      if heap:
   83          allowed |= {'global.get', 'global.set', 'i32.load', 'i32.store', 'i32.add',
   84                      'i32.sub', 'i32.gt_u', 'unreachable'}
   85      observed, traps = set(), 0
   86      for line in wat.splitlines():
   87          line = line.strip()
   88          if not line or line == ')' or line.startswith(('(module', '(type', '(func',
   89                  '(export', '(local', '(memory', '(global', ';;')):
   90              continue
   91          opcode = line.split()[0].rstrip(')')
   92          require(opcode in allowed, ('instruction outside profile', line))
   93          observed.add(opcode); traps += opcode == 'unreachable'
   94      require(traps == int(heap), ('arena is the only unreachable', traps, heap))
   95      require(wat.count('(memory ') == int(heap) and wat.count('(global ') == int(heap), 'heap sections')
   96      if heap:
   97          require('(memory (;0;) 1 1)' in wat, 'one fixed memory page')
   98          require('(global (;0;) (mut i32) (i32.const 0))' in wat, 'initial bump')
   99      exports = re.findall(r'\(export "[^"]+" \(func (\d+)\)\)', wat)
  100      functions = re.findall(r'^  \(func ', wat, re.M)
  101      require([int(i) for i in exports] == list(range(len(functions) - int(heap))), 'index-stable function exports')
  102      return sorted(observed)
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
