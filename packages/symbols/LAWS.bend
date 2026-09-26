import Base
import ./protocol.bend as P
import ./observe.bend as O
import ./cases.bend as C
import ./model.bend as M
import ./main.bend as S

# Universal public observations; no preconditions or uninhabited parameters.
law first:
  for +name: String
  {O.run([P.Intern{name},P.Resolve{0},P.Length{}],1) ==
   [P.Observed{P.Id{0},1,1,[name]},P.Observed{P.Name{name},1,1,[name]},P.Observed{P.Number{1},1,1,[name]}] : List<&2,P.Observation>}

law zero_limit:
  for +name: String
  {O.run([P.Intern{name},P.Find{name},P.Resolve{0}],0) ==
   [P.Observed{P.Full{},0,0,[]},P.Observed{P.Missing{},0,0,[]},P.Observed{P.Invalid{},0,0,[]}] : List<&2,P.Observation>}

law empty_find:
  for name: String
  {O.run([P.Find{name}],3) == [P.Observed{P.Missing{},0,3,[]}] : List<&2,P.Observation>}

# Concrete normalization/refinement witnesses; not universal refinement proofs.
law repeat_preserves:
  {C.check(C.repeat(),4) == True{} : Bool}
law full_preserves:
  {C.check(C.full(),1) == True{} : Bool}
law unicode_exact:
  {C.check(C.unicode(),6) == True{} : Bool}
law default_limit:
  {O.trace([P.Length{},P.Limit{},P.Resolve{4294967295}],S.Table.new()) ==
   [P.Observed{P.Number{0},0,16777216,[]},P.Observed{P.Number{16777216},0,16777216,[]},P.Observed{P.Invalid{},0,16777216,[]}] : List<&2,P.Observation>}
law clamp_limit:
  {O.run([P.Limit{}],4294967295) == [P.Observed{P.Number{16777216},0,16777216,[]}] : List<&2,P.Observation>}
