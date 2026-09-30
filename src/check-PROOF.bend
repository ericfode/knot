import Base
import ./core.bend as C
import ./PROOF.bend as Front
import ./check-LAWS.bend as L

def L.empty_sequence_preserves_uses(uses,token):
  {==}
def L.repeated_affine_level(token):
  {==}
def L.live_erased_occurrence(token,level,type_id):
  {==}
def L.erased_occurrence_preserves_identity(token,level,type_id):
  {==}
def L.refined_constructor_is_fresh(token,type_id,tag):
  {==}
def L.refined_variable_requires_annotation(name,level,q,type_id,param,known,token,scope,next):
  match known:
    case C.Value{origin,typ,tag}: {==}
    case C.Construct{origin,typ,tag,fields,args}: {==}
    case C.Reference{origin,id,typ}: {==}
    case C.Application{origin,id,typ,args}: {==}
    case C.Let{origin,id,quantity,typ,value,body}: {==}
    case C.Case{origin,id,typ,arms}: {==}
    case C.Branch{tag,fields,body}: {==}
    case C.Sequence{items}: {==}
def L.nearest_binding_wins(tail,level):
  {==}
def L.no_checker_budget(node):
  {==}
