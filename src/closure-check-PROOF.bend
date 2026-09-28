import Base
import ./closure-check-LAWS.bend as L

def L.discard_is_not_a_reference(at,bindings,level,open,live,smaller): {==}
def L.closure_application_is_a_computed_scrutinee(token,function,args,scope): {==}
def L.lambda_is_a_computed_scrutinee(token,quantity,body,scope): {==}
def L.affine_capture_is_transferred(token,typ,domain,site,sigs): {==}
def L.affine_capture_cannot_be_consumed_twice(token,function,argument,arrow,domain,result): {==}
def L.erased_argument_has_no_live_read(token,typ,sigs): {==}
def L.erased_read_has_no_live_capture(token,typ,q,parameter,known): {==}
def L.close_starts_with_an_empty_environment(token,site,typ,level,q,domain,captures,body,caller,frames,book): {==}
def L.erased_capture_skips_lookup(site,typ,level,token,id,domain,parameter,known,tail,body,caller,env,frames,book): {==}
def L.apply_evaluates_the_function_first(token,arrow,typ,function,argument,caller,frames,book): {==}
def L.apply_closure_retains_its_environment(site,typ,level,body,env,argument,caller,frames): {==}
def L.apply_enters_the_body_without_a_return_frame(value,level,body,env,frames,book): {==}
