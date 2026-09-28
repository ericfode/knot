import Base
import ./descent-LAWS.bend as L

def L.equality_is_product_identity(order):
  match order:
    case LT{}: {==}
    case EQ{}: {==}
    case GT{}: {==}
def L.growth_blocks_product(order):
  match order:
    case LT{}: {==}
    case EQ{}: {==}
    case GT{}: {==}
def L.equality_is_not_smaller(): {==}
def L.same_variable_is_equal(): {==}
def L.unrelated_variable_is_greater(): {==}
def L.field_is_strictly_smaller(): {==}
def L.rebuilt_parent_is_equal(): {==}
def L.rebuilt_smaller_constructor_decreases(): {==}
def L.product_decreases_in_second_field(): {==}
def L.product_growth_blocks_earlier_shrink(): {==}
def L.same_head_subterm_survives_failed_alignment(): {==}
def L.constructor_identity_includes_type(): {==}
def L.opaque_argument_cannot_decrease(): {==}
def L.failed_alignment_skips_its_field(index): {==}
def L.erased_column_is_skipped(token,type_id,params,arg,args,index,fuel,bindings,aliases): {==}
def L.empty_columns_are_equal(index,fuel,bindings,aliases): {==}
def L.alias_follows_initializer(token): {==}
def L.computed_alias_stays_opaque(token,args): {==}
def L.comparison_exhaustion_is_not_rejection(arg,col): {==}
def L.inspection_exhaustion_is_not_rejection(term,bindings,aliases): {==}
