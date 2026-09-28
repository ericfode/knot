import Base
import ./model-LAWS.bend as L

def L.allocator_installs_one_owner(value): {==}
def L.allocator_round_trip_keeps_reusable_cell(value): {==}
def L.allocator_reuses_exact_size_class(before,after): {==}
def L.wrong_size_class_preserves_rejected_pool(value,incoming): {==}
def L.full_allocator_preserves_live_owner(value,incoming): {==}
def L.allocator_release_preserves_unrelated_owner(first,second): {==}
def L.duplicate_release_preserves_free_chain(value): {==}
def L.counted_allocation_starts_with_one_obligation(tag): {==}
def L.first_release_preserves_shared_data(tag): {==}
def L.final_release_reclaims_data(tag): {==}
def L.shared_open_counts_both_repeated_edges(tag): {==}
def L.shared_open_overflow_preserves_all_obligations(tag): {==}
def L.zero_budget_keeps_release_obligation(tag): {==}
