import Base
import ./LAWS.bend as L

def L.words_round_trip(): {==}
def L.plan_encodes_image(): {==}
def L.image_decodes_plan(): {==}
def L.images_canonical(): {==}
def L.magic_refused(): {==}
def L.opcode_refused(): {==}
def L.tag_refused(): {==}
def L.layout_refused(): {==}
def L.mutations_sound(): {==}
def L.entry_needs_fuel(code,f,ops,stack,heap,calls,quantum,out): {==}
def L.finished_is_final(code,outcome,stack,heap,meter,out): {==}
def L.tail_skips_scopes(): {==}
def L.operands_are_not_tail(): {==}
def L.nat_sum_bound(heap): {==}
def L.nat_product_bound(heap): {==}
def L.division_by_zero(code,heap,a,b,x): {==}
def L.remainder_by_zero(code,heap,a,b,x): {==}
def L.wide_shifts_vanish(a): {==}
def L.value_on_runs(): {==}
def L.closure_captures_runs(): {==}
def L.recursion_map_runs(): {==}
def L.string_append_mortal_runs(): {==}
def L.foreign_print_runs(): {==}
