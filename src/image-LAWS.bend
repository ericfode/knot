import Base
import ./syntax.bend as S
import ./core.bend as C
import ./image.bend as I
import ./image-plan.bend as P
import ./image-layout.bend as Y
import ./image-decode.bend as X

# The round-trip law of the image increment, on fixed books and plans, and the erasure laws it rests on.
#
#   round trip   encode(b) = Done(w)  implies  decode(w) = erase_tokens(b)    for every book b and fuel   [open, D21]
#
# `erase_tokens` is a projection, not a rewriting of the book: tokens, quantity-0 binders, levels,
# datatype kinds and Type/Data distinctions do not survive, and the result is a Plan (src/image-plan.bend),
# the image's own tree. The law over every book and fuel is required and is not weakened; it has no induction
# proof yet, so it stands as an open claim in src/image-OPEN.bend, where the gate checks it and instantiates it. It is an
# open obligation of D21, recorded in src/SPEC.md and tests/compiler-image/LAW_REVIEW.md, and this file
# is its evidence: the ground instances below, quantified over every source position, and the counterexamples
# of the statement it replaced.
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
def mixed_plan() -> P.Plan:
  P.Plan{0,I.undeclared(),
    [P.Algebraic{"Flag",[P.Constructor{"Off",Nil{}},P.Constructor{"On",Nil{}}]},
     P.Algebraic{"Box",[P.Constructor{"Box",[0]}]},
     P.Algebraic{"Hollow",[P.Constructor{"Hollow",Nil{}}]}],
    [P.Function{"flip",[0],0,1,P.Case{0,0,0,0,[P.Branch{0,1,0,P.Value{0,1}},P.Branch{1,1,0,P.Value{0,0}}],None{}}},
     P.Function{"unbox",[1],0,2,P.Case{0,0,1,0,[P.Branch{0,1,1,P.Reference{0,1}}],None{}}},
     P.Function{"drop",[0],0,1,P.Reference{0,0}},
     P.Function{"main",Nil{},0,2,
       P.Let{0,0,P.Application{0,0,[P.Value{0,1}]},
         P.Let{0,1,P.Value{2,0},
           P.Application{0,2,[P.Application{0,1,[P.Construct{1,0,[P.Reference{0,0}]}]}]}}}}]}

def flag_plan() -> P.Plan:
  P.Plan{0,I.undeclared(),[P.Algebraic{"Flag",[P.Constructor{"Off",Nil{}},P.Constructor{"On",Nil{}}]}],
    [P.Function{"main",Nil{},0,0,P.Value{0,1}}]}

# Erasure, by literal review: a position changes nothing, and the plan is the one written above.
law erase_flag_book:
  for +at: S.At
  {I.erase_tokens(64n,flag_book(at)) == Done{flag_plan()} : Result<S.Error,P.Plan>}

law erase_mixed_book:
  for +at: S.At
  {I.erase_tokens(64n,mixed_book(at)) == Done{mixed_plan()} : Result<S.Error,P.Plan>}

# The round trip on those books: decoding the words of the image gives back the erased plan.
law round_trip_flag_book:
  for +at: S.At
  {I.recoded(64n,flag_book(at)) == I.erase_tokens(64n,flag_book(at)) : Result<S.Error,P.Plan>}

law round_trip_mixed_book:
  for +at: S.At
  {I.recoded(64n,mixed_book(at)) == I.erase_tokens(64n,mixed_book(at)) : Result<S.Error,P.Plan>}

# The same, for any type, tag, slot and result type of a value, a constructor and a reference: the
# encoder and decoder only move those words.
law round_trip_any_value:
  for +at: S.At
  for +type_id: U32
  for +tag: U32
  {I.recoded(64n,C.Book{[flag_type(at)],[C.Function{C.Signature{tok("main",at),Nil{},type_id},C.Value{tok("v",at),type_id,tag}}]})
    == Done{P.Plan{0,I.undeclared(),[P.Algebraic{"Flag",[P.Constructor{"Off",Nil{}},P.Constructor{"On",Nil{}}]}],
        [P.Function{"main",Nil{},type_id,0,P.Value{type_id,tag}}]}} : Result<S.Error,P.Plan>}

