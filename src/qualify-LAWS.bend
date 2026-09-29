import Base
import ./syntax.bend as S
import ./qualify.bend as Q

# Scope boundaries and concrete public transformations; not a resolution theorem.
law entry_names_are_bare:
  for name: String
  {Q.prefix("",name) == name : String}

law empty_module:
  for namespace: String
  for aliases: List<&2,Q.Alias>
  for terms: List<&2,String>
  for constructors: List<&2,String>
  {Q.qualify(namespace,aliases,Q.Symbols{terms,constructors},S.Sequence{Nil{}}) == Done{S.Sequence{Nil{}}} : Result<S.Error,S.Node>}

law datatype_keeps_constructor_order:
  for +at: S.At
  {Q.qualify("lib/flag",Nil{},Q.Symbols{Nil{},Nil{}},S.Sequence{[
    S.Datatype{S.Token{"Flag",at},False{},[
      S.Constructor{S.Token{"Off",at},Nil{}},S.Constructor{S.Token{"On",at},Nil{}}]}]}) ==
    Done{S.Sequence{[
      S.Datatype{S.Token{"lib/flag.Flag",at},False{},[
        S.Constructor{S.Token{"lib/flag.Off",at},Nil{}},S.Constructor{S.Token{"lib/flag.On",at},Nil{}}]}]}}
    : Result<S.Error,S.Node>}

law parameter_shadows_global:
  for +at: S.At
  {Q.qualify("lib/m",Nil{},Q.Symbols{["Bool"],Nil{}},S.Sequence{[
    S.Function{S.Token{"keep",at},[S.Parameter{S.Token{"Bool",at},1,S.Token{"Bool",at}}],
      S.Token{"Bool",at},S.Variable{S.Token{"Bool",at}}}]}) ==
    Done{S.Sequence{[
      S.Function{S.Token{"lib/m.keep",at},[S.Parameter{S.Token{"Bool",at},1,S.Token{"Bool",at}}],
        S.Token{"Bool",at},S.Variable{S.Token{"Bool",at}}}]}}
    : Result<S.Error,S.Node>}

law initializer_has_outer_scope:
  for +at: S.At
  {Q.walk(16n,S.Binding{S.Token{"x",at},1,None{},S.Variable{S.Token{"x",at}},S.Variable{S.Token{"x",at}}},
    Q.Expression{},Q.Names{"lib/m",Nil{},Nil{},["lib/m.x"]},Nil{}) ==
    Done{Q.Qualified{S.Binding{S.Token{"x",at},1,None{},S.Variable{S.Token{"lib/m.x",at}},S.Variable{S.Token{"x",at}}},Nil{}}}
    : Result<S.Error,Q.Qualified>}

law arm_binder_has_local_scope:
  for +at: S.At
  {Q.walk(16n,S.Arm{S.Token{"case",at},S.Constructor{S.Token{"Box",at},[S.Variable{S.Token{"x",at}}]},
    S.Variable{S.Token{"x",at}}},Q.Expression{},Q.Names{"lib/m",Nil{},Nil{},["lib/m.Box"]},Nil{}) ==
    Done{Q.Qualified{S.Arm{S.Token{"case",at},S.Constructor{S.Token{"lib/m.Box",at},[S.Variable{S.Token{"x",at}}]},
      S.Variable{S.Token{"x",at}}},Nil{}}}
    : Result<S.Error,Q.Qualified>}

law alias_expands_one_component:
  for +at: S.At
  {Q.qualify("",[Q.Alias{"L","lib/left"}],Q.Symbols{["lib/flag.Flag","lib/left.left"],Nil{}},S.Sequence{[
    S.Function{S.Token{"keep",at},[S.Parameter{S.Token{"x",at},1,S.Token{"L.F.Flag",at}}],
      S.Token{"L.F.Flag",at},S.Variable{S.Token{"x",at}}}]}) ==
    Done{S.Sequence{[
      S.Function{S.Token{"keep",at},[S.Parameter{S.Token{"x",at},1,S.Token{"lib/left.F.Flag",at}}],
        S.Token{"lib/left.F.Flag",at},S.Variable{S.Token{"x",at}}}]}}
    : Result<S.Error,S.Node>}

