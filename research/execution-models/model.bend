import Base

# Abstract sequential join protocol. Data payloads make observations reusable.
# This is not an affine payload store or a concurrent publication algorithm.
type Join<T: Data> is Data:
  JOpen{}
  JLeft{value: T}
  JRight{value: T}
  JReady{left: T, right: T}
  JTaken{}

type Update<T: Data> is Data:
  JAccept{state: Join<T>}
  JReject{state: Join<T>}

type Taken<T: Data> is Data:
  JWait{state: Join<T>}
  JYield{state: Join<T>, left: T, right: T}
  JDenied{state: Join<T>}

def left(-T: Data, s: Join<T>, x: T) -> Update<T>:
  match s:
    case JOpen{}:
      JAccept{JLeft{x}}
    case JLeft{value}:
      JReject{JLeft{value}}
    case JRight{value}:
      JAccept{JReady{x, value}}
    case JReady{left, right}:
      JReject{JReady{left, right}}
    case JTaken{}:
      JReject{JTaken{}}

def right(-T: Data, s: Join<T>, x: T) -> Update<T>:
  match s:
    case JOpen{}:
      JAccept{JRight{x}}
    case JLeft{value}:
      JAccept{JReady{value, x}}
    case JRight{value}:
      JReject{JRight{value}}
    case JReady{left, right}:
      JReject{JReady{left, right}}
    case JTaken{}:
      JReject{JTaken{}}

def state(-T: Data, u: Update<T>) -> Join<T>:
  match u:
    case JAccept{s}: s
    case JReject{s}: s

def take(-T: Data, s: Join<T>) -> Taken<T>:
  match s:
    case JOpen{}: JWait{JOpen{}}
    case JLeft{value}: JWait{JLeft{value}}
    case JRight{value}: JWait{JRight{value}}
    case JReady{left, right}: JYield{JTaken{}, left, right}
    case JTaken{}: JDenied{JTaken{}}

def after_take(-T: Data, t: Taken<T>) -> Join<T>:
  match t:
    case JWait{s}: s
    case JYield{s, left, right}: s
    case JDenied{s}: s
