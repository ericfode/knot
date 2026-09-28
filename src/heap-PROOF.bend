import Base
import ./heap-LAWS.bend as L

def L.size_class_counts_live_slots(kind,first,second): {==}
def L.scalar_slots_occupy_words(): {==}
def L.nullary_cell_includes_prefix_and_tag(): {==}
def L.payload_follows_ownership_prefix(): {==}
def L.last_class_precedes_release_stack(): {==}
def L.first_release_frame_follows_classes(): {==}
def L.last_release_frame_fits_reservation(): {==}
def L.count_word_is_outside_payload(pointer): {==}
def L.retain_adds_one_before_return(pointer,count): {==}
def L.consumed_parent_uses_free_without_child_release(): {==}
def L.last_release_keeps_parent_until_field_scan(pointer,frame): {==}
def L.free_cell_keeps_previous_class_head(pointer,class): {==}
def L.exhausted_cleanup_retains_memory_and_pending(): {==}
def L.stack_bounds_precede_frame_publication(): {==}
def L.scalar_descriptor_never_traces_a_pointer(): {==}
def L.pointer_descriptor_traces_its_exact_slot(): {==}
def L.instruction_budget_is_explicit(chunk,cap): {==}
