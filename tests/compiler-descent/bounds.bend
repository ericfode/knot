import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/descent.bend as D
import ../../src/diagnostic.bend as E

def token() -> S.Token:
  S.Token{"bound",S.At{0,0,0,0}}

def chain() -> List<&2,D.Alias>:
  [D.Alias{10,C.Reference{token(),11,0}},D.Alias{11,C.Value{token(),0,1}}]

def cycle() -> List<&2,D.Alias>:
  [D.Alias{10,C.Reference{token(),11,0}},D.Alias{11,C.Reference{token(),10,0}}]

def shape_text(value: D.Shape) -> String:
  match value:
    case D.Variable{level}: String.append("Variable\t",U32.show(level))
    case D.Constructor{type_id,tag,fields}:
      String.concat(["Constructor\t",U32.show(type_id),"\t",U32.show(tag),"\t",Nat.show(List.length(&2,D.Shape,fields))])
    case D.Opaque{}: "Opaque"
    case D.Sequence{items}: String.append("Sequence\t",Nat.show(List.length(&2,D.Shape,items)))

def order_text(order: Cmp) -> String:
  match order:
    case LT{}: "LT"
    case EQ{}: "EQ"
    case GT{}: "GT"

def shape_probe(fuel: Nat, aliases: List<&2,D.Alias>) -> Result<S.Error,String>:
  S.bind(D.Shape,String,D.shape(fuel,C.Reference{token(),10,0},Nil{},aliases),value => Done{shape_text(value)})

def compare_probe(fuel: Nat) -> Result<S.Error,String>:
  S.bind(Cmp,String,D.compare(fuel,D.Variable{0},D.Constructor{0,1,[D.Variable{0}]}),order => Done{order_text(order)})

def columns_probe(fuel: Nat, q: U32) -> Result<S.Error,String>:
  S.bind(Cmp,String,D.columns([C.Parameter{token(),q,0}],[C.Reference{token(),0,0}],0,fuel,Nil{},Nil{}),
    order => Done{order_text(order)})

# Directly violate the internal product mode's parallel-list invariant.
def product_arity() -> Result<S.Error,String>:
  S.bind(D.Product,String,D.run(1n,D.Fields{[D.Variable{0}],Nil{},0,EQ{}}),result => Done{order_text(D.order(result))})

def request(+name: String) -> Result<S.Error,String>:
  S.choose(Result<S.Error,String>,String.eq(name,"shape-zero"),u => shape_probe(0n,Nil{}),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"compare-zero"),u => compare_probe(0n),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"columns-zero"),u => columns_probe(0n,1),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"alias-chain-enough"),u => shape_probe(3n,chain()),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"alias-chain-short"),u => shape_probe(2n,chain()),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"alias-cycle"),u => shape_probe(8n,cycle()),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"compare-enough"),u => compare_probe(3n),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"compare-short"),u => compare_probe(2n),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"product-arity"),u => product_arity(),u =>
  S.choose(Result<S.Error,String>,String.eq(name,"erased-column-zero"),u => columns_probe(0n,0),u =>
    Fail{S.Host{"bounds","unknown-case"}}))))))))))

def print(result: Result<S.Error,String>) -> IO(Unit):
  match result:
    case Fail{+error}: IO.die(Unit,E.status(error),E.error(error))
    case Done{text}: IO.print(text)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{name,Nil{}}: print(request(name))
    case _: print(Fail{S.Host{"bounds","expected case-name"}})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
