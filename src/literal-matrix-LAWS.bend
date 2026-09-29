import Base
import ./syntax.bend as S
import ./literal-matrix.bend as M

law offset_zero:
  for token: S.Token
  for +tail: S.Token
  {M.literal(S.Offset{token,0,S.Variable{tail}}) == S.Variable{tail} : S.Node}

law offset_successor:
  for +token: S.Token
  for +tail: S.Node
  {M.literal(S.Offset{token,1,tail}) ==
    S.Constructor{M.retoken("Succ",token),[S.Offset{token,0,tail}]} : S.Node}

law natural_successor:
  for +token: S.Token
  {M.literal(S.Literal{token,1,2,Nil{}}) ==
    S.Constructor{M.retoken("Succ",token),[S.Literal{token,1,1,Nil{}}]} : S.Node}

law string_successor:
  for +token: S.Token
  {M.literal(S.Literal{token,3,0,[55357,56832]}) ==
    S.Constructor{M.retoken("SCon",token),[S.Literal{token,2,55357,Nil{}},S.Literal{token,3,0,[56832]}]} : S.Node}

law word_order:
  for +token: S.Token
  for +body: S.Node
  {M.words([M.Row{[S.Literal{token,0,9,Nil{}}],body,Nil{}},
    M.Row{[S.Literal{token,0,9,Nil{}}],body,Nil{}},M.Row{[S.Literal{token,0,2,Nil{}}],body,Nil{}}],Nil{}) == [9,2] : List<&2,U32>}
