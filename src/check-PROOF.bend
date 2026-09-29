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
def L.refined_value_needs_annotation(token,uses,type_id,tag):
  {==}
def L.refined_construct_needs_annotation(token,fields,args,uses,type_id,tag):
  {==}
def L.unrefined_binder_is_inferable(token,uses,level,type_id):
  {==}
def L.annotation_admits_constructor(token,tag):
  {==}
def L.nearest_binding_wins(tail,level):
  {==}
def L.no_checker_budget(node):
  {==}
def L.weight_counts_every_node(token):
  {==}
def L.weight_stops_when_spent(token):
  {==}
