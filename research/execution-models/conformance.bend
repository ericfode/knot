import Base
import ./model.bend as M

def show(s: M.Join<U32>) -> String:
  match s:
    case M.JOpen{}: "open"
    case M.JLeft{x}: String.append("left:",U32.show(x))
    case M.JRight{x}: String.append("right:",U32.show(x))
    case M.JReady{a,b}: String.append(String.append(U32.show(a),","),U32.show(b))
    case M.JTaken{}: "taken"

def show_update(u: M.Update<U32>) -> String:
  match u:
    case M.JAccept{s}: String.append("accepted:",show(s))
    case M.JReject{s}: String.append("rejected:",show(s))

def show_take(t: M.Taken<U32>) -> String:
  match t:
    case M.JWait{s}: String.append("waiting:",show(s))
    case M.JYield{s,a,b}: String.append(String.append("yield:",show(M.JReady{a,b})),String.append(";",show(s)))
    case M.JDenied{s}: String.append("denied:",show(s))

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(show(M.state(U32,M.right(U32,M.state(U32,M.left(U32,M.JOpen{},7)),9))))
    IO.print(show(M.state(U32,M.left(U32,M.state(U32,M.right(U32,M.JOpen{},9)),7))))
    IO.print(show_update(M.left(U32,M.JLeft{7},9)))
    IO.print(show_update(M.right(U32,M.JRight{9},7)))
    IO.print(show_take(M.take(U32,M.JReady{7,9})))
    IO.print(show_take(M.take(U32,M.after_take(U32,M.take(U32,M.JReady{7,9})))))
    IO.print(show_take(M.take(U32,M.JLeft{7})))
    IO.print(show_take(M.take(U32,M.JRight{9})))
    IO.print(show_take(M.take(U32,M.JOpen{})))
    IO.print(show_take(M.take(U32,M.JReady{0,4294967295})))
