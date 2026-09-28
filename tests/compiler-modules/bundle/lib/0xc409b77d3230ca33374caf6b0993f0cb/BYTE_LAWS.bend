import Base
import ./bytes.bend as B
import ./byte_model.bend as M

# Auxiliary list algebra, universal.
law list_right:
  for +s: List<&2,U32>
  {List.append(&2,U32,s, Nil{}) == s : List<&2,U32>}

law list_assoc:
  for +a: List<&2,U32>
  for +b: List<&2,U32>
  for +c: List<&2,U32>
  {List.append(&2,U32,List.append(&2,U32,a,b),c) == List.append(&2,U32,a,List.append(&2,U32,b,c)) : List<&2,U32>}

law flatten_join:
  for +a: List<&2,List<&2,U32>>
  for +b: List<&2,List<&2,U32>>
  {M.flatten(M.join(a,b)) == List.append(&2,U32,M.flatten(a),M.flatten(b)) : List<&2,U32>}

# Universal refinement, including an arbitrary suffix.
law emit_model:
  for +t: B.Tree
  for +suffix: List<&2,U32>
  {B.emit(t,suffix) == List.append(&2,U32,M.flatten(M.chunks(t)),suffix) : List<&2,U32>}

law finish_model:
  for +t: B.Tree
  for +cap: U32
  for +n: U32
  {B.finish(B.Buffer{cap,n,t}) == M.flatten(M.chunks(t)) : List<&2,U32>}

# Concrete normalization, including capacity zero, overflow and invalid bytes.
law empty:
  {B.finish(B.empty(0)) == [] : List<&2,U32>}

law content:
  {M.observe(B.append(B.empty(4),[0,127,128,255])) == Done{([0,127,128,255],4)} : Result<B.Error,List<&2,U32> & U32>}

law invalid:
  {M.observe(B.byte(B.empty(4),256)) == Fail{B.InvalidByte{256}} : Result<B.Error,List<&2,U32> & U32>}

law full:
  {M.observe(B.byte(B.empty(0),0)) == Fail{B.Limit{}} : Result<B.Error,List<&2,U32> & U32>}

law compose_content:
  {M.observe(B.compose(B.Buffer{4,2,B.Chunk{[0,97]}},B.Buffer{2,2,B.Chunk{[255,10]}})) == Done{([0,97,255,10],4)} : Result<B.Error,List<&2,U32> & U32>}

law overflow:
  {B.combine(U32.is_le(1,U32.sub(4294967295,4294967295)),4294967295,4294967295,1,B.Empty{},B.Empty{}) == Fail{B.Limit{}} : Result<B.Error,B.Builder>}
