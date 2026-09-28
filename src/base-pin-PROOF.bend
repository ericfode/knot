import Base
import ./base-pin-LAWS.bend as L

def L.word_is_big_endian(): {==}
def L.octets_are_big_endian(): {==}
def L.rotate_keeps_wrapped_bit(): {==}
def L.zeros_preserve_suffix(tail): {==}
def L.abc_padding_keeps_bytes_and_bit_length(): {==}
def L.fifty_five_bytes_fit_one_block(): {==}
def L.fifty_six_bytes_need_two_blocks(): {==}
def L.complete_block_still_gets_padding(): {==}
def L.second_block_keeps_bit_length(): {==}
def L.digest_keeps_word_order_and_leading_zeros(): {==}
def L.matching_pin_preserves_text(text): {==}
def L.wrong_pin_is_host_failure(text): {==}
def L.hash_failure_is_preserved(text,error): {==}
def L.non_ascii_pin_is_host_failure(): {==}
def L.byte_limit_is_checked_before_absorption(tail,reversed): {==}
