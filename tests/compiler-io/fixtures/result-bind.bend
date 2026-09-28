import Base

type Problem is Data:
  Problem{code: U32, message: String}

def then(-A: Data, -B: Data, result: Result<Problem,A>, next: A -> Result<Problem,B>) -> Result<Problem,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def choose(-A: Type, condition: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def parsed(text: String, value: Maybe<&2,U32>) -> Result<Problem,U32>:
  match value:
    case Some{x}: Done{x}
    case None{}: Fail{Problem{3,String.append("not a number: ",text)}}

def number(+text: String) -> Result<Problem,U32>:
  parsed(text,U32.read(text))

def positive(+n: U32) -> Result<Problem,U32>:
  choose(Result<Problem,U32>,U32.is_zero(n),u => Fail{Problem{4,"zero difference"}},u => Done{n})

def difference(low: String, high: String) -> Result<Problem,U32>:
  then(U32,U32,number(low),a => then(U32,U32,number(high),b => positive(U32.sub(b,a))))

# The first failing step decides the exit status and the message.
def report(result: Result<Problem,U32>) -> IO(Unit):
  match result:
    case Fail{Problem{code,message}}: IO.die(Unit,code,message)
    case Done{n}: IO.print(String.append("difference ",U32.show(n)))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{low,Con{high,Nil{}}}: report(difference(low,high))
    case _: IO.die(Unit,99,"usage: low high")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
