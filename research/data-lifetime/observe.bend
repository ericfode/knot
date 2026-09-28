import Base
import ./model.bend as M

def numbers(xs: List<&2,U32>) -> String:
  match xs:
    case Nil{}: ""
    case Con{h,Nil{}}: U32.show(h)
    case Con{h,t}: String.concat([U32.show(h),",",numbers(t)])

def holders(xs: List<&2,M.Holder>) -> String:
  match xs:
    case Nil{}: ""
    case Con{M.Holder{s,r},Nil{}}: String.concat([U32.show(s),":",U32.show(r)])
    case Con{M.Holder{s,r},t}: String.concat([U32.show(s),":",U32.show(r),",",holders(t)])

def cell(value: M.Cell) -> String:
  match value:
    case M.Cell{i,k,t,n,cs}: String.join([U32.show(i),U32.show(k),U32.show(t),U32.show(n),numbers(cs)],":")

def cells(xs: List<&2,M.Cell>) -> String:
  match xs:
    case Nil{}: ""
    case Con{h,Nil{}}: cell(h)
    case Con{h,t}: String.concat([cell(h),";",cells(t)])

def wire(heap: M.Heap, status: U32) -> String:
  match heap:
    case M.Heap{p,l,c,n,cs,rs,q,r,m,d}:
      String.join([U32.show(status),U32.show(n),holders(rs),cells(cs),numbers(q),holders(r),numbers(m),numbers(d)],"|")

def report(pair: M.Store & U32, next: M.Store -> IO(Unit)) -> IO(Unit):
  (store,status) = pair
  match store:
    case M.Store{+heap}:
      do IO<Unit>:
        IO.print(wire(heap,status))
        next(M.Store{heap})

def run(commands: List<&2,M.Command>, store: M.Store) -> IO(Unit):
  match commands:
    case Nil{}: IO.pure(Unit,Unit{})
    case Con{head,tail}: report(M.transition(head,store),next => run(tail,next))
