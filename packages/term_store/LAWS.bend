import Base
import ./main.bend as S
import ./model.bend as M
import ./checks.bend as C
import ./memo_checks.bend as MC
import ./lifecycle.bend as LC
import ./payload.bend as P

# Universal theorem: public pure transition kernel refines the independent table.
law transition_refinement:
  for T: Data
  for E: Data
  for c: S.Cell<T,E>
  for a: S.Action<T,E>
  {S.Cell.step(T,E,c,a) == M.step(T,E,a,c) : S.Cell<T,E> & Result<S.Error,Unit>}

law pending_is_incomplete:
  for T: Data
  for E: Data
  {S.Cell.result(T,E,S.Pending{}) == Fail{S.NotReady{}} : Result<S.Error,Result<E,T>>}

law evaluating_is_incomplete:
  for T: Data
  for E: Data
  {S.Cell.result(T,E,S.Evaluating{}) == Fail{S.NotReady{}} : Result<S.Error,Result<E,T>>}

law success_is_exact:
  for T: Data
  for E: Data
  for x: T
  {S.Cell.result(T,E,S.Ready{x}) == Done{Done{x}} : Result<S.Error,Result<E,T>>}

law failure_is_exact:
  for T: Data
  for E: Data
  for e: E
  {S.Cell.result(T,E,S.Failed{e}) == Done{Fail{e}} : Result<S.Error,Result<E,T>>}

# Universal list-model law; NOT a proof of Vec-backed store refinement.
law appended_lookup:
  for T: Data
  for xs: List<&2,T>
  for x: T
  {M.at(T,M.append(T,xs,x),M.count(T,xs)) == Done{x} : Result<S.Error,T>}

# Concrete normalization of inhabited store traces. No universal store claim.
law store_trace:
  {C.store_witness() == True{} : Bool}

law zero_limit:
  {C.zero_witness() == True{} : Bool}

# Universal payload theorem on a fixed inhabited 3-cell operation schedule.
# It is not a theorem about arbitrary arena sizes or arbitrary histories.
law generic_growth_write:
  for T: Data
  for a: T
  for b: T
  for c: T
  for x: T
  {P.preserved(T,a,b,c,x) == [a,x,c] : List<T>}

law memo_trace:
  {MC.witness() == True{} : Bool}

law lifetime_separation:
  {LC.separate_lifetimes() == True{} : Bool}

law exhaustion_never_wraps:
  {LC.scope_exhaustion() == True{} : Bool}

law limit_clamped:
  {LC.max_limit() == True{} : Bool}

law zero_store_consumes_scope:
  {LC.zero_consumes_scope() == True{} : Bool}
