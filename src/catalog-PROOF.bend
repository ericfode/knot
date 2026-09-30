import Base
import ./runtime-PROOF.bend as Earlier
import ./catalog-LAWS.bend as L

def L.erased_field_has_no_kind_obligation(data,child):
  match data child:
    case False{} False{}: {==}
    case False{} True{}: {==}
    case True{} False{}: {==}
    case True{} True{}: {==}

def L.data_live_field_requires_data():
  {==}

def L.reusable_field_requires_data(data):
  match data:
    case False{}: {==}
    case True{}: {==}

def L.data_field_preserves_metadata(token,index,data,name,ctors):
  match data:
    case False{}: {==}
    case True{}: {==}

def L.field_capability_is_not_acceptance(token,head,tail,rest):
  {==}

def L.type_positions_read_their_scope(at,here,ctors,body):
  {==}
def L.empty_datatype(name,data):
  {==}

def L.promoted_datatype_is_rejected(): {==}

def L.bare_datatype_name_binds(): {==}

def L.later_datatype_is_no_datatype(): {==}

def L.hidden_type_is_rejected(): {==}

def L.unrelated_binder_hides_nothing(): {==}
