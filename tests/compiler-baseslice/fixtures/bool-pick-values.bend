import Base

type Flag is Data:
  Off{}
  On{}

type Seen is Data:
  TypeOpener{}
  DataOpener{}
  SignedLimit{}
  UnsignedLimit{}
  ParameterMode{}
  ArgumentMode{}

# parse.bend's Mode: a fielded type chosen by Bool.pick.
type Mode is Data:
  Parameters{close: String}
  Arguments{close: String, pattern: Bool}

def bool(f: Flag) -> Bool:
  match f:
    case Off{}: False{}
    case On{}: True{}

def opener_seen(data: Bool) -> Seen:
  match data:
    case False{}: TypeOpener{}
    case True{}: DataOpener{}

def limit_seen(signed: Bool) -> Seen:
  match signed:
    case False{}: UnsignedLimit{}
    case True{}: SignedLimit{}

def mode_seen(m: Mode) -> Seen:
  match m:
    case Parameters{close}: ParameterMode{}
    case Arguments{close, pattern}: ArgumentMode{}

# diagnostic.bend: Bool.pick(String, reusable, " Data(", " Type(").
def opener(reusable: Flag) -> Seen:
  opener_seen(String.eq(Bool.pick(String, bool(reusable), " Data(", " Type("), " Data("))

# wasm-bytes.groups: Bool.pick(U32, signed, 64, 128).
def limit(signed: Flag) -> Seen:
  limit_seen(U32.is_eq(Bool.pick(U32, bool(signed), 64, 128), 64))

# parse.run: Bool.pick(Mode, parameters, Parameters{close}, Arguments{close, pattern}).
def mode(parameters: Flag) -> Seen:
  +close : String = ")"
  mode_seen(Bool.pick(Mode, bool(parameters), Parameters{close}, Arguments{close, False{}}))

def main() -> Seen:
  opener(On{})
