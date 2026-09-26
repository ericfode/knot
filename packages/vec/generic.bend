import Base
import ./main.bend as V
import ./observations.bend as O

type Node is Data:
  Node{id: U32, label: String}

def node_eq(a: Node, b: Node) -> Bool:
  match a:
    case Node{i,x}:
      match b:
        case Node{j,y}:
          Bool.and(U32.is_eq(i,j),String.eq(x,y))

def nodes_eq(xs: List<Node>, ys: List<Node>) -> Bool:
  match xs:
    case Nil{}:
      match ys:
        case Nil{}: True{}
        case Con{h,t}: False{}
    case Con{x,xt}:
      match ys:
        case Nil{}: False{}
        case Con{y,yt}: Bool.and(node_eq(x,y),nodes_eq(xt,yt))

def result_ok(pair: V.Vec<Node> & Result<V.Error,Node>) -> Bool:
  (v,r) = pair
  match r:
    case Fail{e}: False{}
    case Done{x}:
      Bool.and(node_eq(x,Node{2,"beta"}),nodes_eq(O.contents(Node,v),[Node{1,"alpha"},Node{9,"λ"},Node{3,"gamma"},Node{4,"delta"},Node{5,"epsilon"}]))

def main() -> Bool:
  v = O.five(Node,Node{1,"alpha"},Node{2,"beta"},Node{3,"gamma"},Node{4,"delta"},Node{5,"epsilon"})
  v = O.vector(Node,V.Vec.reserve(Node,v,17))
  result_ok(V.Vec.swap(Node,v,1,Node{9,"λ"}))