law alias_member_cannot_be_declared:
  for +at: S.At
  for body: S.Node
  {Q.qualify("m",[Q.Alias{"A","lib/a"}],Q.Symbols{Nil{},Nil{}},S.Sequence{[
    S.Function{S.Token{"A.keep",at},Nil{},S.Token{"Flag",at},body}]}) ==
    Fail{S.Invalid{"load","alias-member",at}} : Result<S.Error,S.Node>}

law loaded_global_cannot_be_declared:
  for +at: S.At
  for constructors: List<&2,S.Node>
  {Q.qualify("m",Nil{},Q.Symbols{["Bool"],Nil{}},S.Sequence{[S.Datatype{S.Token{"Bool",at},False{},constructors}]}) ==
    Fail{S.Invalid{"load","duplicate-global",at}} : Result<S.Error,S.Node>}

law global_constructor_allows_local_type:
  for +at: S.At
  {Q.qualify("m",Nil{},Q.Symbols{["Maybe"],["Some"]},S.Sequence{[
    S.Datatype{S.Token{"Some",at},False{},[S.Constructor{S.Token{"UniqueProbe",at},Nil{}}]}]}) ==
    Done{S.Sequence{[S.Datatype{S.Token{"m.Some",at},False{},[S.Constructor{S.Token{"m.UniqueProbe",at},Nil{}}]}]}}
    : Result<S.Error,S.Node>}

law global_type_allows_local_constructor:
  for +at: S.At
  {Q.qualify("m",Nil{},Q.Symbols{["Bool"],["True","False"]},S.Sequence{[
    S.Datatype{S.Token{"Mark",at},False{},[S.Constructor{S.Token{"Bool",at},Nil{}}]}]}) ==
    Done{S.Sequence{[S.Datatype{S.Token{"m.Mark",at},False{},[S.Constructor{S.Token{"m.Bool",at},Nil{}}]}]}}
    : Result<S.Error,S.Node>}

law later_type_keeps_earlier_resolution:
  for +at: S.At
  {Q.qualify("future",Nil{},Q.Symbols{["Maybe"],["Some"]},S.Sequence{[
    S.Function{S.Token{"early",at},Nil{},S.Token{"Some",at},S.Constructor{S.Token{"UniqueProbe",at},Nil{}}},
    S.Datatype{S.Token{"Some",at},False{},[S.Constructor{S.Token{"UniqueProbe",at},Nil{}}]}]}) ==
    Done{S.Sequence{[
      S.Function{S.Token{"future.early",at},Nil{},S.Token{"Some",at},S.Constructor{S.Token{"future.UniqueProbe",at},Nil{}}},
      S.Datatype{S.Token{"future.Some",at},False{},[S.Constructor{S.Token{"future.UniqueProbe",at},Nil{}}]}]}}
    : Result<S.Error,S.Node>}

law base_name_is_fallback:
  for +at: S.At
  {Q.reference(S.Token{"Bool.not",at},Q.Names{"lib/m",Nil{},["Bool.not"],Nil{}}) ==
    Done{S.Token{"Bool.not",at}} : Result<S.Error,S.Token>}

law alias_ambiguity_is_invalid:
  for +at: S.At
  {Q.reference(S.Token{"F.flip",at},Q.Names{"m",[Q.Alias{"F","lib/flag"}],
    ["lib/flag.flip","F.flip"],Nil{}}) == Fail{S.Invalid{"load","ambiguous-alias",at}} : Result<S.Error,S.Token>}

law inventory_keeps_unused_functions:
  for +at: S.At
  for first: S.Node
  for second: S.Node
  {Q.declaration_names(S.Sequence{[
    S.Datatype{S.Token{"m.Flag",at},False{},[S.Constructor{S.Token{"m.Off",at},Nil{}},S.Constructor{S.Token{"m.On",at},Nil{}}]},
    S.Function{S.Token{"m.first",at},Nil{},S.Token{"m.Flag",at},first},
    S.Function{S.Token{"m.second",at},Nil{},S.Token{"m.Flag",at},second}]}) ==
    ["m.Flag","m.Off","m.On","m.first","m.second"] : List<&2,String>}

