import Base
import ./LAWS.bend as L

def L.rejected_transaction_preserves_state(heap,error): {==}
def L.successful_transaction_publishes_state(before,after): {==}
def L.type_is_not_shareable(id,tag): {==}
def L.count_ceiling_preserves_state(tag): {==}
def L.copied_leaf_has_distinct_owner(tag): {==}
def L.counted_leaf_retains_one_record(tag): {==}
def L.empty_capacity_rejects_allocation(policy,tag): {==}
def L.copied_allocation_installs_owner(tag): {==}
def L.counted_allocation_starts_at_one(tag): {==}
def L.copied_release_keeps_other_value(tag): {==}
def L.shared_open_acquires_children(tag): {==}
def L.zero_budget_retains_obligation(policy,tag): {==}
def L.reader_blocks_reuse(policy,tag): {==}
def L.type_last_release_drops_once(tag): {==}
def L.data_first_release_keeps_alias(tag): {==}
def L.data_last_release_reclaims(tag): {==}
def L.consume_transfers_fields(): {==}
def L.release_queues_without_disposal(tag): {==}
def L.suspension_moves_one_holder(tag): {==}
def L.immutable_graph_rejects_backpatch(heap): {==}
