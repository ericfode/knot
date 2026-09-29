import Base
import ./BYTE_PROOF.bend as BytesProof
import ./main.bend as B
import ./model.bend as M
import ./LAWS.bend as L

def L.string_right(s):
  match s:
    case SNil{}:
      {==}
    case SCon{+h,+t}:
      %L.string_right(t) : {SCon{h,String.append(t,"")} == SCon{h,_} : String}
      {==}

def L.string_assoc(a,b,c):
  match a:
    case SNil{}:
      {==}
    case SCon{+h,+t}:
      %L.string_assoc(t,b,c) : {SCon{h,String.append(String.append(t,b),c)} == SCon{h,_} : String}
      {==}

def L.flatten_join(a,b):
  match a:
    case Nil{}:
      {==}
    case Con{+h,+t}:
      Equal.trans(String,
        String.append(h,M.flatten(M.join(t,b))),
        String.append(h,String.append(M.flatten(t),M.flatten(b))),
        String.append(String.append(h,M.flatten(t)),M.flatten(b)),
        Equal.cong(String,String,x => String.append(h,x),M.flatten(M.join(t,b)),String.append(M.flatten(t),M.flatten(b)),L.flatten_join(t,b)),
        Equal.sym(String,String.append(String.append(h,M.flatten(t)),M.flatten(b)),String.append(h,String.append(M.flatten(t),M.flatten(b))),L.string_assoc(h,M.flatten(t),M.flatten(b))))

def L.emit_model(t,suffix):
  match t:
    case B.Empty{}:
      {==}
    case B.Chunk{+text}:
      Equal.cong(String,String,x => String.append(x,suffix),text,String.append(text,""),Equal.sym(String,String.append(text,""),text,L.string_right(text)))
    case B.Join{+a,+b}:
      Equal.trans(String,
        B.emit(a,B.emit(b,suffix)),
        String.append(M.flatten(M.chunks(a)),B.emit(b,suffix)),
        String.append(M.flatten(M.join(M.chunks(a),M.chunks(b))),suffix),
        L.emit_model(a,B.emit(b,suffix)),
        Equal.trans(String,
          String.append(M.flatten(M.chunks(a)),B.emit(b,suffix)),
          String.append(M.flatten(M.chunks(a)),String.append(M.flatten(M.chunks(b)),suffix)),
          String.append(M.flatten(M.join(M.chunks(a),M.chunks(b))),suffix),
          Equal.cong(String,String,x => String.append(M.flatten(M.chunks(a)),x),B.emit(b,suffix),String.append(M.flatten(M.chunks(b)),suffix),L.emit_model(b,suffix)),
          Equal.trans(String,
            String.append(M.flatten(M.chunks(a)),String.append(M.flatten(M.chunks(b)),suffix)),
            String.append(String.append(M.flatten(M.chunks(a)),M.flatten(M.chunks(b))),suffix),
            String.append(M.flatten(M.join(M.chunks(a),M.chunks(b))),suffix),
            Equal.sym(String,String.append(String.append(M.flatten(M.chunks(a)),M.flatten(M.chunks(b))),suffix),String.append(M.flatten(M.chunks(a)),String.append(M.flatten(M.chunks(b)),suffix)),L.string_assoc(M.flatten(M.chunks(a)),M.flatten(M.chunks(b)),suffix)),
            Equal.cong(String,String,x => String.append(x,suffix),String.append(M.flatten(M.chunks(a)),M.flatten(M.chunks(b))),M.flatten(M.join(M.chunks(a),M.chunks(b))),Equal.sym(String,M.flatten(M.join(M.chunks(a),M.chunks(b))),String.append(M.flatten(M.chunks(a)),M.flatten(M.chunks(b))),L.flatten_join(M.chunks(a),M.chunks(b)))))))

def L.finish_model(t):
  %L.string_right(M.flatten(M.chunks(t))) : {B.finish(t) == _ : String}
  L.emit_model(t,"")

def L.empty():
  {==}

def L.fragment(s):
  L.string_right(s)

def L.compose(a,b):
  Equal.trans(String,B.finish(B.compose(a,b)),String.append(M.flatten(M.chunks(a)),B.finish(b)),String.append(B.finish(a),B.finish(b)),L.emit_model(a,B.finish(b)),Equal.cong(String,String,x => String.append(x,B.finish(b)),M.flatten(M.chunks(a)),B.finish(a),Equal.sym(String,B.finish(a),M.flatten(M.chunks(a)),L.finish_model(a))))

def L.append(a,s):
  %L.string_right(s) : {B.emit(a,String.append(s,"")) == String.append(B.finish(a),_) : String}
  L.compose(a,B.fragment(s))

def L.character(a,c):
  L.compose(a,B.fragment(SCon{c,SNil{}}))

def L.left_identity(a):
  {==}

def L.right_identity(a):
  {==}

def L.associativity(a,b,c):
  {==}

def L.empty_fragment(a):
  {==}

def L.snapshot(a,s):
  %L.finish_model(a) : {(B.finish(a),B.finish(B.append(a,s))) == (_,String.append(M.flatten(M.chunks(a)),s)) : String & String}
  %L.finish_model(a) : {(B.finish(a),B.finish(B.append(a,s))) == (B.finish(a),String.append(_,s)) : String & String}
  %L.append(a,s) : {(B.finish(a),B.finish(B.append(a,s))) == (B.finish(a),_) : String & String}
  {==}

def L.witness():
  {==}
