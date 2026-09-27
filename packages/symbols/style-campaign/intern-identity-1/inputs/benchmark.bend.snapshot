import Base
import ./main.bend as S

# Workload checks every returned ID and every reverse name; returns failure count.
def prefix(n: Nat) -> String:
  match n:
    case 0n: "compiler_"
    case 1n+p: SCon{Chr{120},prefix(p)}

def name(+pre: String, i: U32) -> String:
  String.append(pre,U32.show(i))

def id_error(expected: U32, result: Result<S.Error,U32>) -> U32:
  match result:
    case Fail{e}: 1
    case Done{id}: Bool.to_u32(U32.is_ne(expected,id))

def name_error(expected: String, result: Result<S.Error,String>) -> U32:
  match result:
    case Fail{e}: 1
    case Done{text}: Bool.to_u32(Bool.not(String.eq(expected,text)))

def inserted(next: S.Table -> U32 -> U32, i: U32, errors: U32,
  pair: S.Table & Result<S.Error,U32>) -> U32:
  (t,r) = pair
  next(t,U32.add(errors,id_error(i,r)))

def fill(count: Nat, +i: U32, +pre: String, t: S.Table, errors: U32) -> U32:
  match count:
    case 0n: errors
    case 1n+p: inserted(fill(p,U32.add(i,1),pre),i,errors,S.Table.intern(t,name(pre,i)))

# Continuations thread the table across full insertion, duplicate and reverse passes.
def after_resolve(next: S.Table -> U32 -> U32, expected: String, errors: U32,
  pair: S.Table & Result<S.Error,String>) -> U32:
  (t,r) = pair
  next(t,U32.add(errors,name_error(expected,r)))

def after_repeat(next: S.Table -> U32 -> U32, +i: U32, expected: String,
  errors: U32, pair: S.Table & Result<S.Error,U32>) -> U32:
  (t,r) = pair
  after_resolve(next,expected,U32.add(errors,id_error(i,r)),S.Table.resolve(t,i))

def verify(count: Nat, +i: U32, +pre: String, t: S.Table, errors: U32) -> U32:
  match count:
    case 0n: errors
    case 1n+p:
      after_repeat(verify(p,U32.add(i,1),pre),i,name(pre,i),errors,S.Table.intern(t,name(pre,i)))

def populate(count: Nat, +i: U32, +pre: String, done: S.Table -> U32 -> U32,
  t: S.Table, errors: U32) -> U32:
  match count:
    case 0n: done(t,errors)
    case 1n+p:
      inserted(populate(p,U32.add(i,1),pre,done),i,errors,S.Table.intern(t,name(pre,i)))

def workload(+count: Nat, +pre: String) -> U32:
  populate(count,0,pre,verify(count,0,pre),S.Table.new(),0)

def repeated(times: Nat, +count: Nat, +pre: String) -> U32:
  match times:
    case 0n: 0
    case 1n+p: U32.add(workload(count,pre),repeated(p,count,pre))
