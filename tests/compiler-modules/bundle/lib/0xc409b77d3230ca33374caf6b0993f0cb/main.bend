import Base

type Builder is Data:
  Empty{}
  Chunk{text: String}
  Join{left: Builder, right: Builder}

def empty() -> Builder:
  Empty{}

def fragment(text: String) -> Builder:
  Chunk{text}

def compose(left: Builder, right: Builder) -> Builder:
  Join{left, right}

def append(builder: Builder, text: String) -> Builder:
  Join{builder, Chunk{text}}

def character(builder: Builder, char: Char) -> Builder:
  Join{builder, Chunk{SCon{char, SNil{}}}}

# Internal suffix traversal. Copies each fragment exactly once.
def emit(builder: Builder, suffix: String) -> String:
  match builder:
    case Empty{}:
      suffix
    case Chunk{text}:
      String.append(text, suffix)
    case Join{left, right}:
      emit(left, emit(right, suffix))

def finish(builder: Builder) -> String:
  emit(builder, SNil{})
