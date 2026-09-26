import Base
import ./main.bend as S
import ./checks.bend as C

# Store lifetime witnesses use one affine scope chain, no representation access.
def read_pair(expected: Result<S.Error,U32>,p: S.Store<U32> & Result<S.Error,U32>) -> Bool:
  (s,r) = p
  C.value_eq(r,expected)

def first_cell(second: S.Store<U32>,p: S.Store<U32> & Result<S.Error,S.Id>) -> Bool:
  (first,r) = p
  match r:
    case Fail{e}: False{}
    case Done{+id}:
      Bool.and(read_pair(Done{17},S.Store.get(U32,first,id)),read_pair(Fail{S.WrongScope{}},S.Store.get(U32,second,id)))

def second_created(first: S.Store<U32>,r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{second}: first_cell(second,S.Store.alloc(U32,first,17))

def next_created(first: S.Store<U32>,p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  second_created(first,r)

def first_created(scopes: S.Scopes,r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{first}: next_created(first,S.Store.new(U32,scopes,2))

def both_created(p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  first_created(scopes,r)

def separate_lifetimes() -> Bool:
  both_created(S.Store.new(U32,S.Scopes.from(91),2))

def exhausted_result(r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: C.error_eq(e,S.ScopeExhausted{})
    case Done{s}: False{}

def exhausted_again(p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  exhausted_result(r)

def exhausted_twice(p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  Bool.and(exhausted_result(r),exhausted_again(S.Store.new(U32,scopes,0)))

def final_slot(p: S.Store<U32> & Result<S.Error,S.Id>) -> Bool:
  (s,r) = p
  C.alloc_eq(r,Done{S.Id{4294967295,0}})

def last_created(scopes: S.Scopes,r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}:
      Bool.and(final_slot(S.Store.alloc(U32,s,71)),exhausted_twice(S.Store.new(U32,scopes,1)))

def last_pair(p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  last_created(scopes,r)

def scope_exhaustion() -> Bool:
  last_pair(S.Store.new(U32,S.Scopes.from(4294967295),1))

def max_limit() -> Bool:
  C.trace([C.Limit{},C.Length{},C.Read{S.Id{4294967295,0}}],4294967295,4294967295)

def zero_then_live_alloc(p: S.Store<U32> & Result<S.Error,S.Id>) -> Bool:
  (s,r) = p
  C.alloc_eq(r,Done{S.Id{92,0}})

def zero_then_live_result(r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: zero_then_live_alloc(S.Store.alloc(U32,s,101))

def zero_then_live_pair(p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  zero_then_live_result(r)

def zero_first(scopes: S.Scopes,r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: zero_then_live_pair(S.Store.new(U32,scopes,1))

def zero_first_pair(p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  zero_first(scopes,r)

def zero_last(scopes: S.Scopes,r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: exhausted_twice(S.Store.new(U32,scopes,1))

def zero_last_pair(p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  zero_last(scopes,r)

def zero_consumes_scope() -> Bool:
  Bool.and(zero_first_pair(S.Store.new(U32,S.Scopes.from(91),0)),
    zero_last_pair(S.Store.new(U32,S.Scopes.from(4294967295),0)))
