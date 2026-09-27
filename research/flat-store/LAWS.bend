import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ../../src/syntax.bend as S
import ../owned-store/store.bend as T
import ./layout.bend as L
import ./assembly.bend as A
import ./module.bend as M

def bytes(result: Result<S.Error,B.Builder>) -> Result<S.Error,List<&2,U32>>:
  match result:
    case Done{builder}: Done{B.finish(builder)}
    case Fail{error}: Fail{error}

law locator_round_trip:
  for +arena: U32
  for +index: U32
  for +generation: U32
  {L.decode_locator(L.encode_locator(T.Locator{arena,index,generation})) == Done{T.Locator{arena,index,generation}} : Result<L.Error,T.Locator>}

law missing_word_rejected:
  for arena: U32
  for index: U32
  {L.decode_locator([arena,index]) == Fail{L.LocatorArity{}} : Result<L.Error,T.Locator>}

law trailing_words_rejected:
  for arena: U32
  for index: U32
  for generation: U32
  for extra: U32
  for tail: List<&2,U32>
  {L.decode_locator(Con{arena,Con{index,Con{generation,Con{extra,tail}}}}) == Fail{L.LocatorArity{}} : Result<L.Error,T.Locator>}

law oversized_capacity_precedes_address:
  for index: U32
  {L.offset(4097,index) == Fail{L.CapacityLimit{}} : Result<L.Error,U32>}

law empty_has_no_address:
  {L.offset(0,0) == Fail{L.IndexBounds{}} : Result<L.Error,U32>}

law first_cell_follows_header:
  {L.offset(1,0) == Done{32} : Result<L.Error,U32>}

law last_cell_fits_reserved_memory:
  {L.offset(4096,4095) == Done{65552} : Result<L.Error,U32>}

law padding_is_not_a_cell:
  {L.offset(4096,4096) == Fail{L.IndexBounds{}} : Result<L.Error,U32>}

law zero_fuel_is_explicit:
  for chunk: A.Chunk
  for cap: U32
  {A.encode(0n,chunk,cap) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,B.Builder>}

law sentinel_is_signed_minus_one:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeNegativeOne{}},2)) == Done{[65,127]} : Result<S.Error,List<&2,U32>>}

law store_encodes_alignment_and_offset:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeMemory{54,128}},4)) == Done{[54,2,128,1]} : Result<S.Error,List<&2,U32>>}

law signed_positive_boundary:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeWord{2147483647}},6)) == Done{[65,255,255,255,255,7]} : Result<S.Error,List<&2,U32>>}

law signed_overflow_is_explicit:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeWord{2147483648}},6)) == Fail{S.Internal{"emit","signed-range"}} : Result<S.Error,List<&2,U32>>}

law output_limit_is_explicit:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeNegativeOne{}},1)) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,List<&2,U32>>}

law module_limit_is_explicit:
  {M.emit(0) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,List<&2,U32>>}