# The codec, on plans that no book of this base produces. It carries every form of SPEC section 3:
# literals of each kind, an intrinsic, a foreign leaf, a keys-mode Case with a default, a tag-mode
# Case with a missing row, a closure over a capture and an invoke. decode is the inverse of layout.
def all_forms_plan() -> P.Plan:
  P.Plan{1,I.undeclared(),
    [P.Opaque{"U32"},P.Algebraic{"Flag",[P.Constructor{"Off",Nil{}},P.Constructor{"On",Nil{}}]},P.Erased{4294967295,1},P.Arrow{0,1}],
    [P.Function{"keys",[0],1,2,
       P.Let{1,1,P.Literal{0,P.Constant{0,[7]}},
         P.Case{1,0,0,1,[P.Branch{7,2,0,P.Intrinsic{1,3,[P.Reference{0,0},P.Literal{0,P.Constant{0,[7]}}]}}],Some{P.Value{1,0}}}}},
     P.Function{"strings",Nil{},1,1,
       P.Let{1,0,P.Literal{3,P.Constant{3,[104,105]}},
         P.Case{1,0,3,0,[P.Missing{},P.Branch{1,1,0,P.Foreign{1,1,[P.Reference{3,0}]}}],None{}}}},
     P.Function{"closures",Nil{},3,2,
       P.Closure{3,1,2,[0],P.Invoke{1,P.Reference{3,0},[P.Reference{0,1}]}}},
     P.Function{"main",Nil{},1,0,P.Invoke{1,P.Value{2,0},Nil{}}}]}

law round_trip_all_forms:
  {I.decoded_image(Y.layout(64n,all_forms_plan())) == Done{all_forms_plan()} : Result<S.Error,P.Plan>}

# The first statement of the round trip, `recoded == erase_tokens` at every fuel and book, is false: `encode` gives
# layout the fuel that erasure has, and layout needs more; and layout refuses what erasure accepts (a name that is not
# an identifier, an arity past SPEC section 4). Each law below is a counterexample, erasure answering and the image
# refused. The corrected law (src/image-OPEN.bend) speaks of the fuels and books where encoding answers.
def refusal(result: Result<S.Error,P.Plan>) -> Type:
  match result:
    case Fail{e}: Unit
    case Done{plan}: Empty

# The fuel windows, each fuel a law: erasure answers from 1 (flag_book) and 13 (mixed_book), layout from 3 and 19.
law flag_refuted_at_1:
  for +at: S.At
  {I.recoded(1n,flag_book(at)) != I.erase_tokens(1n,flag_book(at)) : Result<S.Error,P.Plan>}

law flag_refuted_at_2:
  for +at: S.At
  {I.recoded(2n,flag_book(at)) != I.erase_tokens(2n,flag_book(at)) : Result<S.Error,P.Plan>}

law mixed_refuted_at_13:
  for +at: S.At
  {I.recoded(13n,mixed_book(at)) != I.erase_tokens(13n,mixed_book(at)) : Result<S.Error,P.Plan>}

law mixed_refuted_at_14:
  for +at: S.At
  {I.recoded(14n,mixed_book(at)) != I.erase_tokens(14n,mixed_book(at)) : Result<S.Error,P.Plan>}

law mixed_refuted_at_15:
  for +at: S.At
  {I.recoded(15n,mixed_book(at)) != I.erase_tokens(15n,mixed_book(at)) : Result<S.Error,P.Plan>}

law mixed_refuted_at_16:
  for +at: S.At
  {I.recoded(16n,mixed_book(at)) != I.erase_tokens(16n,mixed_book(at)) : Result<S.Error,P.Plan>}

law mixed_refuted_at_17:
  for +at: S.At
  {I.recoded(17n,mixed_book(at)) != I.erase_tokens(17n,mixed_book(at)) : Result<S.Error,P.Plan>}

law mixed_refuted_at_18:
  for +at: S.At
  {I.recoded(18n,mixed_book(at)) != I.erase_tokens(18n,mixed_book(at)) : Result<S.Error,P.Plan>}

def live_parameters(n: Nat, +at: S.At) -> List<&2,C.Parameter>:
  match n:
    case 0n: Nil{}
    case 1n+ +m: Con{C.Parameter{tok("x",at),1,0},live_parameters(m,at)}

