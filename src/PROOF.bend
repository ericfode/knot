import Base
import ./LAWS.bend as L

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

def L.generic_header(at):
  {==}

def L.multiple_scrutinees(at,rest):
  {==}

def L.template_binder(at,rest):
  {==}

def L.destructuring_binding(at,fields,rest):
  {==}

def L.local_import(at,rest):
  {==}

def L.hash_import(at,rest):
  {==}
