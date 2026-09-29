import Base
import ./syntax.bend as S
import ./core.bend as C
import ./image.bend as I

# The round-trip law of the image increment, and the erasure laws it rests on.
#
#   round trip   decode(encode(b)) = erase_tokens(b)    for every checked book b        [open, D21]
#
# `erase_tokens` is a projection, not a rewriting of the book: tokens, quantity-0 binders, levels,
# datatype kinds and Type/Data distinctions do not survive, and the result is a Plan (src/image.bend),
# the image's own tree. The general law is required and is not weakened. It has no induction proof
# yet, so it is recorded as an open obligation in src/SPEC.md and the increment's LAW_REVIEW, with its
# evidence: the ground instances below, quantified over every source position, the golden-image and
# frozen-suite gates, and mutants. An open law would fail this file's gate, so the general statement
# stays in this comment:
#
#   law round_trip:
#     for fuel: Nat
#     for book: C.Book
#     {I.recoded(fuel,book) == I.erase_tokens(fuel,book) : Result<S.Error,I.Plan>}
#
# The books here are fixed, as the literal review of `erase_tokens` is: the plans are written by hand
# from vm/SPEC.md sections 1 and 3, before they were compared with the encoder's answer.

def tok(text: String, +at: S.At) -> S.Token:
  S.Token{text,at}

def flag_type(+at: S.At) -> C.Datatype:
  C.Datatype{tok("Flag",at),True{},[C.Constructor{tok("Off",at),Nil{}},C.Constructor{tok("On",at),Nil{}}]}

def flag_book(+at: S.At) -> C.Book:
  C.Book{[flag_type(at)],[C.Function{C.Signature{tok("main",at),Nil{},0},C.Value{tok("On",at),0,1}}]}

# Flag; Box{-proof, item}, whose first field is erased; Hollow{-proof}, whose only field is erased.
# flip takes its arms in source order, On before Off; unbox binds Box's live field and drops the
# erased one; drop has an erased parameter and an erased let; main calls each, with an erased
# argument and an all-erased constructor.
def mixed_types(+at: S.At) -> List<&2,C.Datatype>:
  [flag_type(at),
   C.Datatype{tok("Box",at),True{},[C.Constructor{tok("Box",at),[C.Parameter{tok("proof",at),0,0},C.Parameter{tok("item",at),1,0}]}]},
   C.Datatype{tok("Hollow",at),True{},[C.Constructor{tok("Hollow",at),[C.Parameter{tok("proof",at),0,0}]}]}]

def flip(+at: S.At) -> C.Function:
  C.Function{C.Signature{tok("flip",at),[C.Parameter{tok("x",at),1,0}],0},
    C.Case{tok("x",at),0,0,[C.Branch{1,Nil{},C.Value{tok("Off",at),0,0}},C.Branch{0,Nil{},C.Value{tok("On",at),0,1}}]}}

def unbox(+at: S.At) -> C.Function:
  C.Function{C.Signature{tok("unbox",at),[C.Parameter{tok("b",at),1,1}],0},
    C.Case{tok("b",at),0,0,[C.Branch{0,[C.Binding{tok("p",at),1,0,0,True{},None{}},C.Binding{tok("x",at),2,1,0,True{},None{}}],C.Reference{tok("x",at),2,0}}]}}

def discard(+at: S.At) -> C.Function:
  C.Function{C.Signature{tok("drop",at),[C.Parameter{tok("p",at),0,0},C.Parameter{tok("x",at),1,0}],0},
    C.Let{tok("y",at),2,0,0,C.Reference{tok("p",at),0,0},C.Reference{tok("x",at),1,0}}}

def mixed_main(+at: S.At) -> C.Function:
  C.Function{C.Signature{tok("main",at),Nil{},0},
    C.Let{tok("f",at),0,1,0,C.Application{tok("flip",at),0,0,[C.Value{tok("On",at),0,1}]},
      C.Let{tok("h",at),1,1,2,C.Construct{tok("Hollow",at),2,0,[C.Parameter{tok("proof",at),0,0}],[C.Value{tok("Off",at),0,0}]},
        C.Application{tok("drop",at),2,0,[C.Value{tok("Off",at),0,0},
          C.Application{tok("unbox",at),1,0,[C.Construct{tok("Box",at),1,0,[C.Parameter{tok("proof",at),0,0},C.Parameter{tok("item",at),1,0}],[C.Value{tok("Off",at),0,0},C.Reference{tok("f",at),0,0}]}]}]}}}}