# One live parameter more than an image holds: 4,097 against 4,096. The size limit is the same class, observed by the gate.
def wide_book(+at: S.At) -> C.Book:
  C.Book{[flag_type(at)],[C.Function{C.Signature{tok("main",at),live_parameters(4097n,at),0},C.Value{tok("On",at),0,1}}]}

law wide_refuted:
  for +at: S.At
  {I.recoded(64n,wide_book(at)) != I.erase_tokens(64n,wide_book(at)) : Result<S.Error,P.Plan>}

# The book of flag_book, its datatype called `name`.
def named_book(name: String, +at: S.At) -> C.Book:
  C.Book{[C.Datatype{tok(name,at),True{},[C.Constructor{tok("Off",at),Nil{}},C.Constructor{tok("On",at),Nil{}}]}],
    [C.Function{C.Signature{tok("main",at),Nil{},0},C.Value{tok("On",at),0,1}}]}

def accent() -> String:
  SCon{Char.from_u32(233),SNil{}}

def nul() -> String:
  SCon{Char.from_u32(0),SNil{}}

law accent_refuted:
  for +at: S.At
  {I.recoded(64n,named_book(accent(),at)) != I.erase_tokens(64n,named_book(accent(),at)) : Result<S.Error,P.Plan>}

# A name that decode does not read is refused by layout, before any word exists (P.spelled).
law empty_name_is_refused:
  for +at: S.At
  {I.encode(64n,named_book("",at)) == P.unsupported(Y.Encoded,"image-name") : Result<S.Error,Y.Encoded>}

law nul_name_is_refused:
  for +at: S.At
  {I.encode(64n,named_book(nul(),at)) == P.unsupported(Y.Encoded,"image-name") : Result<S.Error,Y.Encoded>}

law wide_name_is_refused:
  for +at: S.At
  {I.encode(64n,named_book(accent(),at)) == P.unsupported(Y.Encoded,"image-name") : Result<S.Error,Y.Encoded>}

# The words of a header spell KIMG, version 1, and an empty file is not an image.
law magic_spells_kimg:
  {[U32.and(P.magic(),255),U32.and(U32.shrn(P.magic(),8n),255),U32.and(U32.shrn(P.magic(),16n),255),U32.shrn(P.magic(),24n)] == [75,73,77,71] : List<U32>}

law empty_file_is_not_an_image:
  {X.decode(Nil{}) == Fail{S.Host{"image","length"}} : Result<S.Error,P.Plan>}

# Erasure laws, over every token, level, type and depth: they hold of the definitions, not of a sample.
law all_erased_constructor_is_a_value:
  for +type_id: U32
  for +tag: U32
  for +deepest: U32
  {I.constructed(I.Lowered{Nil{},Nil{},deepest},type_id,tag) == Done{I.one(P.Value{type_id,tag},deepest)} : Result<S.Error,I.Lowered>}

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
  for +initial: P.Node
  for +result: P.Node
  for +a: U32
  for +b: U32
  for +slot: U32
  {I.bound_let(I.Lowered{Con{initial,Nil{}},Nil{},a},I.Lowered{Con{result,Nil{}},Nil{},b},slot)
    == Done{I.one(P.Let{P.type_of(result),slot,initial,result},I.max_depth(a,b))} : Result<S.Error,I.Lowered>}

law absent_arm_is_a_missing_row:
  for +n: Nat
  for +types: List<&2,C.Datatype>
  for +functions: List<&2,C.Function>
  for +locals: List<&2,I.Local>
  for +depth: U32
  for +key: U32
  {I.lower(1n+n,I.Arm{None{},key},types,functions,locals,depth) == Done{I.Lowered{Nil{},[P.Missing{}],depth}} : Result<S.Error,I.Lowered>}

# A chunk is the low byte of each word first, and a stream of nothing ends.
law chunk_bytes_are_little_endian:
  {Y.pull(Y.Cursor{Nil{},[[16909060]]}) == Y.Chunk{[4,3,2,1],Y.Cursor{Nil{},Nil{}}} : Y.Step}

law empty_stream_ends:
  {Y.pull(Y.Cursor{Nil{},Nil{}}) == Y.End{} : Y.Step}
