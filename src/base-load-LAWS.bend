import Base
import ./syntax.bend as S
import ./base-load.bend as B

# Boundary and composition laws for inventory and selection, not a Base proof.
law empty_inventory:
  {B.inventory("") == Nil{} : List<&2,B.Decl>}

law constructor_inventory:
  {B.names(B.inventory("type Flag is Data:\n  Off{}\n  On{}\ndef keep(x: Flag) -> Flag:\n  x\n")) ==
    ["Flag","Off","On","keep"] : List<&2,String>}

law claim_and_fill_share_identity:
  for +claim: String
  for +fill: String
  for +other: String
  {B.coalesce([B.Decl{"f",["f"],claim,False{}},B.Decl{"g",["g"],other,False{}},B.Decl{"f",["f"],fill,False{}}],Nil{}) ==
    [B.Decl{"f",["f"],String.append(claim,fill),False{}},B.Decl{"g",["g"],other,False{}}] : List<&2,B.Decl>}

law bound_name_is_not_dependency:
  for at: S.At
  {B.references(1n,S.Variable{S.Token{"Bool",at}},["Bool"]) == Done{Nil{}} : Result<S.Error,List<&2,B.Use>>}

law free_name_is_dependency:
  for at: S.At
  {B.references(1n,S.Variable{S.Token{"Bool",at}},Nil{}) == Done{[B.Use{"Bool",False{}}]} : Result<S.Error,List<&2,B.Use>>}

law parameter_name_is_not_dependency:
  for at: S.At
  {B.references(4n,S.Function{S.Token{"f",at},[S.Parameter{S.Token{"Bool",at},1,S.Token{"Flag",at}}],
      S.Token{"Flag",at},S.Variable{S.Token{"Bool",at}}},Nil{}) ==
    Done{[B.Use{"Flag",False{}},B.Use{"Flag",False{}}]} : Result<S.Error,List<&2,B.Use>>}

law term_reference_ignores_constructor:
  for source: String
  {B.dependencies([B.Use{"Some",False{}}],[B.Decl{"Maybe",["Maybe","Some"],source,False{}}],Nil{}) ==
    Nil{} : List<&2,String>}

law constructor_reference_ignores_term:
  for source: String
  {B.dependencies([B.Use{"Bool",True{}}],[B.Decl{"Bool",["Bool","False","True"],source,False{}}],Nil{}) ==
    Nil{} : List<&2,String>}

law user_constructor_preserves_base_type:
  for source: String
  {B.dependencies([B.Use{"Bool",False{}}],[B.Decl{"Bool",["Bool","False","True"],source,False{}}],[B.Use{"Bool",True{}}]) ==
    ["Bool"] : List<&2,String>}

law user_type_preserves_base_constructor:
  for source: String
  {B.dependencies([B.Use{"Some",True{}}],[B.Decl{"Maybe",["Maybe","Some"],source,False{}}],[B.Use{"Some",False{}}]) ==
    ["Maybe"] : List<&2,String>}

law user_term_shadows_same_category:
  for source: String
  {B.dependencies([B.Use{"Bool",False{}}],[B.Decl{"Bool",["Bool","False","True"],source,False{}}],[B.Use{"Bool",False{}}]) ==
    Nil{} : List<&2,String>}

law declaration_inventory_keeps_category:
  for +at: S.At
  {B.declarations([S.Datatype{S.Token{"Some",at},False{},[S.Constructor{S.Token{"Bool",at},Nil{}}]}]) ==
    [B.Use{"Some",False{}},B.Use{"Bool",True{}}] : List<&2,B.Use>}

law selection_follows_source_order:
  for +first: S.Node
  for +second: S.Node
  for +source: String
  {B.partition([B.Decl{"a",["a"],source,False{}},B.Decl{"b",["b"],source,False{}}],
      [B.Selected{"b",second},B.Selected{"a",first}]) ==
    B.partition([B.Decl{"a",["a"],source,False{}},B.Decl{"b",["b"],source,False{}}],
      [B.Selected{"a",first},B.Selected{"b",second}]) : B.Slice}

