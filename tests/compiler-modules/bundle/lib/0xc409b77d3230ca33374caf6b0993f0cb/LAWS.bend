import Base
import ./main.bend as B
import ./model.bend as M

# Auxiliary string/list algebra, universal.
law string_right:
  for +s: String
  {String.append(s, "") == s : String}

law string_assoc:
  for +a: String
  for +b: String
  for +c: String
  {String.append(String.append(a,b),c) == String.append(a,String.append(b,c)) : String}

law flatten_join:
  for +a: List<&2,String>
  for +b: List<&2,String>
  {M.flatten(M.join(a,b)) == String.append(M.flatten(a),M.flatten(b)) : String}

# Universal refinement, including an arbitrary suffix.
law emit_model:
  for +t: B.Builder
  for +suffix: String
  {B.emit(t,suffix) == String.append(M.flatten(M.chunks(t)),suffix) : String}

law finish_model:
  for +t: B.Builder
  {B.finish(t) == M.flatten(M.chunks(t)) : String}

law empty:
  {B.finish(B.empty()) == "" : String}

law fragment:
  for +s: String
  {B.finish(B.fragment(s)) == s : String}

law compose:
  for +a: B.Builder
  for +b: B.Builder
  {B.finish(B.compose(a,b)) == String.append(B.finish(a),B.finish(b)) : String}

law append:
  for +a: B.Builder
  for +s: String
  {B.finish(B.append(a,s)) == String.append(B.finish(a),s) : String}

law character:
  for +a: B.Builder
  for +c: Char
  {B.finish(B.character(a,c)) == String.append(B.finish(a),SCon{c,SNil{}}) : String}

law left_identity:
  for +a: B.Builder
  {B.finish(B.compose(B.empty(),a)) == B.finish(a) : String}

law right_identity:
  for +a: B.Builder
  {B.finish(B.compose(a,B.empty())) == B.finish(a) : String}

law associativity:
  for +a: B.Builder
  for +b: B.Builder
  for +c: B.Builder
  {B.finish(B.compose(B.compose(a,b),c)) == B.finish(B.compose(a,B.compose(b,c))) : String}

law empty_fragment:
  for +a: B.Builder
  {B.finish(B.append(a,"")) == B.finish(a) : String}

# Both old and new observations, not merely old == old.
law snapshot:
  for +a: B.Builder
  for +s: String
  {(B.finish(a),B.finish(B.append(a,s))) ==
   (M.flatten(M.chunks(a)),String.append(M.flatten(M.chunks(a)),s)) : String & String}

# Inhabited normalization witness: empty, nonempty, Unicode, LF, CR, NUL.
law witness:
  {B.finish(B.character(B.compose(B.append(B.fragment("λ"),""),B.fragment("🙂\r\n")),Chr{0})) == "λ🙂\r\n\0" : String}