law inventory_separates_namespaces:
  for +at: S.At
  {(Q.term_names(S.Sequence{[S.Datatype{S.Token{"Unit",at},False{},[S.Constructor{S.Token{"Unit",at},Nil{}}]}]}),
    Q.ctor_names(S.Sequence{[S.Datatype{S.Token{"Unit",at},False{},[S.Constructor{S.Token{"Unit",at},Nil{}}]}]})) ==
    (["Unit"],["Unit"]) : List<&2,String> & List<&2,String>}

law exhaustion_is_separate:
  for node: S.Node
  for position: Q.Position
  for names: Q.Names
  for bound: List<&2,String>
  {Q.walk(0n,node,position,names,bound) == Fail{S.Exhausted{"load",S.At{0,0,0,0}}} : Result<S.Error,Q.Qualified>}

law qualified_global_cannot_be_declared:
  for +at: S.At
  {Q.fresh(S.Token{"not",at},"Bool",Nil{},["Bool.not"]) ==
    Fail{S.Invalid{"load","duplicate-global",at}} : Result<S.Error,String>}

law qualified_constructor_cannot_be_declared:
  for +at: S.At
  {Q.qualify("m",Nil{},Q.Symbols{Nil{},["m.Off"]},S.Sequence{[
    S.Datatype{S.Token{"Flag",at},False{},[S.Constructor{S.Token{"Off",at},Nil{}}]}]}) ==
    Fail{S.Invalid{"load","duplicate-global",at}} : Result<S.Error,S.Node>}

law local_constructor_is_not_a_pattern_binder:
  for +at: S.At
  {Q.walk_in(1n,S.Variable{S.Token{"Off",at}},Q.Pattern{},
    Q.Names{"m",Nil{},Nil{},["m.Off"]},Nil{},["m.Off"]) ==
    Fail{S.Invalid{"check","constructor-pattern-binder",at}} : Result<S.Error,Q.Qualified>}

law global_constructor_is_not_a_pattern_binder:
  for +at: S.At
  {Q.walk_in(1n,S.Variable{S.Token{"True",at}},Q.Pattern{},
    Q.Names{"m",Nil{},["True"],Nil{}},Nil{},["True"]) ==
    Fail{S.Invalid{"check","constructor-pattern-binder",at}} : Result<S.Error,Q.Qualified>}

law term_name_can_be_a_pattern_binder:
  for +at: S.At
  {Q.walk_in(1n,S.Variable{S.Token{"Bool",at}},Q.Pattern{},
    Q.Names{"m",Nil{},["Bool"],Nil{}},Nil{},["False","True"]) ==
    Done{Q.Qualified{S.Variable{S.Token{"Bool",at}},["Bool"]}} : Result<S.Error,Q.Qualified>}

law promoted_constructor_is_not_a_pattern_binder:
  for +at: S.At
  {Q.walk_in(1n,S.Promotion{S.Token{"Off",at}},Q.Pattern{},
    Q.Names{"m",Nil{},Nil{},["m.Off"]},Nil{},["m.Off"]) ==
    Fail{S.Invalid{"check","constructor-pattern-binder",at}} : Result<S.Error,Q.Qualified>}

law constructor_is_not_a_let_binder:
  for +at: S.At
  {Q.walk_in(3n,S.Binding{S.Token{"True",at},1,None{},S.Variable{S.Token{"v",at}},S.Variable{S.Token{"v",at}}},Q.Expression{},
    Q.Names{"m",Nil{},["True"],Nil{}},["v"],["True"]) ==
    Fail{S.Invalid{"check","constructor-pattern-binder",at}} : Result<S.Error,Q.Qualified>}

law later_constructor_can_be_a_let_binder:
  for +at: S.At
  {Q.walk_in(3n,S.Binding{S.Token{"Late",at},1,None{},S.Variable{S.Token{"v",at}},S.Variable{S.Token{"v",at}}},Q.Expression{},
    Q.Names{"m",Nil{},Nil{},Nil{}},["v"],["m.Late"]) ==
    Done{Q.Qualified{S.Binding{S.Token{"Late",at},1,None{},S.Variable{S.Token{"v",at}},S.Variable{S.Token{"v",at}}},Nil{}}}
    : Result<S.Error,Q.Qualified>}
