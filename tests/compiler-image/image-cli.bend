import Base
import ../../src/syntax.bend as S
import ../../src/driver.bend as D
import ../../src/image.bend as I
import ../../src/compile-cli.bend as CLI

# Test driver for the image codec. It reads an image file, decodes it with `image.decode` and either
# prints the plan in the gate's canonical text, or lays the plan out again and writes it, so the gate
# can compare both with vm/serializer.py:
#   image-cli decode IMAGE           prints the plan; the gate renders serializer.decode the same way
#   image-cli recode IMAGE OUTPUT    encodes the decoded plan again and writes it through the chunked path
# The image file is read whole, up to one word past the 16 MiB image limit, so an oversize image is read as one.

def numbers(values: List<&2,U32>) -> String:
  match values:
    case Nil{}: ""
    case Con{head,Nil{}}: U32.show(head)
    case Con{head,tail}: String.concat([U32.show(head),";",numbers(tail)])

def joined(parts: List<String>) -> String:
  match parts:
    case Nil{}: ""
    case Con{head,Nil{}}: head
    case Con{head,tail}: String.concat([head,";",joined(tail)])

type Show is Data:
  Node{node: I.Node}
  Nodes{nodes: List<&2,I.Node>}
  Rows{rows: List<&2,I.Row>}
  Default{default: Maybe<&2,I.Node>}

# The notation is prefix and bracketed: `con[type,tag](operand;operand)`, a Case
# `case[type,slot,scrutinee,mode](row;row|default)` and a row `-` or `branch[key,first,fields](body)`.
def show(fuel: Nat, mode: Show) -> String:
  match fuel mode:
    case 0n _: "!"
    case 1n+ +n Node{I.Literal{+t,I.Constant{+k,+d}}}: String.concat(["lit[",U32.show(t),",",U32.show(k),",",numbers(d),"]"])
    case 1n+ +n Node{I.Intrinsic{+t,+p,+operands}}: String.concat(["prim[",U32.show(t),",",U32.show(p),"](",show(n,Nodes{operands}),")"])
    case 1n+ +n Node{I.Value{+t,+tag}}: String.concat(["value[",U32.show(t),",",U32.show(tag),"]"])
    case 1n+ +n Node{I.Construct{+t,+tag,+operands}}: String.concat(["con[",U32.show(t),",",U32.show(tag),"](",show(n,Nodes{operands}),")"])
    case 1n+ +n Node{I.Reference{+t,+slot}}: String.concat(["ref[",U32.show(t),",",U32.show(slot),"]"])
    case 1n+ +n Node{I.Application{+t,+f,+operands}}: String.concat(["call[",U32.show(t),",",U32.show(f),"](",show(n,Nodes{operands}),")"])
    case 1n+ +n Node{I.Let{+t,+slot,+value,+body}}:
      String.concat(["let[",U32.show(t),",",U32.show(slot),"](",show(n,Node{value}),";",show(n,Node{body}),")"])
    case 1n+ +n Node{I.Case{+t,+slot,+scrutinee,+m,+rows,+default}}:
      String.concat(["case[",U32.show(t),",",U32.show(slot),",",U32.show(scrutinee),",",U32.show(m),"](",show(n,Rows{rows}),"|",show(n,Default{default}),")"])
    case 1n+ +n Node{I.Closure{+t,+live,+slots,+captures,+body}}:
      String.concat(["closure[",U32.show(t),",",U32.show(live),",",U32.show(slots),",",numbers(captures),"](",show(n,Node{body}),")"])
    case 1n+ +n Node{I.Invoke{+t,+function,Nil{}}}: String.concat(["invoke[",U32.show(t),"](",show(n,Node{function}),")"])
    case 1n+ +n Node{I.Invoke{+t,+function,+arguments}}:
      String.concat(["invoke[",U32.show(t),"](",show(n,Node{function}),";",show(n,Nodes{arguments}),")"])
    case 1n+ +n Node{I.Foreign{+t,+f,+operands}}: String.concat(["foreign[",U32.show(t),",",U32.show(f),"](",show(n,Nodes{operands}),")"])
    case 1n+ +n Nodes{Nil{}}: ""
    case 1n+ +n Nodes{Con{head,Nil{}}}: show(n,Node{head})
    case 1n+ +n Nodes{Con{head,tail}}: String.concat([show(n,Node{head}),";",show(n,Nodes{tail})])
    case 1n+ +n Rows{Nil{}}: ""
    case 1n+ +n Rows{Con{I.Missing{},Nil{}}}: "-"
    case 1n+ +n Rows{Con{I.Missing{},tail}}: String.concat(["-;",show(n,Rows{tail})])
    case 1n+ +n Rows{Con{I.Branch{+key,+first,+fields,+body},Nil{}}}:
      String.concat(["branch[",U32.show(key),",",U32.show(first),",",U32.show(fields),"](",show(n,Node{body}),")"])
    case 1n+ +n Rows{Con{I.Branch{+key,+first,+fields,+body},tail}}:
      String.concat(["branch[",U32.show(key),",",U32.show(first),",",U32.show(fields),"](",show(n,Node{body}),");",show(n,Rows{tail})])
    case 1n+ +n Default{None{}}: "-"
    case 1n+ +n Default{Some{node}}: show(n,Node{node})

