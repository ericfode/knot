import Base
import ./LAWS.bend as Laws

def Laws.empty_contents(T): {==}
def Laws.singleton_get(T,x): {==}
def Laws.growth_order(T,a,b,c,d,e): {==}
def Laws.reserve_preserves(T,a,b,c): {==}
def Laws.set_preserves(T,a,b,c,x): {==}
def Laws.swap_old_and_preserves(T,a,b,c,x): {==}
def Laws.push_pop_growth(T,a,b,x): {==}
def Laws.slice_order(T,a,b,c,d,e): {==}
def Laws.logical_bounds(T,a,b,c,x): {==}
def Laws.max_index(T,a): {==}
def Laws.zero_limit(T,x): {==}
def Laws.empty_pop(T): {==}
def Laws.empty_slice(T): {==}
def Laws.reversed_slice(T,x): {==}
def Laws.maximum_reserve(T,x): {==}
def Laws.initial_metadata(): {==}
def Laws.initial_capacity(): {==}
def Laws.rounded_capacity(): {==}
def Laws.effective_limit(): {==}
def Laws.get_preserves(T,a,b,c): {==}
def Laws.set_then_get(T,a,b,c,x): {==}
def Laws.push_success(T,a,b,x): {==}
def Laws.pop_length(T,a,b,x): {==}
def Laws.maximum_plan(): {==}
def Laws.exact_limit_reserve(): {==}
