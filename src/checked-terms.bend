import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E

# Checked terms compose affine uses: disjoint in sequence, union in alternatives.
# Let and branch binders leave the external-use set before composition.
def prepend_argument(head: C.Checked, tail: C.Checked, token: S.Token) -> Result<S.Error,C.Checked>:
  match head tail:
    case C.Checked{+term,type_id,uses} C.Checked{C.Sequence{+items},ignored,rest}:
      S.bind(List<&2,U32>,C.Checked,E.sequential(uses,rest,token),merged => Done{C.Checked{C.Sequence{Con{term,items}},0,merged}})
    case _ _: C.internal(C.Checked,"argument-list")

def let_result(value: C.Checked, body: C.Checked, +token: S.Token, +level: U32, q: U32) -> Result<S.Error,C.Checked>:
  match value body:
    case C.Checked{+initial,+type_id,uses} C.Checked{+result,+result_type,body_uses}:
      S.bind(List<&2,U32>,C.Checked,E.sequential(uses,E.remove(body_uses,level),token),merged =>
        Done{C.Checked{C.Let{token,level,q,type_id,initial,result},result_type,merged}})

def prepend_arm(tag: U32, +fields: List<&2,C.Binding>, head: C.Checked, tail: C.Checked) -> Result<S.Error,C.Checked>:
  match head tail:
    case C.Checked{body,type_id,uses} C.Checked{C.Sequence{items},ignored,rest}:
      Done{C.Checked{C.Sequence{Con{C.Branch{tag,fields,body},items}},0,E.alternatives(E.remove_fields(fields,uses),rest)}}
    case _ _: C.internal(C.Checked,"arm-list")

def case_result(branches: C.Checked, inspected: C.Checked, +token: S.Token, level: U32, wanted: Maybe<&2,U32>) -> Result<S.Error,C.Checked>:
  match branches inspected wanted:
    case C.Checked{C.Sequence{+items},ignored,uses} C.Checked{term,source_type,scrutinee_uses} Some{+type_id}:
      S.bind(List<&2,U32>,C.Checked,E.sequential(scrutinee_uses,uses,token),merged => Done{C.Checked{C.Case{token,level,type_id,items},type_id,merged}})
    case _ _ None{}: C.internal(C.Checked,"uninferred-match")
    case _ _ _: C.internal(C.Checked,"match-result")

def checked_function(signature: C.Signature, checked: C.Checked) -> C.Function:
  match checked:
    case C.Checked{term,type_id,uses}: C.Function{signature,term}