def constructor_line(constructors: List<&2,I.Constructor>) -> String:
  match constructors:
    case Nil{}: ""
    case Con{I.Constructor{name,fields},Nil{}}: String.concat([name,"(",numbers(fields),")"])
    case Con{I.Constructor{name,fields},tail}: String.concat([name,"(",numbers(fields),") ",constructor_line(tail)])

def shape_line(index: U32, shape: I.Shape) -> String:
  match shape:
    case I.Algebraic{name,constructors}: String.concat(["type ",U32.show(index)," algebraic ",name," ",constructor_line(constructors)])
    case I.Arrow{domain,result}: String.concat(["type ",U32.show(index)," arrow ",U32.show(domain)," ",U32.show(result)])
    case I.Erased{domain,result}: String.concat(["type ",U32.show(index)," erased ",U32.show(domain)," ",U32.show(result)])
    case I.Opaque{name}: String.concat(["type ",U32.show(index)," opaque ",name])

def shape_lines(shapes: List<&2,I.Shape>, +index: U32) -> String:
  match shapes:
    case Nil{}: ""
    case Con{head,tail}: String.concat([shape_line(index,head),"\n",shape_lines(tail,U32.add(index,1))])

def function_lines(functions: List<&2,I.Function>, +index: U32) -> String:
  match functions:
    case Nil{}: ""
    case Con{I.Function{name,parameters,result,slots,body},tail}:
      String.concat(["function ",U32.show(index)," ",name," (",numbers(parameters),") ",U32.show(result)," ",U32.show(slots)," ",show(1000000n,Node{body}),"\n",function_lines(tail,U32.add(index,1))])

def plan_text(plan: I.Plan) -> String:
  match plan:
    case I.Plan{entry,representation,shapes,functions}:
      String.concat(["entry ",U32.show(entry),"\nrepresentation ",numbers(representation),"\n",shape_lines(shapes,0),function_lines(functions,0)])

def printed(result: Result<S.Error,I.Plan>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{plan}: IO.print(plan_text(plan))

def recoded_layout(path: String, result: Result<S.Error,I.Encoded>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{encoded}: CLI.image_sized(path,encoded,16777216)

def recoded(path: String, result: Result<S.Error,I.Plan>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{plan}: recoded_layout(path,I.layout(1000000n,plan))

type Then is Type:
  Print{}
  Recode{path: String}

def decoded(mode: Then, result: Result<S.Error,List<&2,U32>>) -> IO(Unit):
  match mode result:
    case Print{} Fail{e}: D.fail(e)
    case Recode{path} Fail{e}: D.fail(e)
    case Print{} Done{words}: printed(I.decode(words))
    case Recode{path} Done{words}: recoded(path,I.decode(words))

def bytes_read(mode: Then, result: Result<&1,&1,U32 & String,List<&2,U32>>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{bytes}: decoded(mode,I.words_of(bytes))

def pair_read(mode: Then, pair: File & Result<&1,&1,U32 & String,List<&2,U32>>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    bytes_read(mode,result)

def opened(mode: Then, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,List<&2,U32>>,Unit,File.read_bytes(file,16777220),pair => pair_read(mode,pair))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{command,Con{path,Nil{}}}:
      S.choose(IO(Unit),String.eq(command,"decode"),u =>
        IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(Print{},result)),u =>
        IO.die(Unit,5,"HostFailure\targuments\texpected decode IMAGE | recode IMAGE OUTPUT"))
    case Con{command,Con{path,Con{output,Nil{}}}}:
      S.choose(IO(Unit),String.eq(command,"recode"),u =>
        IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(Recode{output},result)),u =>
        IO.die(Unit,5,"HostFailure\targuments\texpected decode IMAGE | recode IMAGE OUTPUT"))
    case _: IO.die(Unit,5,"HostFailure\targuments\texpected decode IMAGE | recode IMAGE OUTPUT")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
