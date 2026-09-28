import Base
import ./syntax.bend as S

def location(a: S.At) -> String:
  match a:
    case S.At{start,end,line,col}:
      String.concat([U32.show(start),":",U32.show(end),":",U32.show(line),":",U32.show(col)])

def error(e: S.Error) -> String:
  match e:
    case S.Invalid{phase,code,at}: String.concat(["Invalid\t",phase,"\t",code,"\t",location(at)])
    case S.Unsupported{phase,code,at}: String.concat(["Unsupported\t",phase,"\t",code,"\t",location(at)])
    case S.Exhausted{phase,at}: String.concat(["Exhausted\t",phase,"\tbudget\t",location(at)])
    case S.Internal{phase,code}: String.concat(["InternalFailure\t",phase,"\t",code])
    case S.Host{phase,code}: String.concat(["HostFailure\t",phase,"\t",code])

def status(e: S.Error) -> U32:
  match e:
    case S.Invalid{phase,code,at}: 2
    case S.Unsupported{phase,code,at}: 3
    case S.Exhausted{phase,at}: 4
    case S.Internal{phase,code}: 6
    case S.Host{phase,code}: 5

def concat(parts: List<&1,Result<S.Error,String>>) -> Result<S.Error,String>:
  match parts:
    case Nil{}: Done{""}
    case Con{Fail{e},tail}: Fail{e}
    case Con{Done{+head},tail}:
      S.bind(String,String,concat(tail),text => Done{String.append(head,text)})

def annotation(value: Maybe<&2,S.Token>) -> String:
  match value:
    case None{}: ""
    case Some{token}: String.append(":",S.text(token))

# Inspection-only canonical tree rendering; never used as a semantic evaluator.
def tree(fuel: Nat, node: S.Node) -> Result<S.Error,String>:
  match fuel node:
    case 0n _: Fail{S.Exhausted{"inspect",S.At{0,0,0,0}}}
    case 1n+ +n S.Variable{token}: Done{String.append("$",S.text(token))}
    case 1n+ +n S.Promotion{token}: Done{String.append("+$",S.text(token))}
    case 1n+ +n S.Constructor{token,args}:
      concat([Done{S.text(token)},Done{"{"},tree(n,S.Sequence{args}),Done{"}"}])
    case 1n+ +n S.Call{token,args}:
      concat([Done{S.text(token)},Done{"("},tree(n,S.Sequence{args}),Done{")"}])
    case 1n+ +n S.Binding{token,q,annot,value,body}:
      concat([Done{"let["},Done{U32.show(q)},Done{" "},Done{S.text(token)},Done{annotation(annot)},Done{" "},tree(n,value),Done{"] "},tree(n,body)])
    case 1n+ +n S.Match{token,value,arms}:
      concat([Done{"match["},tree(n,value),Done{"]("},tree(n,S.Sequence{arms}),Done{")"}])
    case 1n+ +n S.Arm{token,pattern,body}:
      concat([tree(n,pattern),Done{" => "},tree(n,body)])
    case 1n+ +n S.Parameter{token,q,typ}:
      Done{String.concat([U32.show(q)," ",S.text(token),":",S.text(typ)])}
    case 1n+ +n S.Datatype{token,reusable,ctors}:
      concat([Done{"type "},Done{S.text(token)},Done{Bool.pick(String,reusable," Data("," Type(")},tree(n,S.Sequence{ctors}),Done{")"}])
    case 1n+ +n S.Function{token,params,result,body}:
      concat([Done{"def "},Done{S.text(token)},Done{"("},tree(n,S.Sequence{params}),Done{")->"},Done{S.text(result)},Done{" "},tree(n,body)])
    case 1n+ +n S.TypeApply{token,args,q}:
      concat([Done{Bool.pick(String,U32.is_eq(q,2),"+","")},Done{S.text(token)},Done{"<"},tree(n,S.Sequence{args}),Done{">"}])
    case 1n+ +n S.TypeKind{token,q}:
      concat([Done{"Kind("},tree(n,q),Done{")"}])
    case 1n+ +n S.Quantity{token,q}: Done{String.append("&",U32.show(q))}
    case 1n+ +n S.QuantType{token}: Done{"Quant"}
    case 1n+ +n S.Meet{token,left,right}:
      concat([Done{"("},tree(n,left),Done{" <&> "},tree(n,right),Done{")"}])
    case 1n+ +n S.Generic{token,params,kind,ctors}:
      concat([Done{"type "},Done{S.text(token)},Done{"<"},tree(n,S.Sequence{params}),Done{"> "},tree(n,kind),Done{"("},tree(n,S.Sequence{ctors}),Done{")"}])
    case 1n+ +n S.TypedParameter{token,q,typ}:
      concat([Done{U32.show(q)},Done{" "},Done{S.text(token)},Done{":"},tree(n,typ)])
    case 1n+ +n S.TypedFunction{token,params,result,body}:
      concat([Done{"def "},Done{S.text(token)},Done{"("},tree(n,S.Sequence{params}),Done{")->"},tree(n,result),Done{" "},tree(n,body)])
    case 1n+ +n S.TypedBinding{token,q,annot,value,body}:
      concat([Done{"let["},Done{U32.show(q)},Done{" "},Done{S.text(token)},Done{":"},tree(n,annot),Done{" "},tree(n,value),Done{"] "},tree(n,body)])
    case 1n+ +n S.Sequence{Nil{}}: Done{""}
    case 1n+ +n S.Sequence{Con{head,Nil{}}}: tree(n,head)
    case 1n+ +n S.Sequence{Con{head,tail}}:
      concat([tree(n,head),Done{"; "},tree(n,S.Sequence{tail})])
