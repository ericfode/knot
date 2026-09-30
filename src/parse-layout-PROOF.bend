import Base
import ./syntax.bend as S
import ./parse.bend as P
import ./parse-layout-LAWS.bend as L

def L.datatype_colon_layout(n,name,at,rest):
  {==}

def L.generic_colon_layout(n,name,params,at,body):
  match body:
    case Nil{}: {==}
    case Con{head,Nil{}}: {==}
    case Con{head,Con{next,tail}}: {==}

def L.result_arrow_layout(n,name,at,rest):
  {==}

def L.parameters_layout(n,close,at,rest):
  {==}

def L.parameter_tail_layout(n,close,head,at,rest):
  {==}

def L.nonleading_template_layout(n,head,at,mark,rest):
  {==}

def L.declaration_name_layout(n,at,name,rest):
  {==}

def L.named_header_close_gap(name,q,rest):
  {==}
