import Base
import ./recursion-PROOF.bend as Recursion
import ./opt-LAWS.bend as L

def L.matching_arm_is_selected(fields,body,other,rest): {==}
def L.value_case_returns_matching_body(token,typ,body,other): {==}
def L.fields_bind_in_declaration_order(token,a,b,body): {==}
def L.empty_field_binding_is_identity(body): {==}
def L.zero_parameter_binding_is_identity(body,base): {==}
def L.arguments_bind_once_in_order(token,a,b,body): {==}
def L.reference_translation(token,level,typ,offset): {==}
def L.dead_reusable_value_is_removed(token,typ,value): {==}
def L.used_reusable_binding_is_retained(token,typ,value): {==}
def L.export_reconstruction_preserves_signature(signature,body,rest): {==}
def L.empty_pipeline_is_identity(depth,book): {==}
def L.zero_pipeline_fuel_is_exhausted(depth,book): {==}
def L.last_verified_round_stops(same): {==}
def L.enum_literal_is_propagated(token): {==}
def L.boxed_literal_is_retained(token,empty,successor): {==}
def L.dropped_export_is_rejected(depth,types,signature,body): {==}
