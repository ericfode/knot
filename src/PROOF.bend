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
