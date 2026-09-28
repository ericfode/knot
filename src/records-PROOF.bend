import Base
import ./records-LAWS.bend as L

def L.reusable_occurrence_acquires_an_edge(source,destination): {==}
def L.affine_occurrence_transfers_an_edge(source,destination): {==}
def L.dropped_binding_enters_cleanup(source): {==}
def L.completion_carries_issued_attempt(join,slot,source): {==}
def L.logical_slots_survive_reverse_delivery(token,typ,join,first,flow): {==}
def L.erased_argument_has_no_slot(token,typ,params,join,slot,source,flow): {==}
def L.erased_parameter_has_no_owner(token,typ,params,types,level,first,flow): {==}
def L.tail_arguments_keep_source_order(token,typ,source,destination,flow): {==}
def L.relocation_preserves_the_test(source,tag,yes,no): {==}
def L.return_cleans_before_delivery(join,destination,source,flow): {==}
def L.full_activation_cannot_wrap(locals,plan,next): {==}
def L.pending_compilation_needs_fuel(mode,types,functions,act,flow): {==}
def L.affine_binding_moves_even_data(token,constructors,level,capture,locals,next,plan): {==}
