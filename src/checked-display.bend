import Base
import ./syntax.bend as S
import ./core.bend as C
import ./diagnostic.bend as D

def binders(fields: List<&2,C.Binding>) -> String:
  match fields:
    case Nil{}: ""
    case Con{C.Binding{token,level,q,type_id,param,known},tail}:
      String.concat([U32.show(q)," $",U32.show(level),":",U32.show(type_id),";",binders(tail)])

# Canonical observation of resolved syntax. This is not evaluation.
def term(fuel: Nat, value: C.Term) -> Result<S.Error,String>:
  match fuel value:
    case 0n _: Fail{S.Exhausted{"inspect",S.At{0,0,0,0}}}
    case 1n+ +n C.Value{token,type_id,tag}: Done{String.concat(["v",U32.show(type_id),".",U32.show(tag)])}
    case 1n+ +n C.Construct{token,type_id,tag,fields,args}:
      D.concat([Done{"v"},Done{U32.show(type_id)},Done{"."},Done{U32.show(tag)},Done{"{"},term(n,C.Sequence{args}),Done{"}"}])
    case 1n+ +n C.Reference{token,level,type_id}: Done{String.concat(["$",U32.show(level),":",U32.show(type_id)])}
    case 1n+ +n C.Application{token,index,type_id,args}:
      D.concat([Done{"call"},Done{U32.show(index)},Done{"("},term(n,C.Sequence{args}),Done{")"}])
    case 1n+ +n C.Let{token,level,q,type_id,value,body}:
      D.concat([Done{"let"},Done{U32.show(q)},Done{" $"},Done{U32.show(level)},Done{":"},Done{U32.show(type_id)},Done{"="},term(n,value),Done{" in "},term(n,body)])
    case 1n+ +n C.Case{token,level,type_id,arms}:
      D.concat([Done{"case $"},Done{U32.show(level)},Done{" ["},term(n,C.Sequence{arms}),Done{"]"}])
    case 1n+ +n C.Branch{tag,Nil{},body}:
      D.concat([Done{U32.show(tag)},Done{"=>"},term(n,body)])
    case 1n+ +n C.Branch{tag,fields,body}:
      D.concat([Done{U32.show(tag)},Done{"("},Done{binders(fields)},Done{")=>"},term(n,body)])
    case 1n+ +n C.Sequence{Nil{}}: Done{""}
    case 1n+ +n C.Sequence{Con{head,Nil{}}}: term(n,head)
    case 1n+ +n C.Sequence{Con{head,tail}}:
      D.concat([term(n,head),Done{";"},term(n,C.Sequence{tail})])

def parameter(value: C.Parameter) -> String:
  match value:
    case C.Parameter{token,q,type_id}: String.concat([U32.show(q),":",U32.show(type_id)])

def parameters(values: List<&2,C.Parameter>) -> String:
  match values:
    case Nil{}: ""
    case Con{head,Nil{}}: parameter(head)
    case Con{head,tail}: String.concat([parameter(head),",",parameters(tail)])

def functions(values: List<&2,C.Function>) -> Result<S.Error,String>:
  match values:
    case Nil{}: Done{""}
    case Con{C.Function{C.Signature{token,params,result},body},tail}:
      D.concat([Done{S.text(token)},Done{"("},Done{parameters(params)},Done{")->"},Done{U32.show(result)},Done{"="},term(4096n,body),Done{"\n"},functions(tail)])

def book(value: C.Book) -> Result<S.Error,String>:
  match value:
    case C.Book{types,funcs}: functions(funcs)
