# Twin of fuel-four-columns: a Scope pattern stands in the catalog column.
import Base

type Level is Type:
  Starved{}
  Unbound{}
  Mismatch{}
  Fine{}

type Want is Data:
  Num{}
  Fun{}

type Node is Data:
  Var{}
  Lit{}
  Call{arg: Node}

type Mode is Data:
  Expr{node: Node, wanted: Want}
  Arg{node: Node}

type Catalog is Data:
  Catalog{strict: Bool}

type Scope is Data:
  Scope{bound: Bool}

type Term is Type:
  TVar{}
  TLit{}
  TCall{}
  TNest{}

type Setting is Data:
  Loose{}
  Strict{}
  Empty{}

def run(fuel: Nat, mode: Mode, +catalog: Catalog, +scope: Scope) -> Level:
  match fuel mode catalog scope:
    case 0n _ _ _: Starved{}
    case 1n+ +n Expr{Var{},_} _ Scope{False{}}: Unbound{}
    case 1n+ +n Expr{Var{},Num{}} _ _: Fine{}
    case 1n+ +n Expr{Var{},Fun{}} _ _: Mismatch{}
    case 1n+ +n Expr{Lit{},Fun{}} Scope{True{}} _: Mismatch{}
    case 1n+ +n Expr{Lit{},_} _ _: Fine{}
    case 1n+ +n Expr{Call{arg},Num{}} _ _: run(n,Arg{arg},catalog,scope)
    case 1n+ +n Expr{Call{arg},Fun{}} _ _: Mismatch{}
    case 1n+ +n Arg{node} _ _: run(n,Expr{node,Fun{}},catalog,scope)

def node(t: Term) -> Node:
  match t:
    case TVar{}: Var{}
    case TLit{}: Lit{}
    case TCall{}: Call{Lit{}}
    case TNest{}: Call{Call{Var{}}}

def catalog(s: Setting) -> Catalog:
  match s:
    case Loose{}: Catalog{False{}}
    case Strict{}: Catalog{True{}}
    case Empty{}: Catalog{False{}}

def scope(s: Setting) -> Scope:
  match s:
    case Loose{}: Scope{True{}}
    case Strict{}: Scope{True{}}
    case Empty{}: Scope{False{}}

def probe(t: Term, +s: Setting) -> Level:
  run(4n,Expr{node(t),Num{}},catalog(s),scope(s))

def main() -> Level:
  probe(TCall{},Strict{})
