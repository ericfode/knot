import Base
import ./LAWS.bend as L
import ./syntax.bend as S
import ./parse.bend as P

def L.empty_source(fuel):
  match fuel:
    case 0n: {==}
    case 1n+n: {==}

def L.word_source(extra):
  match extra:
    case 0n: {==}
    case 1n+n: {==}

def L.name_words_witness(): {==}

def L.malformed_word_source(extra):
  match extra:
    case 0n: {==}
    case 1n+n: {==}

def L.no_character_budget(c,tail):
  {==}

def L.no_parser_budget(tokens):
  {==}

def L.generic_header(at,rest):
  {==}

def L.comma_scrutinees(at): {==}

def L.multiple_scrutinees(at):
  {==}

def L.header_joins_lines(at,rest): {==}

def L.touches_witness(): {==}

def L.touching_brace(pattern,x,y,z,rest,touch):
  match pattern:
    case True{}:
      Equal.cong(Bool,Result<S.Error,P.Parsed>,found =>
        S.choose(Result<S.Error,P.Parsed>,found,
          u => P.then(P.run(1n,P.Arguments{"}",True{}},Con{S.Token{"}",z},rest}),
            args => after => P.wrap_call(S.Token{"On",x},True{},args,after)),
          u => P.invalid(Con{S.Token{"{",y},Con{S.Token{"}",z},rest}},"detached-brace")),
        S.touches(S.Token{"On",x},S.Token{"{",y}),True{},touch)
    case False{}:
      Equal.cong(Bool,Result<S.Error,P.Parsed>,found =>
        S.choose(Result<S.Error,P.Parsed>,found,
          u => P.then(P.run(1n,P.Arguments{"}",False{}},Con{S.Token{"}",z},rest}),
            args => after => P.wrap_call(S.Token{"On",x},True{},args,after)),
          u => P.invalid(Con{S.Token{"{",y},Con{S.Token{"}",z},rest}},"detached-brace")),
        S.touches(S.Token{"On",x},S.Token{"{",y}),True{},touch)

def L.detached_brace(pattern,x,y,rest,gap):
  match pattern:
    case True{}:
      Equal.cong(Bool,Result<S.Error,P.Parsed>,found =>
        S.choose(Result<S.Error,P.Parsed>,found,
          u => P.then(P.run(0n,P.Arguments{"}",True{}},rest),
            args => after => P.wrap_call(S.Token{"On",x},True{},args,after)),
          u => P.invalid(Con{S.Token{"{",y},rest},"detached-brace")),
        S.touches(S.Token{"On",x},S.Token{"{",y}),False{},gap)
    case False{}:
      Equal.cong(Bool,Result<S.Error,P.Parsed>,found =>
        S.choose(Result<S.Error,P.Parsed>,found,
          u => P.then(P.run(0n,P.Arguments{"}",False{}},rest),
            args => after => P.wrap_call(S.Token{"On",x},True{},args,after)),
          u => P.invalid(Con{S.Token{"{",y},rest},"detached-brace")),
        S.touches(S.Token{"On",x},S.Token{"{",y}),False{},gap)

def L.joined_brace_witness(): {==}

def L.marks_witness(): {==}

def L.detached_plus(keyword,pattern,parent,column,rest): {==}

def L.line_broken_scrutinees_witness(): {==}

def L.detached_marker(rest): {==}

def L.first_marker(rest): {==}

def L.dotted_pattern_binder(at,rest): {==}

def L.dotted_promotion_binder(at,rest): {==}

def L.dotted_let_binder(at,rest): {==}

def L.dotted_typed_let_binder(at,rest): {==}

def L.unnamed_binder_is_invalid(at,rest): {==}

def L.line_break_in_arguments(at,rest): {==}

def L.line_break_after_element(at,head,rest): {==}

def L.same_line_arm(at,value,rest): {==}

def L.body_ends_at_line_break(at,value,rest): {==}

def L.template_binder(at,rest):
  {==}

def L.nonleading_template_binder(at,head,rest):
  {==}

def L.destructuring_binding(at,fields,rest,plain):
  %Equal.sym(Bool,Bool.or(P.starts(rest,"="),P.starts(rest,">")),False{},plain) :
    {S.choose(Result<S.Error,P.Parsed>,_,
      u => P.body_end(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},rest}),
      u => P.unsupported(Con{S.Token{"=",at},rest},"destructuring-binding"))
      == Fail{S.Unsupported{"parse","destructuring-binding",at}} : Result<S.Error,P.Parsed>}
  {==}

def L.equality_is_not_binding(at,fields,rest):
  {==}

def L.arrow_is_not_binding(at,fields,rest):
  {==}

def L.parameter_type_application(at,rest):
  {==}

def L.return_type_application(at,rest):
  {==}

def L.split_arrow(at,rest): {==}

def L.binding_type_application(at,rest):
  {==}

def L.local_import(at,rest):
  {==}

def L.hash_import(at,rest):
  {==}

def L.numeral_witness(): {==}

def L.statement_witness(): {==}

def L.numeral_column_is_unsupported(at,rest): {==}

def L.same_line_statement(at,rest): {==}

def L.let_ends_at_line_break(at,rest): {==}

def L.split_before_colon_witness(): {==}
