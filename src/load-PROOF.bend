import Base
import ./load-LAWS.bend as L

def L.completed_module_is_not_read_again(tail,tree,symbols,base,loaded,bundle,characters,depth):
  {==}

def L.active_module_is_a_cycle(done,active,tree,symbols,base,loaded,tail):
  {==}

def L.source_failure_is_preserved(error,path,namespace,characters,tail,state):
  {==}

def L.raw_input_is_bounded_before_header_removal(path,namespace,tail,state):
  {==}

def L.budget_counts_utf8_bytes():
  {==}

def L.multibyte_source_is_bounded_by_bytes(path,namespace,tail,state):
  {==}

def L.empty_namespace_is_entry_relative():
  {==}

def L.nested_namespace_is_importer_relative():
  {==}

def L.parent_paths_have_one_identity():
  {==}

def L.hash_paths_use_the_bundle():
  {==}

def L.package_relative_paths_keep_identity():
  {==}

def L.bundle_identity_is_independent_of_import_spelling():
  {==}

def L.absolute_import_is_unsupported():
  {==}

def L.mixed_path_roots_are_unsupported():
  {==}

def L.climbing_paths_have_no_identity():
  {==}

def L.working_directory_bundle_contains_local_paths():
  {==}

def L.package_escape_is_invalid():
  {==}

def L.namespace_is_lexically_canonical():
  {==}

def L.glued_hash_stays_in_the_path():
  {==}

def L.glued_hash_ends_an_alias():
  {==}

def L.header_separator_outside_ascii_is_unsupported():
  {==}

def L.duplicate_alias_is_invalid():
  {==}

def L.parent_import_is_recognized_without_loading(at,rest):
  {==}

def L.base_term_collision_is_invalid(): {==}
def L.base_constructor_collision_is_invalid(): {==}
def L.column_zero_foreign_body_is_unsupported(): {==}
def L.module_import_after_declaration_is_invalid(): {==}
def L.quoted_body_leaves_imports_to_the_lexer(): {==}
def L.ambiguous_host_path_is_unsupported(): {==}
def L.canonical_host_path_can_load(): {==}
def L.path_query_failure_is_a_host_failure(message): {==}
