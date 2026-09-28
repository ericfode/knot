import Base
import ./syntax.bend as S
import ./base-pin.bend as H

# Concrete encoding/padding boundaries and verification results, not a crypto theorem.
law word_is_big_endian:
  {H.word(18,52,86,120) == 305419896 : U32}

law octets_are_big_endian:
  {H.octets(305419896) == [18,52,86,120] : List<&2,U32>}

law rotate_keeps_wrapped_bit:
  {H.rotate(2147483649,1n,31n) == 3221225472 : U32}

law zeros_preserve_suffix:
  for +tail: List<&2,U32>
  {H.zeros(3n,tail) == Con{0,Con{0,Con{0,tail}}} : List<&2,U32>}

law abc_padding_keeps_bytes_and_bit_length:
  {H.padded(3,[99,98,97]) ==
    [97,98,99,128,0,0,0,0,0,0,0,0,0,0,0,0,
     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,24] : List<&2,U32>}

law fifty_five_bytes_fit_one_block:
  {List.length(&2,U32,H.padded(55,H.zeros(55n,Nil{}))) == 64n : Nat}

law fifty_six_bytes_need_two_blocks:
  {List.length(&2,U32,H.padded(56,H.zeros(56n,Nil{}))) == 128n : Nat}

law complete_block_still_gets_padding:
  {List.length(&2,U32,H.padded(64,H.zeros(64n,Nil{}))) == 128n : Nat}

law second_block_keeps_bit_length:
  {List.drop(&2,U32,H.padded(56,H.zeros(56n,Nil{})),120n) == [0,0,0,0,0,0,1,192] : List<&2,U32>}

law digest_keeps_word_order_and_leading_zeros:
  {H.show(H.Digest{0,1,2,3,4,5,6,4294967295}) ==
    "00000000000000010000000200000003000000040000000500000006ffffffff" : String}

law matching_pin_preserves_text:
  for +text: String
  {H.verified(text,Done{H.expected()}) == Done{text} : Result<S.Error,String>}

law wrong_pin_is_host_failure:
  for text: String
  {H.verified(text,Done{"0000000000000000000000000000000000000000000000000000000000000000"}) ==
    Fail{S.Host{"load","base-pin"}} : Result<S.Error,String>}

law hash_failure_is_preserved:
  for text: String
  for +error: S.Error
  {H.verified(text,Fail{error}) == Fail{error} : Result<S.Error,String>}

law non_ascii_pin_is_host_failure:
  {H.ascii(SCon{Char.from_u32(128),SNil{}},0,Nil{}) == Fail{S.Host{"load","base-pin"}} : Result<S.Error,H.Digest>}

law byte_limit_is_checked_before_absorption:
  for tail: String
  for reversed: List<&2,U32>
  {H.ascii(SCon{'a',tail},131072,reversed) == Fail{S.Host{"load","base-pin"}} : Result<S.Error,H.Digest>}
