import Base
import ../../src/fields-PROOF.bend as Earlier
import ./LAWS.bend as L

def L.enum_capability_preserved(types): {==}
def L.fields_capability_follows_checking(types): {==}
def L.erased_constructor_still_has_a_cell(token,name,type_id,rest): {==}
def L.erased_argument_takes_no_slot(n,head,tail,token,type_id,params,slots,tag,heap,functions,locals,next,cap): {==}
def L.erased_pattern_keeps_offset_and_locals(n,token,level,type_id,parameter,known,tail,pointer,offset,body,heap,functions,locals,next,cap): {==}
