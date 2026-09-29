<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=generics; head=19a534d33af4; base=481bb3188010; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/type-erasure-PROOF.bend@19a534d3 sha256=a3f959f232cab4ec55896fa873a7b207483dc810ce7e698e26809185ad66d212; tests/compiler-generics/LAW_REVIEW.md@19a534d3 sha256=e7376ca83ef99a21c439127849d25e375faf3765c15a078eee22fdea6d53e6b4 -->
# Claim
tests/compiler-generics/LAW_REVIEW.md:31-33 (section: Generic checking and erasure review) - verbatim text:

> `src/type-erasure-PROOF.bend` fills all 17 erasure
> laws. Its evaluator equations quantify over environments, frames, arguments and
> books, with an explicit one-step fuel adjustment.

# Evidence
Evidence: the diff of the paths the claim names.
```diff
diff --git a/src/type-erasure-PROOF.bend b/src/type-erasure-PROOF.bend
new file mode 100644
index 00000000..1db384f9
--- /dev/null
+++ b/src/type-erasure-PROOF.bend
@@ -0,0 +1,44 @@
+import Base
+import ./types-PROOF.bend as Types
+import ./syntax.bend as S
+import ./core.bend as C
+import ./generic-catalog.bend as G
+import ./type-erasure.bend as E
+import ./wasm.bend as W
+import ./type-erasure-LAWS.bend as L
+
+def L.empty_family(token,q,kind,params,generic): {==}
+def L.nominal_identity(index): {==}
+def L.application_erases_argument(function,argument): {==}
+def L.parameter_retains_quantity(token,q,typ): {==}
+def L.plain_fields(token,params): {==}
+def L.plain_arguments(token,args): {==}
+def L.plain_bindings(token,params): {==}
+def L.generic_fields(token,params): {==}
+def L.generic_arguments(token,args): {==}
+def L.generic_bindings(token,params): {==}
+def L.generic_nullary_is_boxed(token,typ,tag): {==}
+def L.plain_nullary_is_ordinal(token,typ,tag): {==}
+
+def L.generic_constructor_uses_memory(token,params):
+  match params:
+    case Nil{}: {==}
+    case Con{head,tail}: {==}
+
+def L.generic_branch_uses_memory(token,params,tag,body):
+  match params:
+    case Nil{}: {==}
+    case Con{head,tail}: {==}
+
+def L.marker_retains_live_signature(token,params):
+  match params:
+    case Nil{}: {==}
+    case Con{G.Parameter{name,+q,typ},+tail}:
+      Equal.cong(List<&2,U32>,List<&2,U32>,
+        xs => S.choose(List<&2,U32>,U32.is_eq(q,0),u => xs,u => Con{127,xs}),
+        W.live_types(E.fields(token,tail,True{})),W.live_types(E.parameters(tail)),
+        L.marker_retains_live_signature(token,tail))
+
+def L.erased_argument_commutes(fuel,token,typ,params,head,args,level,caller,callee,body,frames,book): {==}
+def L.erased_field_commutes(fuel,type_id,tag,token,typ,params,head,args,env,values,frames,book): {==}
+def L.erased_pattern_commutes(fuel,token,level,typ,parameter,known,params,values,env,body,frames,book): {==}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
