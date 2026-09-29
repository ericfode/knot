import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/driver.bend as D
import ../../src/image.bend as I
import ../../src/image-plan.bend as P
import ../../src/image-layout.bend as Y
import ../../src/image-decode.bend as X
import ../../src/compile-cli.bend as CLI
import ../../src/diagnostic.bend as G

# Test driver for the image codec. It reads an image file, decodes it with `image.decode` and either
# prints the plan in the gate's canonical text, or lays the plan out again and writes it, so the gate
# can compare both with vm/serializer.py:
#   image-cli decode IMAGE           prints the plan; the gate renders serializer.decode the same way
#   image-cli recode IMAGE OUTPUT    encodes the decoded plan again and writes it through the chunked path
#   image-cli plan SOURCE            prints erase_tokens of the checked book, in the same text
#   image-cli roundtrip SOURCE       prints `Roundtrip<TAB>equal` when decode(encode(book)) and erase_tokens(book) print alike
#   image-cli named NAME             encodes the one-function book whose datatype is called NAME and prints `Encoded<TAB>words`
#   image-cli answers SOURCE         prints the outcome of erase_tokens and of recoded, `Done` or a diagnostic, one line each;
#                                    SOURCE is read at the image profile's maximum budgets
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
  Node{node: P.Node}
  Nodes{nodes: List<&2,P.Node>}
  Rows{rows: List<&2,P.Row>}
  Default{default: Maybe<&2,P.Node>}

# The notation is prefix and bracketed: `con[type,tag](operand;operand)`, a Case
# `case[type,slot,scrutinee,mode](row;row|default)` and a row `-` or `branch[key,first,fields](body)`.
def show(fuel: Nat, mode: Show) -> String:
  match fuel mode:
    case 0n _: "!"
    case 1n+ +n Node{P.Literal{+t,P.Constant{+k,+d}}}: String.concat(["lit[",U32.show(t),",",U32.show(k),",",numbers(d),"]"])
    case 1n+ +n Node{P.Intrinsic{+t,+p,+operands}}: String.concat(["prim[",U32.show(t),",",U32.show(p),"](",show(n,Nodes{operands}),")"])
    case 1n+ +n Node{P.Value{+t,+tag}}: String.concat(["value[",U32.show(t),",",U32.show(tag),"]"])
    case 1n+ +n Node{P.Construct{+t,+tag,+operands}}: String.concat(["con[",U32.show(t),",",U32.show(tag),"](",show(n,Nodes{operands}),")"])
    case 1n+ +n Node{P.Reference{+t,+slot}}: String.concat(["ref[",U32.show(t),",",U32.show(slot),"]"])
    case 1n+ +n Node{P.Application{+t,+f,+operands}}: String.concat(["call[",U32.show(t),",",U32.show(f),"](",show(n,Nodes{operands}),")"])
    case 1n+ +n Node{P.Let{+t,+slot,+value,+body}}:
      String.concat(["let[",U32.show(t),",",U32.show(slot),"](",show(n,Node{value}),";",show(n,Node{body}),")"])
    case 1n+ +n Node{P.Case{+t,+slot,+scrutinee,+m,+rows,+default}}:
      String.concat(["case[",U32.show(t),",",U32.show(slot),",",U32.show(scrutinee),",",U32.show(m),"](",show(n,Rows{rows}),"|",show(n,Default{default}),")"])
    case 1n+ +n Node{P.Closure{+t,+live,+slots,+captures,+body}}:
      String.concat(["closure[",U32.show(t),",",U32.show(live),",",U32.show(slots),",",numbers(captures),"](",show(n,Node{body}),")"])
    case 1n+ +n Node{P.Invoke{+t,+function,Nil{}}}: String.concat(["invoke[",U32.show(t),"](",show(n,Node{function}),")"])
    case 1n+ +n Node{P.Invoke{+t,+function,+arguments}}:
      String.concat(["invoke[",U32.show(t),"](",show(n,Node{function}),";",show(n,Nodes{arguments}),")"])
    case 1n+ +n Node{P.Foreign{+t,+f,+operands}}: String.concat(["foreign[",U32.show(t),",",U32.show(f),"](",show(n,Nodes{operands}),")"])
    case 1n+ +n Nodes{Nil{}}: ""
    case 1n+ +n Nodes{Con{head,Nil{}}}: show(n,Node{head})
    case 1n+ +n Nodes{Con{head,tail}}: String.concat([show(n,Node{head}),";",show(n,Nodes{tail})])
    case 1n+ +n Rows{Nil{}}: ""
    case 1n+ +n Rows{Con{P.Missing{},Nil{}}}: "-"
    case 1n+ +n Rows{Con{P.Missing{},tail}}: String.concat(["-;",show(n,Rows{tail})])
    case 1n+ +n Rows{Con{P.Branch{+key,+first,+fields,+body},Nil{}}}:
      String.concat(["branch[",U32.show(key),",",U32.show(first),",",U32.show(fields),"](",show(n,Node{body}),")"])
    case 1n+ +n Rows{Con{P.Branch{+key,+first,+fields,+body},tail}}:
      String.concat(["branch[",U32.show(key),",",U32.show(first),",",U32.show(fields),"](",show(n,Node{body}),");",show(n,Rows{tail})])
    case 1n+ +n Default{None{}}: "-"
    case 1n+ +n Default{Some{node}}: show(n,Node{node})

