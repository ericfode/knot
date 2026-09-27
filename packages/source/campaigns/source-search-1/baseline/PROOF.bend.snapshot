import Base
import ./LAWS.bend as Laws
import ./main.bend as S
import ./types.bend as T

def Laws.content_identity(id): {==}
def Laws.file_identity(id): {==}
def Laws.empty_content(id): {==}
def Laws.empty_lines(id): {==}
def Laws.scalar_units(id): {==}
def Laws.indexed_value(): {==}
def Laws.peek_codepoint(): {==}
def Laws.bump_restore_content(): {==}
def Laws.eof_fixed_point(): {==}
def Laws.span_order(): {==}
def Laws.empty_eof_span(): {==}
def Laws.newline_location(): {==}
def Laws.newline_roundtrip(): {==}
def Laws.cr_is_content(): {==}
def Laws.crlf_location(): {==}
def Laws.trailing_line(): {==}
def Laws.canonical_location(): {==}
def Laws.foreign_cursor(): {==}
def Laws.foreign_span(): {==}
def Laws.rejected_span(): {==}
def Laws.rejected_offset(): {==}
def Laws.exhausted_limit(): {==}
def Laws.invalid_scalar(): {==}
def Laws.checked_cursor(s,id,i): {==}

def Laws.accepted_cursor(s,i,valid):
  match s:
    case S.Buffer{id,n,chars,lines}:
      %Equal.sym(Bool,U32.is_le(i,n),True{},valid) : {S.cursor_if(S.Buffer{id,n,chars,lines},T.Cursor{id,i},_) == (S.Buffer{id,n,chars,lines},Done{T.Cursor{id,i}}) : S.Source & Result<T.Error,T.Cursor>}
      {==}

def Laws.rejected_cursor(s,i,invalid):
  match s:
    case S.Buffer{id,n,chars,lines}:
      %Equal.sym(Bool,U32.is_le(i,n),False{},invalid) : {S.cursor_if(S.Buffer{id,n,chars,lines},T.Cursor{id,i},_) == (S.Buffer{id,n,chars,lines},Fail{T.Bounds{}}) : S.Source & Result<T.Error,T.Cursor>}
      {==}

def Laws.accepted_span(s,a,b,valid):
  match s:
    case S.Buffer{id,n,chars,lines}:
      %Equal.sym(Bool,Bool.and(U32.is_le(a,b),U32.is_le(b,n)),True{},valid) : {S.span_if(S.Buffer{id,n,chars,lines},T.Span{id,a,b},_) == (S.Buffer{id,n,chars,lines},Done{T.Span{id,a,b}}) : S.Source & Result<T.Error,T.Span>}
      {==}

def Laws.rejected_span_universal(s,a,b,invalid):
  match s:
    case S.Buffer{id,n,chars,lines}:
      %Equal.sym(Bool,Bool.and(U32.is_le(a,b),U32.is_le(b,n)),False{},invalid) : {S.span_if(S.Buffer{id,n,chars,lines},T.Span{id,a,b},_) == (S.Buffer{id,n,chars,lines},Fail{T.InvalidRange{}}) : S.Source & Result<T.Error,T.Span>}
      {==}

def Laws.foreign_restore(s,foreign,i,different):
  match s:
    case S.Buffer{id,n,chars,lines}:
      %Equal.sym(Bool,U32.is_eq(foreign,id),False{},different) : {S.restore_if(S.Buffer{id,n,chars,lines},i,_) == (S.Buffer{id,n,chars,lines},Fail{T.ForeignFile{}}) : S.Source & Result<T.Error,T.Cursor>}
      {==}
def Laws.inhabited_cursor_domain(): {==}
def Laws.inhabited_span_domain(): {==}
def Laws.maximum_policy(): {==}
