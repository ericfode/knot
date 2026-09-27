import Base
import ./LAWS.bend as L

def L.locator_round_trip(arena,index,generation): {==}
def L.missing_word_rejected(arena,index): {==}
def L.trailing_words_rejected(arena,index,generation,extra,tail): {==}
def L.oversized_capacity_precedes_address(index): {==}
def L.empty_has_no_address(): {==}
def L.first_cell_follows_header(): {==}
def L.last_cell_fits_reserved_memory(): {==}
def L.padding_is_not_a_cell(): {==}
def L.zero_fuel_is_explicit(chunk,cap): {==}
def L.sentinel_is_signed_minus_one(): {==}
def L.store_encodes_alignment_and_offset(): {==}
def L.signed_positive_boundary(): {==}
def L.signed_overflow_is_explicit(): {==}
def L.output_limit_is_explicit(): {==}
def L.module_limit_is_explicit(): {==}
