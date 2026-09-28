import Base
import ./literal-LAWS.bend as L
import ./syntax.bend as S

def L.div_zero(x): {==}
def L.rem_zero(x): {==}
def L.shl_wide(x,n,wide):
  Equal.cong(Bool,U32,b => S.choose(U32,b,u => 0,u => U32.shln(x,U32.to_nat(n))),U32.is_ge(n,32),True{},wide)
def L.shr_wide(x,n,wide):
  Equal.cong(Bool,U32,b => S.choose(U32,b,u => 0,u => U32.shrn(x,U32.to_nat(n))),U32.is_ge(n,32),True{},wide)
def L.wide_boundary(): {==}
def L.append_order(): {==}
def L.length_count(): {==}
def L.equal_length(): {==}
def L.surrogate_code(token): {==}
def L.surrogate_sequence(token): {==}
def L.scalar_sequence(token): {==}
def L.decimal_maximum(token): {==}
def L.decimal_overflow(token): {==}
def L.signed_bits(): {==}
def L.nul_is_a_character(token): {==}
def L.legacy_literal_boundary(token): {==}