def mixed_book(+at: S.At) -> C.Book:
  C.Book{mixed_types(at),[flip(at),unbox(at),discard(at),mixed_main(at)]}

# The plan of mixed_book, by hand. Rows are in tag order whatever the order of the arms; a live
# binder takes the next slot, an erased one none; a Let's type is its body's; the erased argument, the
# erased field, the erased let and the erased parameter are gone; Hollow{Off} is the value Hollow.
def mixed_plan() -> I.Plan:
  I.Plan{0,I.undeclared(),
    [I.Algebraic{"Flag",[I.Constructor{"Off",Nil{}},I.Constructor{"On",Nil{}}]},
     I.Algebraic{"Box",[I.Constructor{"Box",[0]}]},
     I.Algebraic{"Hollow",[I.Constructor{"Hollow",Nil{}}]}],
    [I.Function{"flip",[0],0,1,I.Case{0,0,0,0,[I.Branch{0,1,0,I.Value{0,1}},I.Branch{1,1,0,I.Value{0,0}}],None{}}},
     I.Function{"unbox",[1],0,2,I.Case{0,0,1,0,[I.Branch{0,1,1,I.Reference{0,1}}],None{}}},
     I.Function{"drop",[0],0,1,I.Reference{0,0}},
     I.Function{"main",Nil{},0,2,
       I.Let{0,0,I.Application{0,0,[I.Value{0,1}]},
         I.Let{0,1,I.Value{2,0},
           I.Application{0,2,[I.Application{0,1,[I.Construct{1,0,[I.Reference{0,0}]}]}]}}}}]}

def flag_plan() -> I.Plan:
  I.Plan{0,I.undeclared(),[I.Algebraic{"Flag",[I.Constructor{"Off",Nil{}},I.Constructor{"On",Nil{}}]}],
    [I.Function{"main",Nil{},0,0,I.Value{0,1}}]}

# Erasure, by literal review: a position changes nothing, and the plan is the one written above.
law erase_flag_book:
  for +at: S.At
  {I.erase_tokens(64n,flag_book(at)) == Done{flag_plan()} : Result<S.Error,I.Plan>}

law erase_mixed_book:
  for +at: S.At
  {I.erase_tokens(64n,mixed_book(at)) == Done{mixed_plan()} : Result<S.Error,I.Plan>}

# The round trip on those books: decoding the words of the image gives back the erased plan.
law round_trip_flag_book:
  for +at: S.At
  {I.recoded(64n,flag_book(at)) == I.erase_tokens(64n,flag_book(at)) : Result<S.Error,I.Plan>}

law round_trip_mixed_book:
  for +at: S.At
  {I.recoded(64n,mixed_book(at)) == I.erase_tokens(64n,mixed_book(at)) : Result<S.Error,I.Plan>}

# The same, for any type, tag, slot and result type of a value, a constructor and a reference: the
# encoder and decoder only move those words.
law round_trip_any_value:
  for +at: S.At
  for +type_id: U32
  for +tag: U32
  {I.recoded(64n,C.Book{[flag_type(at)],[C.Function{C.Signature{tok("main",at),Nil{},type_id},C.Value{tok("v",at),type_id,tag}}]})
    == Done{I.Plan{0,I.undeclared(),[I.Algebraic{"Flag",[I.Constructor{"Off",Nil{}},I.Constructor{"On",Nil{}}]}],
        [I.Function{"main",Nil{},type_id,0,I.Value{type_id,tag}}]}} : Result<S.Error,I.Plan>}

# The codec, on plans that no book of this base produces. It carries every form of SPEC section 3:
# literals of each kind, an intrinsic, a foreign leaf, a keys-mode Case with a default, a tag-mode
# Case with a missing row, a closure over a capture and an invoke. decode is the inverse of layout.
def all_forms_plan() -> I.Plan:
  I.Plan{1,I.undeclared(),
    [I.Opaque{"U32"},I.Algebraic{"Flag",[I.Constructor{"Off",Nil{}},I.Constructor{"On",Nil{}}]},I.Erased{4294967295,1},I.Arrow{0,1}],
    [I.Function{"keys",[0],1,2,
       I.Let{1,1,I.Literal{0,I.Constant{0,[7]}},
         I.Case{1,0,0,1,[I.Branch{7,2,0,I.Intrinsic{1,3,[I.Reference{0,0},I.Literal{0,I.Constant{0,[7]}}]}}],Some{I.Value{1,0}}}}},
     I.Function{"strings",Nil{},1,1,
       I.Let{1,0,I.Literal{3,I.Constant{3,[104,105]}},
         I.Case{1,0,3,0,[I.Missing{},I.Branch{1,1,0,I.Foreign{1,1,[I.Reference{3,0}]}}],None{}}}},
     I.Function{"closures",Nil{},3,2,
       I.Closure{3,1,2,[0],I.Invoke{1,I.Reference{3,0},[I.Reference{0,1}]}}},
     I.Function{"main",Nil{},1,0,I.Invoke{1,I.Value{2,0},Nil{}}}]}

