import Base
import ./syntax.bend as S

type Constructor is Data:
  Constructor{token: S.Token, fields: List<&2,Parameter>}
type Datatype is Data:
  Datatype{token: S.Token, reusable: Bool, constructors: List<&2,Constructor>}
type Parameter is Data:
  Parameter{token: S.Token, quantity: U32, type_id: U32}
type Signature is Data:
  Signature{token: S.Token, parameters: List<&2,Parameter>, result: U32}
type Catalog is Data:
  Catalog{types: List<&2,Datatype>, signatures: List<&2,Signature>}

# Levels identify binders independently of display names. Branch scopes may
# reuse levels. Branch and Sequence are internal traversal containers only.
type Term is Data:
  Value{token: S.Token, type_id: U32, tag: U32}
  Reference{token: S.Token, level: U32, type_id: U32}
  Application{token: S.Token, index: U32, type_id: U32, arguments: List<&2,Term>}
  Let{token: S.Token, level: U32, quantity: U32, type_id: U32, value: Term, body: Term}
  Case{token: S.Token, level: U32, type_id: U32, arms: List<&2,Term>}
  Branch{tag: U32, body: Term}
  Sequence{items: List<&2,Term>}
type Function is Data:
  Function{signature: Signature, body: Term}
type Book is Data:
  Book{types: List<&2,Datatype>, functions: List<&2,Function>}
type Binding is Data:
  Binding{token: S.Token, level: U32, quantity: U32, type_id: U32, parameter: Bool, known: Maybe<&2,U32>}
type Checked is Data:
  Checked{term: Term, type_id: U32, uses: List<&2,U32>}

def invalid(-A: Type, code: String, token: S.Token) -> Result<S.Error,A>:
  Fail{S.Invalid{"check",code,S.at(token)}}
def unsupported(-A: Type, code: String, token: S.Token) -> Result<S.Error,A>:
  Fail{S.Unsupported{"check",code,S.at(token)}}
def exhausted(-A: Type, token: S.Token) -> Result<S.Error,A>:
  Fail{S.Exhausted{"check",S.at(token)}}
def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"check",code}}
