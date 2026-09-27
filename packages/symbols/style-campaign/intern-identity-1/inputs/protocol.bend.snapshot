import Base

type Command is Data:
  Intern{name: String}
  Find{name: String}
  Resolve{id: U32}
  Length{}
  Limit{}

type Reply is Data:
  Id{id: U32}
  Name{name: String}
  Missing{}
  Invalid{}
  Full{}
  Number{value: U32}

type Observation is Data:
  Observed{reply: Reply, length: U32, limit: U32, names: List<&2,String>}

def reply_eq(a: Reply, b: Reply) -> Bool:
  match a b:
    case Id{x} Id{y}: U32.is_eq(x,y)
    case Name{x} Name{y}: String.eq(x,y)
    case Missing{} Missing{}: True{}
    case Invalid{} Invalid{}: True{}
    case Full{} Full{}: True{}
    case Number{x} Number{y}: U32.is_eq(x,y)
    case _ _: False{}

def names_eq(a: List<&2,String>, b: List<&2,String>) -> Bool:
  match a b:
    case Nil{} Nil{}: True{}
    case Con{x,xs} Con{y,ys}: Bool.and(String.eq(x,y),names_eq(xs,ys))
    case _ _: False{}

def observation_eq(a: Observation, b: Observation) -> Bool:
  match a b:
    case Observed{r,n,l,xs} Observed{s,m,k,ys}:
      Bool.and(reply_eq(r,s),Bool.and(U32.is_eq(n,m),Bool.and(U32.is_eq(l,k),names_eq(xs,ys))))

def trace_eq(a: List<&2,Observation>, b: List<&2,Observation>) -> Bool:
  match a b:
    case Nil{} Nil{}: True{}
    case Con{x,xs} Con{y,ys}: Bool.and(observation_eq(x,y),trace_eq(xs,ys))
    case _ _: False{}
