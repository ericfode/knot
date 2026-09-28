import Base
import ./fields-PROOF.bend as Fields
import ./runtime-PROOF.bend as Runtime
import ./descent-PROOF.bend as Descent
import ./scope.bend as E
import ./recursion-LAWS.bend as L

def L.local_binding_preserves_descent(bindings,next,open,live,aliases,token,q,type_id,value): {==}
def L.opening_root_records_descent(token,bindings,params,args,aliases): {==}
def L.opening_descendant_records_descent(token,bindings,params,args,aliases): {==}
def L.descending_self_call_is_checked(token,uses): {==}
def L.nondecreasing_self_call_is_invalid(token,uses): {==}
def L.rebuilt_parent_does_not_decrease(token): {==}
def L.later_argument_establishes_descent(token,uses): {==}
def L.earlier_growth_blocks_later_descent(token): {==}
def L.dead_self_call_needs_no_descent(token,type_id,args,uses,bindings,aliases,params): {==}
def L.earlier_call_needs_no_descent(token,type_id,args,uses,scope,params):
  match scope:
    case E.Scope{bindings,next,open,live,aliases}:
      match live:
        case False{}: {==}
        case True{}: {==}
def L.recursive_evaluation_exhaustion(token,index,type_id,args,env,frames,book): {==}
