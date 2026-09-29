import Base
import ./image-LAWS.bend as L
import ./syntax.bend as S
import ./core.bend as C
import ./image.bend as I
import ./image-plan.bend as P
import ./image-layout.bend as Y
import ./image-decode.bend as X

def L.erase_flag_book(at):
  {==}

def L.erase_mixed_book(at):
  {==}

def L.round_trip_flag_book(at):
  {==}

def L.round_trip_mixed_book(at):
  {==}

def L.round_trip_any_value(at,type_id,tag):
  {==}

def L.round_trip_all_forms():
  {==}

def L.flag_refuted_at_1(at, e):
  %e : L.refusal(_)
  Unit{}

def L.flag_refuted_at_2(at, e):
  %e : L.refusal(_)
  Unit{}

def L.mixed_refuted_at_13(at, e):
  %e : L.refusal(_)
  Unit{}

def L.mixed_refuted_at_14(at, e):
  %e : L.refusal(_)
  Unit{}

def L.mixed_refuted_at_15(at, e):
  %e : L.refusal(_)
  Unit{}

def L.mixed_refuted_at_16(at, e):
  %e : L.refusal(_)
  Unit{}

def L.mixed_refuted_at_17(at, e):
  %e : L.refusal(_)
  Unit{}

def L.mixed_refuted_at_18(at, e):
  %e : L.refusal(_)
  Unit{}

def L.wide_refuted(at, e):
  %e : L.refusal(_)
  Unit{}

def L.accent_refuted(at, e):
  %e : L.refusal(_)
  Unit{}

def L.empty_name_is_refused(at):
  {==}

def L.nul_name_is_refused(at):
  {==}

def L.wide_name_is_refused(at):
  {==}

def L.magic_spells_kimg():
  {==}

def L.empty_file_is_not_an_image():
  {==}

def L.all_erased_constructor_is_a_value(type_id,tag,deepest):
  {==}

def L.erased_let_is_its_body(n,types,functions,locals,depth,token,level,type_id,value,body):
  {==}

def L.erased_operand_is_dropped(n,types,functions,locals,depth,term,terms,token,type_id,parameters):
  {==}

def L.let_takes_its_bodys_type(initial,result,a,b,slot):
  {==}

def L.absent_arm_is_a_missing_row(n,types,functions,locals,depth,key):
  {==}

def L.chunk_bytes_are_little_endian():
  {==}

def L.empty_stream_ends():
  {==}
