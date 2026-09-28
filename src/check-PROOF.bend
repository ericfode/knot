import Base
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
def L.promoted_rebuild_is_fresh(term,type_id,uses):
  {==}
def L.affine_rebuild_keeps_uses(term,type_id,uses):
  {==}
def L.nearest_binding_wins(tail,level):
  {==}
def L.no_checker_budget(node):
  {==}
