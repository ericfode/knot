import Base
import ./syntax.bend as S
import ./core.bend as C
import ./records.bend as R

law reusable_occurrence_acquires_an_edge:
  for +source: U32
  for +destination: U32
  {R.transfer(True{},source,destination) == R.Op{2,source,destination,0,0,0} : R.Record}

law affine_occurrence_transfers_an_edge:
  for +source: U32
  for +destination: U32
  {R.transfer(False{},source,destination) == R.Op{3,source,destination,0,0,0} : R.Record}

law dropped_binding_enters_cleanup:
  for +source: U32
  {R.release(source) == R.Op{5,source,0,0,0,0} : R.Record}

law completion_carries_issued_attempt:
  for +join: U32
  for +slot: U32
  for +source: U32
  {R.delivery(join,slot,source) == R.Op{9,join,1,slot,source,0} : R.Record}

law logical_slots_survive_reverse_delivery:
  for +token: S.Token
  for +typ: U32
  for +join: U32
  for +first: U32
  for +flow: R.Flow
  {R.deliveries([C.Parameter{token,1,typ},C.Parameter{token,1,typ}],join,0,first,flow) == R.push(R.delivery(join,0,first),R.push(R.delivery(join,1,U32.add(first,1)),flow)) : R.Flow}

law erased_argument_has_no_slot:
  for token: S.Token
  for typ: U32
  for +params: List<&2,C.Parameter>
  for +join: U32
  for +slot: U32
  for +source: U32
  for +flow: R.Flow
  {R.deliveries(Con{C.Parameter{token,0,typ},params},join,slot,source,flow) == R.deliveries(params,join,slot,source,flow) : R.Flow}

law erased_parameter_has_no_owner:
  for token: S.Token
  for typ: U32
  for +params: List<&2,C.Parameter>
  for +types: List<&2,C.Datatype>
  for +level: U32
  for +first: U32
  for +flow: R.Flow
  {R.bind_parameters(Con{C.Parameter{token,0,typ},params},types,level,first,flow) == R.bind_parameters(params,types,U32.add(level,1),first,flow) : Result<S.Error,R.Flow>}

law tail_arguments_keep_source_order:
  for +token: S.Token
  for +typ: U32
  for +source: U32
  for +destination: U32
  for +flow: R.Flow
  {R.moves([C.Parameter{token,1,typ},C.Parameter{token,1,typ}],source,destination,flow) == R.push(R.Op{3,U32.add(source,1),U32.add(destination,1),0,0,0},R.push(R.Op{3,source,destination,0,0,0},flow)) : R.Flow}

law relocation_preserves_the_test:
  for +source: U32
  for +tag: U32
  for +yes: U32
  for +no: U32
  {R.relocate(R.Op{14,source,tag,0,1,0},[R.Address{0,yes},R.Address{1,no}]) == Done{R.Op{14,source,tag,yes,no,0}} : Result<S.Error,R.Record>}

law return_cleans_before_delivery:
  for +join: U32
  for +destination: U32
  for +source: U32
  for +flow: R.Flow
  {R.returned(R.Reply{join,destination},source,flow) == R.push(R.Op{11,join,1,destination,0,0},R.push(R.delivery(join,0,source),R.cleanup(flow))) : R.Flow}

law full_activation_cannot_wrap:
  for locals: List<&2,R.Slot>
  for plan: R.Plan
  for next: U32 -> R.Flow -> Result<S.Error,R.Flow>
  {R.reserve(1,0,R.Flow{locals,512,plan},next) == Fail{S.Exhausted{"records",S.At{0,0,0,0}}} : Result<S.Error,R.Flow>}

law pending_compilation_needs_fuel:
  for mode: R.Mode
  for types: List<&2,C.Datatype>
  for functions: List<&2,C.Function>
  for act: R.Activation
  for flow: R.Flow
  {R.lower(0n,mode,types,functions,act,flow) == Fail{S.Exhausted{"records",S.At{0,0,0,0}}} : Result<S.Error,R.Flow>}

law affine_binding_moves_even_data:
  for token: S.Token
  for constructors: List<&2,C.Constructor>
  for +level: U32
  for +capture: U32
  for +locals: List<&2,R.Slot>
  for +next: U32
  for +plan: R.Plan
  {R.bind_slot([C.Datatype{token,True{},constructors}],level,0,1,capture,R.Flow{locals,next,plan}) == Done{R.Flow{Con{R.Slot{level,capture,False{}},locals},next,plan}} : Result<S.Error,R.Flow>}
