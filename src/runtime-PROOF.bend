import Base
import ./check-PROOF.bend as Front
import ./runtime-LAWS.bend as L

def L.returned_value_needs_no_fuel(value,book): {==}
def L.pending_evaluation_needs_fuel(term,environment,frames,book): {==}
def L.erased_initializer_is_not_evaluated(token,level,type_id,initial,body,environment,frames,book): {==}
def L.bind_keeps_caller_scope(level,value,body,environment,frames,book): {==}
def L.unsigned_leb_boundary(): {==}
def L.signed_leb_boundary(): {==}
def L.unsigned_leb_maximum(): {==}
