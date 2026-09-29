import Base
import ./bytes.bend as B
import ./byte_model.bend as M
import ./BYTE_LAWS.bend as L

def L.list_right(s):
  match s:
    case Nil{}:
      {==}
    case Con{+h,+t}:
      %L.list_right(t) : {Con{h,List.append(&2,U32,t,Nil{})} == Con{h,_} : List<&2,U32>}
      {==}

def L.list_assoc(a,b,c):
  match a:
    case Nil{}:
      {==}
    case Con{+h,+t}:
      %L.list_assoc(t,b,c) : {Con{h,List.append(&2,U32,List.append(&2,U32,t,b),c)} == Con{h,_} : List<&2,U32>}
      {==}

def L.flatten_join(a,b):
  match a:
    case Nil{}:
      {==}
    case Con{+h,+t}:
      Equal.trans(List<&2,U32>,
        List.append(&2,U32,h,M.flatten(M.join(t,b))),
        List.append(&2,U32,h,List.append(&2,U32,M.flatten(t),M.flatten(b))),
        List.append(&2,U32,List.append(&2,U32,h,M.flatten(t)),M.flatten(b)),
        Equal.cong(List<&2,U32>,List<&2,U32>,x => List.append(&2,U32,h,x),M.flatten(M.join(t,b)),List.append(&2,U32,M.flatten(t),M.flatten(b)),L.flatten_join(t,b)),
        Equal.sym(List<&2,U32>,List.append(&2,U32,List.append(&2,U32,h,M.flatten(t)),M.flatten(b)),List.append(&2,U32,h,List.append(&2,U32,M.flatten(t),M.flatten(b))),L.list_assoc(h,M.flatten(t),M.flatten(b))))

def L.emit_model(t,suffix):
  match t:
    case B.Empty{}:
      {==}
    case B.Chunk{+text}:
      Equal.cong(List<&2,U32>,List<&2,U32>,x => List.append(&2,U32,x,suffix),text,List.append(&2,U32,text,Nil{}),Equal.sym(List<&2,U32>,List.append(&2,U32,text,Nil{}),text,L.list_right(text)))
    case B.Join{+a,+b}:
      Equal.trans(List<&2,U32>,
        B.emit(a,B.emit(b,suffix)),
        List.append(&2,U32,M.flatten(M.chunks(a)),B.emit(b,suffix)),
        List.append(&2,U32,M.flatten(M.join(M.chunks(a),M.chunks(b))),suffix),
        L.emit_model(a,B.emit(b,suffix)),
        Equal.trans(List<&2,U32>,
          List.append(&2,U32,M.flatten(M.chunks(a)),B.emit(b,suffix)),
          List.append(&2,U32,M.flatten(M.chunks(a)),List.append(&2,U32,M.flatten(M.chunks(b)),suffix)),
          List.append(&2,U32,M.flatten(M.join(M.chunks(a),M.chunks(b))),suffix),
          Equal.cong(List<&2,U32>,List<&2,U32>,x => List.append(&2,U32,M.flatten(M.chunks(a)),x),B.emit(b,suffix),List.append(&2,U32,M.flatten(M.chunks(b)),suffix),L.emit_model(b,suffix)),
          Equal.trans(List<&2,U32>,
            List.append(&2,U32,M.flatten(M.chunks(a)),List.append(&2,U32,M.flatten(M.chunks(b)),suffix)),
            List.append(&2,U32,List.append(&2,U32,M.flatten(M.chunks(a)),M.flatten(M.chunks(b))),suffix),
            List.append(&2,U32,M.flatten(M.join(M.chunks(a),M.chunks(b))),suffix),
            Equal.sym(List<&2,U32>,List.append(&2,U32,List.append(&2,U32,M.flatten(M.chunks(a)),M.flatten(M.chunks(b))),suffix),List.append(&2,U32,M.flatten(M.chunks(a)),List.append(&2,U32,M.flatten(M.chunks(b)),suffix)),L.list_assoc(M.flatten(M.chunks(a)),M.flatten(M.chunks(b)),suffix)),
            Equal.cong(List<&2,U32>,List<&2,U32>,x => List.append(&2,U32,x,suffix),List.append(&2,U32,M.flatten(M.chunks(a)),M.flatten(M.chunks(b))),M.flatten(M.join(M.chunks(a),M.chunks(b))),Equal.sym(List<&2,U32>,M.flatten(M.join(M.chunks(a),M.chunks(b))),List.append(&2,U32,M.flatten(M.chunks(a)),M.flatten(M.chunks(b))),L.flatten_join(M.chunks(a),M.chunks(b)))))))

def L.finish_model(t,cap,n):
  %L.list_right(M.flatten(M.chunks(t))) : {B.finish(B.Buffer{cap,n,t}) == _ : List<&2,U32>}
  L.emit_model(t,Nil{})

def L.empty():
  {==}

def L.content():
  {==}

def L.invalid():
  {==}

def L.full():
  {==}

def L.compose_content():
  {==}

def L.overflow():
  {==}