law unselected_names_remain_explicit:
  for source: String
  {B.partition([B.Decl{"a",["a"],source,False{}}],Nil{}) ==
    B.Slice{S.Sequence{Nil{}},Nil{},["a"]} : B.Slice}

law visited_name_is_not_loaded_again:
  for +depth: Nat
  for parser: Nat
  for +book: List<&2,B.Decl>
  for +items: List<&2,B.Selected>
  {B.visit(1n+depth,parser,["Bool"],book,["Bool"],items) == Done{B.partition(book,items)} : Result<S.Error,B.Slice>}

law pending_work_requires_budget:
  for parser: Nat
  for name: String
  for tail: List<&2,String>
  for book: List<&2,B.Decl>
  for seen: List<&2,String>
  for items: List<&2,B.Selected>
  {B.visit(0n,parser,Con{name,tail},book,seen,items) ==
    Fail{S.Exhausted{"base-slice",S.At{0,0,0,0}}} : Result<S.Error,B.Slice>}

law pinned_syntax_cannot_be_invalid:
  for phase: String
  for +code: String
  for +at: S.At
  {B.base_error(S.Invalid{phase,code,at}) == S.Unsupported{"load",String.append("base-",code),at} : S.Error}

law unsafe_slice_is_unsupported:
  for depth: Nat
  for name: String
  for names: List<&2,String>
  for source: String
  {B.parse(depth,B.Decl{name,names,source,True{}}) ==
    Fail{S.Unsupported{"load","base-unsafe",S.At{0,0,0,0}}} : Result<S.Error,S.Node>}

law empty_base_type_is_unsupported:
  for +at: S.At
  for tree: S.Node
  {B.nonempty(Some{S.Token{"Empty",at}},tree) ==
    Fail{S.Unsupported{"check","base-empty-datatype",at}} : Result<S.Error,S.Node>}

law foreign_slice_is_unsupported:
  for depth: Nat
  {B.parse(depth,B.Decl{"f",["f"],"def f() -> Unit:\n  import \"./f.c\"\n",False{}}) ==
    Fail{S.Unsupported{"check","foreign-definition",S.At{0,0,0,0}}} : Result<S.Error,S.Node>}

# User value mentions: not a scrutinee, a call head, a type or a binder.
law mentions_are_free_values:
  for +at: S.At
  {B.mentions(32n,S.Function{S.Token{"f",at},[S.Parameter{S.Token{"x",at},1,S.Token{"Bool",at}}],S.Token{"Bool",at},
      S.Match{S.Token{"match",at},S.Variable{S.Token{"Bool",at}},[S.Arm{S.Token{"case",at},
        S.Constructor{S.Token{"Box",at},[S.Variable{S.Token{"y",at}}]},
        S.Binding{S.Token{"h",at},0,Some{S.Token{"Bool",at}},S.Variable{S.Token{"Bool.not",at}},
          S.Call{S.Token{"g",at},[S.Variable{S.Token{"x",at}},S.Variable{S.Token{"y",at}},S.Variable{S.Token{"h",at}}]}}}]}},Nil{}) ==
    Done{[S.Token{"Bool.not",at}]} : Result<S.Error,List<&2,S.Token>>}

# A value mention of a Base type or function is Unsupported and selects nothing;
# a constructor name is not a declaration there.
law base_values_are_unsupported:
  for +at: S.At
  {(B.undeclared([S.Token{"Bool",at}],[B.Decl{"Bool",["Bool","False","True"],"type Bool is Data:\n",False{}}]),
    B.undeclared([S.Token{"Bool.not",at}],[B.Decl{"Bool.not",["Bool.not"],"def Bool.not(b: Bool) -> Bool:\n",False{}}]),
    B.undeclared([S.Token{"True",at}],[B.Decl{"Bool",["Bool","False","True"],"type Bool is Data:\n",False{}}]))
   == (Fail{S.Unsupported{"check","type-as-term",at}},Fail{S.Unsupported{"check","function-reference",at}},Done{Unit{}})
   : Result<S.Error,Unit> & Result<S.Error,Unit> & Result<S.Error,Unit>}
