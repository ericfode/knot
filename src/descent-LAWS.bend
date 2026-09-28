import Base
import ./syntax.bend as S
import ./core.bend as C
import ./descent.bend as D

# Algebraic helper laws and inhabited comparison witnesses, not termination.
law equality_is_product_identity:
  for +order: Cmp
  {D.join(EQ{},order) == order : Cmp}

law growth_blocks_product:
  for order: Cmp
  {D.join(order,GT{}) == GT{} : Cmp}

law equality_is_not_smaller:
  {D.smaller(EQ{}) == False{} : Bool}

law same_variable_is_equal:
  {D.compare(8n,D.Variable{0},D.Variable{0}) == Done{EQ{}} : Result<S.Error,Cmp>}

law unrelated_variable_is_greater:
  {D.compare(8n,D.Variable{1},D.Variable{0}) == Done{GT{}} : Result<S.Error,Cmp>}

law field_is_strictly_smaller:
  {D.compare(8n,D.Variable{1},D.Constructor{0,1,[D.Variable{1}]}) == Done{LT{}} : Result<S.Error,Cmp>}

law rebuilt_parent_is_equal:
  {D.compare(16n,D.Constructor{0,1,[D.Variable{1}]},D.Constructor{0,1,[D.Variable{1}]}) == Done{EQ{}} : Result<S.Error,Cmp>}

law rebuilt_smaller_constructor_decreases:
  {D.compare(24n,D.Constructor{0,1,[D.Variable{1}]},D.Constructor{0,1,[D.Constructor{0,1,[D.Variable{1}]}]}) == Done{LT{}} : Result<S.Error,Cmp>}

law product_decreases_in_second_field:
  {D.compare(24n,D.Constructor{0,0,[D.Variable{1},D.Variable{2}]},
    D.Constructor{0,0,[D.Variable{1},D.Constructor{0,1,[D.Variable{2}]}]}) == Done{LT{}} : Result<S.Error,Cmp>}

law product_growth_blocks_earlier_shrink:
  {D.compare(32n,D.Constructor{0,0,[D.Variable{1},D.Constructor{0,1,[D.Variable{2}]}]},
    D.Constructor{0,0,[D.Constructor{0,1,[D.Variable{1}]},D.Variable{2}]}) == Done{GT{}} : Result<S.Error,Cmp>}

law same_head_subterm_survives_failed_alignment:
  {D.compare(32n,D.Constructor{0,1,[D.Variable{1},D.Variable{2}]},
    D.Constructor{0,1,[D.Constructor{0,1,[D.Variable{1},D.Variable{2}]},D.Variable{3}]}) == Done{LT{}} : Result<S.Error,Cmp>}

law constructor_identity_includes_type:
  {D.compare(8n,D.Constructor{0,0,Nil{}},D.Constructor{1,0,Nil{}}) == Done{GT{}} : Result<S.Error,Cmp>}

law opaque_argument_cannot_decrease:
  {D.compare(8n,D.Opaque{},D.Constructor{0,1,[D.Variable{1}]}) == Done{GT{}} : Result<S.Error,Cmp>}

law failed_alignment_skips_its_field:
  for +index: U32
  {D.fallback(D.Product{GT{},Some{index}},at => Done{D.Product{EQ{},Some{at}}}) ==
    Done{D.Product{EQ{},Some{index}}} : Result<S.Error,D.Product>}

law erased_column_is_skipped:
  for token: S.Token
  for type_id: U32
  for +params: List<&2,C.Parameter>
  for arg: C.Term
  for +args: List<&2,C.Term>
  for +index: U32
  for +fuel: Nat
  for +bindings: List<&2,C.Binding>
  for +aliases: List<&2,D.Alias>
  {D.columns(Con{C.Parameter{token,0,type_id},params},Con{arg,args},index,fuel,bindings,aliases) ==
    D.columns(params,args,U32.add(index,1),fuel,bindings,aliases) : Result<S.Error,Cmp>}

law empty_columns_are_equal:
  for index: U32
  for fuel: Nat
  for bindings: List<&2,C.Binding>
  for aliases: List<&2,D.Alias>
  {D.columns(Nil{},Nil{},index,fuel,bindings,aliases) == Done{EQ{}} : Result<S.Error,Cmp>}

law alias_follows_initializer:
  for +token: S.Token
  {D.shape(8n,C.Reference{token,2,0},Nil{},[D.Alias{2,C.Reference{token,1,0}}]) ==
    Done{D.Variable{1}} : Result<S.Error,D.Shape>}

law computed_alias_stays_opaque:
  for +token: S.Token
  for args: List<&2,C.Term>
  {D.shape(8n,C.Reference{token,2,0},Nil{},[D.Alias{2,C.Application{token,0,0,args}}]) ==
    Done{D.Opaque{}} : Result<S.Error,D.Shape>}

law comparison_exhaustion_is_not_rejection:
  for arg: D.Shape
  for col: D.Shape
  {D.compare(0n,arg,col) == Fail{S.Exhausted{"check",S.At{0,0,0,0}}} : Result<S.Error,Cmp>}

law inspection_exhaustion_is_not_rejection:
  for term: C.Term
  for bindings: List<&2,C.Binding>
  for aliases: List<&2,D.Alias>
  {D.shape(0n,term,bindings,aliases) == Fail{S.Exhausted{"check",S.At{0,0,0,0}}} : Result<S.Error,D.Shape>}
