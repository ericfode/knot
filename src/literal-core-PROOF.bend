import Base
import ./literal-core-LAWS.bend as L
import ./syntax.bend as S
import ./core.bend as C
import ./eval.bend as E

def L.natural_literal(token,id,env,frames): {==}
def L.natural_cell(id,value,frames): {==}
def L.natural_offset(id,token,field,tail,value): {==}
def L.offset_cells(k,id,tag,token,field,term,env,v,c,ev,m,frames):
  match k:
    case 0n: ev(frames,m)
    case 1n+p:
      %L.offset_cells(p,id,tag,token,field,term,env,v,c,ev,2n+m,Con{E.Field{id,tag,Nil{},Nil{},env,Nil{}},frames}) :
        {E.run(m,E.Return{E.Object{id,tag,[L.cells(p,id,tag,v)]},frames},C.Book{Nil{},Nil{}}) == _ : Result<S.Error,E.Value>}
      {==}
def L.intrinsic_arguments(token,id,args,env,frames): {==}
def L.default_selection(body,tail,tag): {==}
def L.default_scope(value,body,env,frames):
  match value:
    case E.Value{typ,tag}: {==}
    case E.Object{typ,tag,fields}: {==}
def L.text_cell(id,char_id,code,tail,value,frames): {==}
def L.primitive_fields_display_as_literals(): {==}
