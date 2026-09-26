import Base

# One owning slot. Reuse is explicit; no numeric handles or generations here.
type Slot<-T: Type> is Type:
  Vacant{}
  Occupied{value: T}

type Put<-T: Type> is Type:
  Inserted{slot: Slot<T>}
  Rejected{slot: Slot<T>, value: T}

type Take<-T: Type> is Type:
  Missing{slot: Slot<T>}
  Extracted{slot: Slot<T>, value: T}

def put(-T: Type, s: Slot<T>, x: T) -> Put<T>:
  match s:
    case Vacant{}: Inserted{Occupied{x}}
    case Occupied{value}: Rejected{Occupied{value},x}

def take(-T: Type, s: Slot<T>) -> Take<T>:
  match s:
    case Vacant{}: Missing{Vacant{}}
    case Occupied{value}: Extracted{Vacant{},value}

def put_slot(-T: Type, p: Put<T>) -> Slot<T>:
  match p:
    case Inserted{s}: s
    case Rejected{s,value}: s

def take_slot(-T: Type, t: Take<T>) -> Slot<T>:
  match t:
    case Missing{s}: s
    case Extracted{s,value}: s
