import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S
import ./heap-code.bend as A
import ./heap.bend as H

law size_class_counts_live_slots:
  for +kind: Bool
  for +first: Bool
  for +second: Bool
  {H.slots(H.Layout{kind,[first,second]}) == 2 : U32}

law scalar_slots_occupy_words:
  {H.bytes(H.slots(H.Layout{True{},[False{},False{}]})) == 24 : U32}

law nullary_cell_includes_prefix_and_tag:
  {H.bytes(0) == 16 : U32}

law payload_follows_ownership_prefix:
  {H.payload_address(65536) == 65548 : U32}

law last_class_precedes_release_stack:
  {H.class_address(4095) == 16380 : U32}

law first_release_frame_follows_classes:
  {H.frame_address(0) == 16384 : U32}

law last_release_frame_fits_reservation:
  {H.frame_address(4095) == 49144 : U32}

law count_word_is_outside_payload:
  for +pointer: U32
  {H.prefix(pointer,4) == [A.get(pointer),A.word(12),A.op(107),A.load(4)] : List<&2,A.Instruction>}

law retain_adds_one_before_return:
  for +pointer: U32
  for +count: U32
  {H.retain_count(pointer,count) == [A.get(pointer),A.word(12),A.op(107),A.get(count),A.word(1),A.op(106),A.save(4)] : List<&2,A.Instruction>}

law consumed_parent_uses_free_without_child_release:
  {H.unique_open(20) == [A.get(0),A.call(30),A.op(15)] : List<&2,A.Instruction>}

law last_release_keeps_parent_until_field_scan:
  for +pointer: U32
  for +frame: U32
  {H.begin_drop(pointer,frame) == [
    A.get(pointer),A.word(12),A.op(107),A.word(2),A.save(0),
    A.get(pointer),A.word(12),A.op(107),A.word(0),A.save(4),
    A.get(frame),A.word(1),A.save(4)] : List<&2,A.Instruction>}

law free_cell_keeps_previous_class_head:
  for +pointer: U32
  for +class: U32
  {H.recycle(pointer,class) == [
    A.get(pointer),A.word(12),A.op(107),A.word(0),A.save(0),
    A.get(pointer),A.word(12),A.op(107),A.get(class),A.load(0),A.save(4),
    A.get(class),A.get(pointer),A.save(0),A.global_get(1),A.word(1),A.op(107),A.global_set(1)] : List<&2,A.Instruction>}

law exhausted_cleanup_retains_memory_and_pending:
  {H.outcome(3) == [A.word(3),A.global_set(4),A.word(3),A.op(15)] : List<&2,A.Instruction>}

law stack_bounds_precede_frame_publication:
  {H.stack_room() == [
    A.global_get(5),A.global_get(7),A.op(79),A.When{[A.word(3),A.global_set(4),A.word(3),A.op(15)],Nil{}},
    A.global_get(5),A.word(4096),A.op(79),A.When{[A.word(3),A.global_set(4),A.word(3),A.op(15)],Nil{}}] : List<&2,A.Instruction>}

law scalar_descriptor_never_traces_a_pointer:
  {H.edge_cases([False{}],0) == [
    A.get(1),A.word(0),A.op(70),A.When{[A.word(0),A.op(15)],Nil{}},A.word(0),A.op(15)] : List<&2,A.Instruction>}

law pointer_descriptor_traces_its_exact_slot:
  {H.edge_cases([False{},True{}],0) == [
    A.get(1),A.word(0),A.op(70),A.When{[A.word(0),A.op(15)],Nil{}},
    A.get(1),A.word(1),A.op(70),A.When{[A.word(1),A.op(15)],Nil{}},A.word(0),A.op(15)] : List<&2,A.Instruction>}

law instruction_budget_is_explicit:
  for chunk: A.Chunk
  for cap: U32
  {A.encode(0n,chunk,cap) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,B.Builder>}
