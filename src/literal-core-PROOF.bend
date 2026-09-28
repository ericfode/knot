import Base
import ./literal-core-LAWS.bend as L
import ./eval.bend as E

def L.natural_literal(token,id,env,frames): {==}
def L.natural_cell(id,value,frames): {==}
def L.natural_offset(id,token,field,tail,value): {==}
def L.intrinsic_arguments(token,id,args,env,frames): {==}
def L.default_selection(body,tail,tag): {==}
def L.default_scope(value,body,env,frames):
  match value:
    case E.Value{typ,tag}: {==}
    case E.Object{typ,tag,fields}: {==}
def L.text_cell(id,char_id,code,tail,value,frames): {==}
def L.primitive_fields_display_as_literals(): {==}
