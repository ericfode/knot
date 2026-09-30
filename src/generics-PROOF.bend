import Base
import ./syntax.bend as S
import ./core.bend as C
import ./types.bend as T
import ./generics.bend as G
import ./generics-LAWS.bend as L

def L.reconstructed_needs_type(name,level,q,typ,param,term,token,env,next):
  {==}

def L.unrefined_inference(name,level,q,typ,param,token,env,next):
  {==}

def L.annotated_occurrence(binding,token,wanted,env,next):
  match binding:
    case G.Binding{name,level,q,typ,param,Some{term}}: {==}
    case G.Binding{name,level,q,typ,param,None{}}: {==}
