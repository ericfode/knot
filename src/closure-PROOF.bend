import Base
import ./core.bend as C
import ./closure.bend as F
import ./closure-LAWS.bend as L

def L.capture_arity(captures,rename):
  match captures:
    case Nil{}: {==}
    case Con{C.Binding{token,id,q,typ,param,known},+tail}:
      Equal.cong(Nat,Nat,x => 1n+x,List.length(&2,C.Term,F.capture_args(tail,rename)),List.length(&2,C.Binding,tail),L.capture_arity(tail,rename))

def L.capture_quantity(token,level,quantity,typ,parameter,known,tail): {==}
def L.close_has_one_cell(token,tag,typ,captures,rename): {==}
def L.invoke_has_one_dispatch(token,index,result,function,argument): {==}
def L.outer_levels_are_unchanged(id): {==}
def L.rewrite_exhaustion(term,rename,table): {==}
