import Base
import ./LAWS.bend as L
import ./main.bend as S
import ./model.bend as M

def L.transition_refinement(T,E,c,a):
  match c:
    case S.Pending{}:
      match a:
        case S.Begin{}: {==}
        case S.Succeed{x}: {==}
        case S.Reject{e}: {==}
        case S.Cancel{}: {==}
    case S.Evaluating{}:
      match a:
        case S.Begin{}: {==}
        case S.Succeed{x}: {==}
        case S.Reject{e}: {==}
        case S.Cancel{}: {==}
    case S.Ready{x}:
      match a:
        case S.Begin{}: {==}
        case S.Succeed{y}: {==}
        case S.Reject{e}: {==}
        case S.Cancel{}: {==}
    case S.Failed{e}:
      match a:
        case S.Begin{}: {==}
        case S.Succeed{x}: {==}
        case S.Reject{f}: {==}
        case S.Cancel{}: {==}

def L.pending_is_incomplete(T,E): {==}
def L.evaluating_is_incomplete(T,E): {==}
def L.success_is_exact(T,E,x): {==}
def L.failure_is_exact(T,E,e): {==}

def L.appended_lookup(T,xs,x):
  match xs:
    case Nil{}: {==}
    case Con{y,rest}: L.appended_lookup(T,rest,x)

def L.store_trace(): {==}
def L.zero_limit(): {==}

def L.generic_growth_write(T,a,b,c,x): {==}
def L.memo_trace(): {==}
def L.lifetime_separation(): {==}
def L.exhaustion_never_wraps(): {==}
def L.limit_clamped(): {==}

def L.zero_store_consumes_scope(): {==}
