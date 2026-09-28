# The driver.bend opened and read_pair shape: Act.bind at Both(Handle,Res<&1,&1,Both(Code,Flag),Color>), a partial read_pair, a Pack inside Fail.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}
  Gray{}

type Code is Data:
  Missing{}
  Denied{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Handle is Type:
  Handle{id: Flag}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

type Dep<a, b, -A: Kind(a), -B: @-x: A -> Kind(b)> is Kind(a <&> b):
  Pack{fst: A, snd: B(fst)}

type Op<-R: Type> is Type:
  Emit{value: R}
  Halt{code: Fault}

def Both(-A: Type, -B: Type) -> Type:
  Dep<&1,&1,A,_ => B>

def Act(-A: Type) -> Type:
  @-R: Type ->
  @k: (A -> Op<R>) ->
  Op<R>

def Act.pure(-A: Type, x: A) -> Act(A):
  R => k => k(x)

def Act.bind(-A: Type, -B: Type, m: Act(A), f: A -> Act(B)) -> Act(B):
  R => k => m(R,x => f(x,R,k))

def Act.die(-A: Type, code: Fault) -> Act(A):
  R => k => Halt{code}

def fault(code: Code, message: Flag) -> Fault:
  match code:
    case Missing{}: Invalid{}
    case Denied{}:
      match message:
        case Off{}: Invalid{}
        case On{}: Unsupported{}

def read(h: Handle, f: Flag, g: Flag) -> Act(Both(Handle,Res<&1,&1,Both(Code,Flag),Color>)):
  match f:
    case Off{}: Act.pure(Both(Handle,Res<&1,&1,Both(Code,Flag),Color>),Pack{h,Fail{Pack{Denied{},g}}})
    case On{}: Act.pure(Both(Handle,Res<&1,&1,Both(Code,Flag),Color>),Pack{h,Done{Blue{}}})

def read_result(result: Res<&1,&1,Both(Code,Flag),Color>, depth: Flag) -> Act(Color):
  match result:
    case Fail{Pack{code,message}}: Act.die(Color,fault(code,message))
    case Done{c}:
      match depth:
        case Off{}: Act.pure(Color,c)
        case On{}: Act.pure(Color,Red{})

def read_pair(depth: Flag, pair: Both(Handle,Res<&1,&1,Both(Code,Flag),Color>)) -> Act(Color):
  Pack{handle,result} = pair
  read_result(result,depth)

def opened(depth: Flag, f: Flag, g: Flag) -> Act(Color):
  Act.bind(Both(Handle,Res<&1,&1,Both(Code,Flag),Color>),Color,read(Handle{On{}},f,g),read_pair(depth))

def settle(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{Invalid{}}: Gray{}
    case Halt{Unsupported{}}: Red{}

def run(depth: Flag, f: Flag, g: Flag) -> Color:
  settle(opened(depth,f,g,Color,c => Emit{c}))

def main() -> Color:
  run(Off{},On{},Off{})
