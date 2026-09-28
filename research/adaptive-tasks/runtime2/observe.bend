import Base
import ./protocol.bend as P

def numbers(xs: List<&2,U32>) -> String:
  List.show(~&2,~U32,~U32.show,xs)

def object(value: P.Object) -> String:
  match value:
    case P.Free{}: "[]"
    case P.Object{id,kind,rc,tag,children}:
      String.concat(["[",U32.show(id),",",U32.show(kind),",",U32.show(rc),",",U32.show(tag),",",numbers(children),"]"])

def join(value: P.Join) -> String:
  match value:
    case P.Join{attempt,phase,arity,received,completions,code,base,count,results}:
      String.concat(["[",U32.show(attempt),",",U32.show(phase),",",U32.show(arity),",",U32.show(received),",",
        U32.show(completions),",",U32.show(code),",",U32.show(base),",",U32.show(count),",",numbers(results),"]"])

def state(value: P.State) -> String:
  match value:
    case P.State{config,P.Store{next,readers,freed,objects,captures,pending},joins,status,reply}:
      String.concat(["[",U32.show(status),",",U32.show(reply),",",U32.show(next),",",U32.show(readers),",",U32.show(freed),",",
        List.show(~&2,~P.Object,~object,objects),",",numbers(captures),",",numbers(pending),",",List.show(~&2,~P.Join,~join,joins),"]"])
