import Base
import ./fields-PROOF.bend as Fields
import ./runtime-PROOF.bend as Runtime
import ./scope.bend as E
import ./recursion-LAWS.bend as L

def L.root_fields_are_smaller(fields,smaller): {==}
def L.descendant_fields_are_smaller(fields): {==}
def L.unrelated_fields_stay_unmarked(fields): {==}
def L.marked_reference_descends(token,type_id,tail): {==}
def L.root_reference_does_not_descend(token,type_id,tail): {==}
def L.rebuilt_argument_does_not_descend(token,type_id,tag,params,args,smaller): {==}
def L.computed_argument_does_not_descend(token,index,type_id,args,smaller): {==}
def L.empty_call_does_not_descend(smaller): {==}
def L.later_argument_cannot_establish_descent(token,type_id): {==}
def L.local_binding_preserves_descent(bindings,next,open,live,smaller,token,q,type_id): {==}
def L.opening_root_records_descent(token,bindings,params,args): {==}
def L.opening_descendant_records_descent(token,bindings,params,args): {==}
def L.descending_self_call_is_checked(token,type_id,uses,bindings): {==}
def L.nondecreasing_self_call_is_unsupported(token,type_id,uses,bindings,live): {==}
def L.earlier_call_needs_no_descent(token,type_id,args,uses,scope):
  match scope:
    case E.Scope{bindings,next,open,live,smaller}: {==}
def L.recursive_evaluation_exhaustion(token,index,type_id,args,env,frames,book): {==}
