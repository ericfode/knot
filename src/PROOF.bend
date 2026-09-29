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

def L.no_character_budget(c,tail):
  {==}

def L.no_parser_budget(tokens):
  {==}

def L.generic_header(at,rest):
  {==}

def L.multiple_scrutinees(at,rest):
  {==}

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

def L.binding_type_application(at,rest):
  {==}

def L.local_import(at,rest):
  {==}

def L.hash_import(at,rest):
  {==}

def L.malformed_name(at): {==}

def L.name_shapes(): {==}

def L.dotted_binder_needs_a_parameter(at): {==}

def L.dotted_binder_repeats_a_parameter(at): {==}

def L.dotted_reference_binds_nothing(at): {==}

def L.offset_tail_after_newline(rest): {==}

def L.list_across_lines(at,rest): {==}

def L.arm_across_lines(at): {==}

def L.cases_right_of_parent(at,rest): {==}