def constructor_line(constructors: List<&2,P.Constructor>) -> String:
  match constructors:
    case Nil{}: ""
    case Con{P.Constructor{name,fields},Nil{}}: String.concat([name,"(",numbers(fields),")"])
    case Con{P.Constructor{name,fields},tail}: String.concat([name,"(",numbers(fields),") ",constructor_line(tail)])

def shape_line(index: U32, shape: P.Shape) -> String:
  match shape:
    case P.Algebraic{name,constructors}: String.concat(["type ",U32.show(index)," algebraic ",name," ",constructor_line(constructors)])
    case P.Arrow{domain,result}: String.concat(["type ",U32.show(index)," arrow ",U32.show(domain)," ",U32.show(result)])
    case P.Erased{domain,result}: String.concat(["type ",U32.show(index)," erased ",U32.show(domain)," ",U32.show(result)])
    case P.Opaque{name}: String.concat(["type ",U32.show(index)," opaque ",name])

def shape_lines(shapes: List<&2,P.Shape>, +index: U32) -> String:
  match shapes:
    case Nil{}: ""
    case Con{head,tail}: String.concat([shape_line(index,head),"\n",shape_lines(tail,U32.add(index,1))])

def function_lines(functions: List<&2,P.Function>, +index: U32) -> String:
  match functions:
    case Nil{}: ""
    case Con{P.Function{name,parameters,result,slots,body},tail}:
      String.concat(["function ",U32.show(index)," ",name," (",numbers(parameters),") ",U32.show(result)," ",U32.show(slots)," ",show(1000000n,Node{body}),"\n",function_lines(tail,U32.add(index,1))])

def plan_text(plan: P.Plan) -> String:
  match plan:
    case P.Plan{entry,representation,shapes,functions}:
      String.concat(["entry ",U32.show(entry),"\nrepresentation ",numbers(representation),"\n",shape_lines(shapes,0),function_lines(functions,0)])

