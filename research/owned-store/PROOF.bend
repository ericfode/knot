import Base
import ./LAWS.bend as L

def L.free_accepts_owner(A,value,generation): {==}
def L.occupied_preserves_both_owners(A,old,incoming,generation): {==}
def L.retired_preserves_incoming(A,value): {==}
def L.stale_preserves_live_owner(A,value,generation,ceiling): {==}
def L.ceiling_retires_without_wrap(A,value): {==}
def L.last_generation_remains_usable(A,value): {==}
def L.capacity_limit_is_explicit(A): {==}
def L.zero_capacity_preserves_incoming(A,value): {==}
def L.singleton_take_transfers_and_advances(A,value): {==}
def L.singleton_take_retires(A,value): {==}
def L.wrong_arena_preserves_owner(A,value): {==}
def L.stale_locator_cannot_take_twice(A): {==}
def L.failed_release_preserves_store(A,B,store,error,dispose): {==}
def L.successful_release_applies_disposer(A,B,store,value,dispose): {==}
