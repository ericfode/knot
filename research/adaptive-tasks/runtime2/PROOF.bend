import Base
import ./DRIVER-PROOF.bend as DriverProof
import ./LAWS.bend as L

def L.unsupported_preserves(cfg,store,joins,status,reply): {==}
def L.reserved_preserves(cfg,store,joins,status,reply): {==}
def L.span_exact_max(state): {==}
def L.span_overflow_preserves(state): {==}
def L.span_product_preserves(state): {==}
def L.type_cannot_share(id,tag,objects,limit): {==}
def L.move_once(tag): {==}
def L.decrement_keeps_alias(tag): {==}
def L.open_transfers(tag): {==}
def L.shared_open_atomic(tag): {==}
def L.cleanup_retains_work(tag): {==}
def L.reader_retains_work(tag): {==}
def L.identity_retires(): {==}
def L.stale_preserves_source(tag): {==}
def L.right_before_left(): {==}
def L.nary_once(): {==}
def L.cancel_owns_pending(): {==}
def L.empty_join_once(): {==}
