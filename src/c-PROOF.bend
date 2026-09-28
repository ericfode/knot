import Base
import ./c-LAWS.bend as L

def L.erased_constructor_has_a_cell(token,name,type_id,rest): {==}
def L.saved_calls_keep_their_continuation(name,context,index): {==}
def L.erased_argument_has_no_code_or_slot(n,head,tail,token,type_id,params,slots,action,context,locals,next,cap): {==}
def L.erased_binding_has_no_initializer(n,token,level,type_id,value,body,destination,context,locals,next,cap): {==}
def L.erased_pattern_preserves_offset(n,token,level,type_id,parameter,known,tail,pointer,offset,body,destination,context,locals,next,cap): {==}
def L.erased_parameter_preserves_saved_arguments(token,type_id,tail,slots,level): {==}
def L.two_parameters_rebind_before_loop(token,type_id): {==}
def L.zero_depth_is_exhausted(mode,context,locals,next,cap): {==}
