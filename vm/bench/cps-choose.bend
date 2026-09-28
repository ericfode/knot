import Base

# The lexer's shape (src/lex.bend normal): a chain of choose calls whose two
# branches are closures over the scanner state, about 16 per character.
type Mode is Data:
  Blank{}
  Comment{}
  Word{length: U32}

type Tally is Data:
  Tally{mode: Mode, words: U32, lines: U32}

def choose(-A: Type, condition: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def ended(mode: Mode, +words: U32) -> U32:
  match mode:
    case Word{n}: U32.add(words,1)
    case _: words

def grown(mode: Mode) -> Mode:
  match mode:
    case Word{n}: Word{U32.add(n,1)}
    case _: Word{1}

def normal(+code: U32, +mode: Mode, +words: U32, +lines: U32) -> Result<U32,Tally>:
  choose(Result<U32,Tally>,U32.is_eq(code,10),u =>
    Done{Tally{Blank{},ended(mode,words),U32.add(lines,1)}},u =>
  choose(Result<U32,Tally>,U32.is_eq(code,32),u =>
    Done{Tally{Blank{},ended(mode,words),lines}},u =>
  choose(Result<U32,Tally>,U32.is_eq(code,35),u =>
    Done{Tally{Comment{},ended(mode,words),lines}},u =>
  choose(Result<U32,Tally>,Bool.or(U32.is_eq(code,9),U32.is_eq(code,13)),u =>
    Fail{1},u =>
  choose(Result<U32,Tally>,Bool.or(U32.is_eq(code,34),U32.is_eq(code,39)),u =>
    Fail{2},u =>
  choose(Result<U32,Tally>,U32.is_gt(code,126),u =>
    Fail{3},u =>
  choose(Result<U32,Tally>,U32.is_lt(code,32),u =>
    Fail{4},u =>
    Done{Tally{grown(mode),words,lines}})))))))

def step(c: Char, tally: Tally) -> Result<U32,Tally>:
  match tally:
    case Tally{Comment{},+words,+lines}:
      +code = Char.to_u32(c)
      choose(Result<U32,Tally>,U32.is_eq(code,10),u => normal(code,Comment{},words,lines),u =>
        Done{Tally{Comment{},words,lines}})
    case Tally{mode,words,lines}: normal(Char.to_u32(c),mode,words,lines)

def run(text: String, result: Result<U32,Tally>) -> Result<U32,Tally>:
  match text result:
    case SCon{c,rest} Done{tally}: run(rest,step(c,tally))
    case _ r: r

def text(k: Nat, acc: String) -> String:
  match k:
    case 0n: acc
    case 1n+p: text(p,String.append("let value = 42 # note\n",acc))

# Each 22-character line holds four words and one comment.
def verdict(result: Result<U32,Tally>) -> Bool:
  match result:
    case Done{Tally{mode,words,lines}}: Bool.and(U32.is_eq(words,200000),U32.is_eq(lines,50000))
    case Fail{code}: False{}

# Every pass rescans the same 1.1M characters.
def passes(k: Nat, +text: String, hits: U32) -> U32:
  match k:
    case 0n: hits
    case 1n+p: passes(p,text,U32.add(hits,Bool.pick(U32,verdict(run(text,Done{Tally{Blank{},0,0}})),1,0)))

def main() -> Bool:
  U32.is_eq(passes(8n,text(50000n,""),0),8)