law round_trip_all_forms:
  {I.decoded_image(I.layout(64n,all_forms_plan())) == Done{all_forms_plan()} : Result<S.Error,I.Plan>}

# The words of a header spell KIMG, version 1, and an empty file is not an image.
law magic_spells_kimg:
  {[U32.and(I.magic(),255),U32.and(U32.shrn(I.magic(),8n),255),U32.and(U32.shrn(I.magic(),16n),255),U32.shrn(I.magic(),24n)] == [75,73,77,71] : List<U32>}

law empty_file_is_not_an_image:
  {I.decode(Nil{}) == Fail{S.Host{"image","length"}} : Result<S.Error,I.Plan>}

# Erasure laws, over every token, level, type and depth: they hold of the definitions, not of a sample.
law all_erased_constructor_is_a_value:
  for +type_id: U32
  for +tag: U32
  for +deepest: U32
  {I.constructed(I.Lowered{Nil{},Nil{},deepest},type_id,tag) == Done{I.one(I.Value{type_id,tag},deepest)} : Result<S.Error,I.Lowered>}

law erased_let_is_its_body:
  for +n: Nat
  for +types: List<&2,C.Datatype>
  for +functions: List<&2,C.Function>
  for +locals: List<&2,I.Local>
  for +depth: U32
  for +token: S.Token
  for +level: U32
  for +type_id: U32
  for +value: C.Term
  for +body: C.Term
  {I.lower(1n+n,I.Term{C.Let{token,level,0,type_id,value,body}},types,functions,locals,depth)
    == I.lower(n,I.Term{body},types,functions,Con{I.Local{level,0,type_id,False{}},locals},depth) : Result<S.Error,I.Lowered>}

law erased_operand_is_dropped:
  for +n: Nat
  for +types: List<&2,C.Datatype>
  for +functions: List<&2,C.Function>
  for +locals: List<&2,I.Local>
  for +depth: U32
  for +term: C.Term
  for +terms: List<&2,C.Term>
  for +token: S.Token
  for +type_id: U32
  for +parameters: List<&2,C.Parameter>
  {I.lower(1n+n,I.Operands{Con{term,terms},Con{C.Parameter{token,0,type_id},parameters}},types,functions,locals,depth)
    == I.lower(n,I.Operands{terms,parameters},types,functions,locals,depth) : Result<S.Error,I.Lowered>}

law let_takes_its_bodys_type:
  for +initial: I.Node
  for +result: I.Node
  for +a: U32
  for +b: U32
  for +slot: U32
  {I.bound_let(I.Lowered{Con{initial,Nil{}},Nil{},a},I.Lowered{Con{result,Nil{}},Nil{},b},slot)
    == Done{I.one(I.Let{I.type_of(result),slot,initial,result},I.max_depth(a,b))} : Result<S.Error,I.Lowered>}

law absent_arm_is_a_missing_row:
  for +n: Nat
  for +types: List<&2,C.Datatype>
  for +functions: List<&2,C.Function>
  for +locals: List<&2,I.Local>
  for +depth: U32
  for +key: U32
  {I.lower(1n+n,I.Arm{None{},key},types,functions,locals,depth) == Done{I.Lowered{Nil{},[I.Missing{}],depth}} : Result<S.Error,I.Lowered>}

# A chunk is the low byte of each word first, and a stream of nothing ends.
law chunk_bytes_are_little_endian:
  {I.pull(I.Cursor{Nil{},[[16909060]]}) == I.Chunk{[4,3,2,1],I.Cursor{Nil{},Nil{}}} : I.Step}

law empty_stream_ends:
  {I.pull(I.Cursor{Nil{},Nil{}}) == I.End{} : I.Step}