def printed(result: Result<S.Error,P.Plan>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{plan}: IO.print(plan_text(plan))

def recoded_layout(path: String, result: Result<S.Error,Y.Encoded>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{encoded}: CLI.image_sized(path,encoded,16777216)

def recoded(path: String, result: Result<S.Error,P.Plan>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{plan}: recoded_layout(path,Y.layout(1000000n,plan))

type Then is Type:
  Print{}
  Recode{path: String}

def decoded(mode: Then, result: Result<S.Error,List<&2,U32>>) -> IO(Unit):
  match mode result:
    case Print{} Fail{e}: D.fail(e)
    case Recode{path} Fail{e}: D.fail(e)
    case Print{} Done{words}: printed(X.decode(words))
    case Recode{path} Done{words}: recoded(path,X.decode(words))

def bytes_read(mode: Then, result: Result<&1,&1,U32 & String,List<&2,U32>>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{bytes}: decoded(mode,X.words_of(bytes))

def pair_read(mode: Then, pair: File & Result<&1,&1,U32 & String,List<&2,U32>>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    bytes_read(mode,result)

def opened(mode: Then, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,List<&2,U32>>,Unit,File.read_bytes(file,16777220),pair => pair_read(mode,pair))

def planned(+book: C.Book) -> IO(Unit):
  printed(I.erase_tokens(1000000n,book))

def same_plans(left: Result<S.Error,P.Plan>, right: Result<S.Error,P.Plan>) -> IO(Unit):
  match left right:
    case Fail{e} _: D.fail(e)
    case _ Fail{e}: D.fail(e)
    case Done{p} Done{q}:
      S.choose(IO(Unit),String.eq(plan_text(p),plan_text(q)),u => IO.print("Roundtrip\tequal"),u => IO.die(Unit,6,"InternalFailure\timage\troundtrip-differs"))

def compared(+book: C.Book) -> IO(Unit):
  same_plans(I.erase_tokens(1000000n,book),I.recoded(1000000n,book))

def outcome(result: Result<S.Error,P.Plan>) -> String:
  match result:
    case Fail{e}: G.error(e)
    case Done{plan}: "Done"

def answered(+book: C.Book) -> IO(Unit):
  IO.print(String.concat(["erase_tokens\t",outcome(I.erase_tokens(1000000n,book)),"\nrecoded\t",outcome(I.recoded(1000000n,book))]))

def token(text: String) -> S.Token:
  S.Token{text,S.At{0,0,0,0}}

# The book of image-LAWS.bend `flag_book`, its datatype called `name`.
def named_book(name: String) -> C.Book:
  C.Book{[C.Datatype{token(name),True{},[C.Constructor{token("Off"),Nil{}},C.Constructor{token("On"),Nil{}}]}],
    [C.Function{C.Signature{token("main"),Nil{},0},C.Value{token("On"),0,1}}]}

def encoded_words(result: Result<S.Error,Y.Encoded>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{Y.Encoded{records,words}}: IO.print(String.concat(["Encoded\t",U32.show(words)]))

def source_limits() -> D.Limits:
  D.Limits{65536n,512n,512n}

def usage() -> IO(Unit):
  IO.die(Unit,5,"HostFailure\targuments\texpected decode IMAGE | recode IMAGE OUTPUT | plan SOURCE | roundtrip SOURCE | named NAME | answers SOURCE")

def chosen(decode: Bool, plan: Bool, roundtrip: Bool, named: Bool, answers: Bool, path: String) -> IO(Unit):
  match decode plan roundtrip named answers:
    case True{} _ _ _ _: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(Print{},result))
    case False{} True{} _ _ _: D.load(path,source_limits(),book => planned(book))
    case False{} False{} True{} _ _: D.load(path,source_limits(),book => compared(book))
    case False{} False{} False{} True{} _: encoded_words(I.encode(1000000n,named_book(path)))
    case False{} False{} False{} False{} True{}: CLI.image_load(path,D.Limits{4194304n,4096n,4096n},book => answered(book))
    case False{} False{} False{} False{} False{}: usage()

def command(+name: String, path: String) -> IO(Unit):
  chosen(String.eq(name,"decode"),String.eq(name,"plan"),String.eq(name,"roundtrip"),String.eq(name,"named"),String.eq(name,"answers"),path)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{command_name,Con{path,Nil{}}}: command(command_name,path)
    case Con{command_name,Con{path,Con{output,Nil{}}}}:
      S.choose(IO(Unit),String.eq(command_name,"recode"),u =>
        IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(Recode{output},result)),u => usage())
    case _: usage()

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
