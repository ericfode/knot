import Base
import ./PROOF.bend as P
import ./LAWS.bend as L

# Constructive instantiations: U32 with distinct nonempty element witnesses.
def inhabited() -> Unit:
  -w_empty_contents = L.empty_contents(U32)
  -w_singleton_get = L.singleton_get(U32,11)
  -w_growth_order = L.growth_order(U32,11,23,37,49,61)
  -w_reserve_preserves = L.reserve_preserves(U32,11,23,37)
  -w_set_preserves = L.set_preserves(U32,11,23,37,49)
  -w_swap_old_and_preserves = L.swap_old_and_preserves(U32,11,23,37,49)
  -w_push_pop_growth = L.push_pop_growth(U32,11,23,37)
  -w_slice_order = L.slice_order(U32,11,23,37,49,61)
  -w_logical_bounds = L.logical_bounds(U32,11,23,37,49)
  -w_max_index = L.max_index(U32,11)
  -w_zero_limit = L.zero_limit(U32,11)
  -w_empty_pop = L.empty_pop(U32)
  -w_empty_slice = L.empty_slice(U32)
  -w_reversed_slice = L.reversed_slice(U32,11)
  -w_maximum_reserve = L.maximum_reserve(U32,11)
  -w_initial_metadata = L.initial_metadata()
  -w_initial_capacity = L.initial_capacity()
  -w_rounded_capacity = L.rounded_capacity()
  -w_effective_limit = L.effective_limit()
  -w_get_preserves = L.get_preserves(U32,11,23,37)
  -w_set_then_get = L.set_then_get(U32,11,23,37,49)
  -w_push_success = L.push_success(U32,11,23,37)
  -w_pop_length = L.pop_length(U32,11,23,37)
  -w_maximum_plan = L.maximum_plan()
  -w_exact_limit_reserve = L.exact_limit_reserve()
  Unit{}
