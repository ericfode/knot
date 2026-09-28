import Base
import ./ownership-LAWS.bend as L

def L.affine_occurrence_moves(future,level): {==}
def L.reusable_last_occurrence_moves(level): {==}
def L.reusable_surviving_occurrence_shares(): {==}
def L.erased_field_has_no_edge(token,type_id,rest,types): {==}
def L.erased_parameter_has_no_local(token,type_id): {==}
def L.live_local_preserves_level(token,type_id): {==}
def L.empty_continuation_has_no_holders(index,quantity,type_id): {==}
def L.surviving_continuation_keeps_holder(index,quantity,type_id): {==}
def L.erased_initializer_has_no_use(token,type_id): {==}
def L.branch_field_is_not_an_incoming_holder(token,type_id): {==}
def L.wide_tail_uses_ordinary_call(index): {==}
def L.narrow_tail_keeps_return_call(index): {==}
def L.ordinary_call_keeps_its_target(index): {==}
