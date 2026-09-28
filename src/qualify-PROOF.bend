import Base
import ./qualify-LAWS.bend as L

def L.entry_names_are_bare(name): {==}
def L.empty_module(namespace,aliases,terms,constructors): {==}
def L.datatype_keeps_constructor_order(at): {==}
def L.parameter_shadows_global(at): {==}
def L.initializer_has_outer_scope(at): {==}
def L.arm_binder_has_local_scope(at): {==}
def L.alias_expands_one_component(at): {==}
def L.alias_member_cannot_be_declared(at,body): {==}
def L.loaded_global_cannot_be_declared(at,constructors): {==}
def L.global_constructor_allows_local_type(at): {==}
def L.global_type_allows_local_constructor(at): {==}
def L.later_type_keeps_earlier_resolution(at): {==}
def L.base_name_is_fallback(at): {==}
def L.alias_ambiguity_is_invalid(at): {==}
def L.inventory_keeps_unused_functions(at,first,second): {==}
def L.inventory_separates_namespaces(at): {==}
def L.exhaustion_is_separate(node,position,names,bound): {==}

def L.qualified_global_cannot_be_declared(at): {==}
def L.qualified_constructor_cannot_be_declared(at): {==}
def L.local_constructor_is_not_a_pattern_binder(at): {==}
def L.global_constructor_is_not_a_pattern_binder(at): {==}
def L.term_name_can_be_a_pattern_binder(at): {==}
def L.promoted_constructor_is_not_a_pattern_binder(at): {==}
def L.later_constructor_leaves_a_binder(at): {==}
def L.let_binder_cannot_rebind_a_constructor(at,value,body): {==}
def L.file_binders_meet_only_earlier_constructors(at,value,body): {==}
