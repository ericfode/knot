import Base
import ./base-load-LAWS.bend as L

def L.empty_inventory(): {==}
def L.constructor_inventory(): {==}
def L.claim_and_fill_share_identity(claim,fill,other): {==}
def L.bound_name_is_not_dependency(at): {==}
def L.free_name_is_dependency(at): {==}
def L.parameter_name_is_not_dependency(at): {==}
def L.term_reference_ignores_constructor(source): {==}
def L.constructor_reference_ignores_term(source): {==}
def L.user_constructor_preserves_base_type(source): {==}
def L.user_type_preserves_base_constructor(source): {==}
def L.user_term_shadows_same_category(source): {==}
def L.declaration_inventory_keeps_category(at): {==}
def L.selection_follows_source_order(first,second,source): {==}
def L.unselected_names_remain_explicit(source): {==}
def L.visited_name_is_not_loaded_again(depth,parser,book,items):
  match depth:
    case 0n: {==}
    case 1n+n: {==}
def L.pending_work_requires_budget(parser,name,tail,book,seen,items): {==}
def L.pinned_syntax_cannot_be_invalid(phase,code,at): {==}
def L.unsafe_slice_is_unsupported(depth,name,names,source): {==}
def L.empty_base_type_is_unsupported(at,tree): {==}
def L.foreign_slice_is_unsupported(depth): {==}
def L.mentions_are_free_values(at): {==}
def L.base_values_are_unsupported(at): {==}
