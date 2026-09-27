# Knot shapes

The pattern sheet for Knot's Bend. A **shape** is a recurring form: a fixed
silhouette that keeps its identity while the vocabulary changes. A **figure** is
one bounded mechanism that instantiates shapes: a datatype, its lead recurrence,
its projections, its laws, its proof fills and one use, declared in a manifest
under `docs/style-campaign/figures/`. Style identity is judged at the figure,
against this sheet. Supporting declarations earn their place by instantiating a
shape exactly. The lead and the figure earn theirs by making the shape teach:
after the lead and one law, the reader anticipates the proof and the next
operation.

Every shape below is drawn from code already in the repository. Skeletons use
placeholder names in capitals; instances are exact declarations. Nothing here
is earned by a comment naming the shape. The form has to be visible in the
clauses, the types and the laws.

## Conventions the sheet fixes

- The recursion argument comes first in a joint match: `match fuel state`.
- Stop arms come first and are named; the advancing arm comes last. A catch-all
  never merges two distinct stopping reasons.
- A transition returns the whole owner it still owes, in the same position
  every time: `(store, result)`, `Rejected{slot, value}`.
- Two operations that share a descent share one spine; they differ only in the
  policy passed down.
- Laws follow their mechanisms in the same order. An equation puts operation,
  result and type on three successive lines.
- A proof fill follows the same case split as the mechanism it proves.

## S1 Fuel-first machine

Give a computation time; get back its answer or the work still owed.

```bend
def run(fuel: Nat, state: S) -> S:
  match fuel state:
    case 0n _: state
    case 1n+n Pending{work}: run(n,step(work))
    case 1n+n Terminal{..}: Terminal{..}
```

Fixed: fuel first; zero fuel returns the complete residual owner; terminals
ignore fuel; exactly one arm advances and recurses on the smaller fuel.
Varies: the state datatype, the step, the number of terminal constructors.

Law shape: `run(0,r) = r`; `run(n,Terminal) = Terminal`;
`run(m,run(n,r)) = run(n+m,r)`.

Instances: `research/adaptive-tasks/task.bend::run`, `src/eval.bend::run`,
`src/parse.bend::run`, `src/check.bend::run`, `packages/source/main.bend::search`,
`packages/vec/main.bend::plan_step`.

Next move the reader expects: a `slices` or `run_many` that regroups fuel, and a
`fuel_add` law whose proof splits on the same two arms.

## S2 Residual owner with absorbing terminals

The state datatype has one pending constructor holding everything still owed,
and terminal constructors that no step can leave.

```bend
type Run is Type:
  Checkpoint{task: Task}
  Delivered{destination: U32, payload: Payload}
```

Fixed: the pending constructor owns the complete continuation; a terminal
carries only its result; observing consumes the owner. Varies: how many
terminals, what a checkpoint holds.

Law shape: `run(n,Delivered{d,p}) = Delivered{d,p}`; a terminal search state
ignores fuel.

Instances: `research/adaptive-tasks/task.bend::Run`,
`packages/source/main.bend::Search` with `Searching`, `Found`, `BadIndex`,
`src/eval.bend::State` with `Return{value,Nil{}}` as the absorbing arm.

## S3 Owner-returning outcome

Every transition returns what it still owes its caller: the store it was
given back, and on refusal the offer that could not be accepted.

```bend
type Put<-T: Type> is Type:
  Inserted{slot: Slot<T>}
  Rejected{slot: Slot<T>, value: T}

def put(-T: Type, s: Slot<T>, x: T) -> Put<T>:
  match s:
    case Vacant{}: Inserted{Occupied{x}}
    case Occupied{value}: Rejected{Occupied{value},x}
```

Fixed: the owner is in the first position of every outcome; refusal keeps both
the old occupant and the offer visible; nothing is silently dropped.
Varies: pair `(store, result)` or a named outcome datatype.

Law shape: `put(Occupied{x},y) = Rejected{Occupied{x},y}`;
`take(put_slot(put(Vacant,x))) = Extracted{Vacant,x}`.

Instances: `research/adaptive-tasks/slot.bend::put` and `take`,
`packages/vec/main.bend::push_ready` returning `Vec<T> & Result<Error,Unit>`,
`packages/symbols/main.bend::Trie.get` returning `Trie & Maybe<&2,U32>`,
`packages/symbols/main.bend::Table.intern` returning `Table & Result<Error,U32>`.

## S4 Spine edit

One descent, parameterised by what happens at the end and how each level is
rebuilt. Two operations differ only in the policy they pass down.

```bend
def edit_path(~join: @-T: Data -> IntMap<T> -> IntMap<T> -> IntMap<T>,
              -V: Data, path: List<&2,Bool>, +m: IntMap<V>, end: IntMap<V>) -> IntMap<V>:
  match path:
    case Nil{}: end
    case Con{False{},tail}: join(V,edit_path(~join,V,tail,low(V,m),end),high(V,m))
    case Con{True{},tail}: join(V,low(V,m),edit_path(~join,V,tail,high(V,m),end))

def set_path(...): edit_path(~(T => lo => hi => Branch{lo,hi}),V,path,m,Entry{key,v})
def remove_path(...): edit_path(~branch,V,path,m,Tip{})
```

Fixed: the path grammar is shared by lookup and edit; the endpoint and the
rebuild are the only policies; the untouched sibling is passed through.
Varies: the key encoding, the rebuild constructor, the endpoint value.

Law shape: `get(set(m,k,v),k) = Some{v}`; `get(remove(m,k),k) = None{}`;
`remove` prunes only through its rebuild policy.

Instances: `packages/int_map/main.bend::edit_path` with `set_path` and
`remove_path`, `src/scope.bend::set_known` with `refine` and `replace`,
`packages/symbols/main.bend::Trie.rejoin` rebuilding one child position.

## S5 Three-way pivot

A comparison fans into three continuations that each rebuild the context in
the same position, so lookup and insertion read as the same figure.

```bend
({\{
  LT: Trie.rejoin(child => Fork{color,pivot,child,same,more},Trie.get(less,SCon{Chr{char},tail}));
  EQ: Trie.rejoin(child => Fork{color,pivot,less,child,more},Trie.get(same,tail));
  GT: Trie.rejoin(child => Fork{color,pivot,less,same,child},Trie.get(more,SCon{Chr{char},tail}))
} : Cmp -> Trie & Maybe<&2,U32>})(U32.cmp(char,pivot))
```

Fixed: LT, EQ, GT in that order; each arm rebuilds exactly one child position;
EQ consumes the matched element, LT and GT keep it. Varies: the rebuilt
constructor, what the EQ arm does at the end of the key.

Law shape: strict sibling order and equal black height hold after every insert.

Instances: `packages/symbols/main.bend::Trie.get` and `Trie.insert`.

## S6 First-error composition

Stages are named in order inside one expression; the first failure wins; the
IO continuation stays outermost.

```bend
checked(
  S.bind(List<&2,S.Token>,C.Book,L.tokenize(chars,text),tokens =>
    S.bind(P.Parsed,C.Book,P.parse(parser,tokens),tree =>
      K.check(checker,parsed_root(tree)))),
  next)
```

Fixed: one `bind` per stage; the bound name is the stage's output; the final
stage returns the result type directly. Varies: the number of stages, the
error type.

Law shape: `bind(Fail{e},k) = Fail{e}`; `bind(Done{x},k) = k(x)`.

Instances: `src/driver.bend::source`, `src/eval.bend::run`, the `then` chains
in `src/parse.bend::run`, `packages/output_builder/bytes.bend::join`.

## S7 One-exception constructor

A smart constructor states its single exception and passes every other input
through unchanged.

```bend
def branch(-V: Data, lo: IntMap<V>, hi: IntMap<V>) -> IntMap<V>:
  match lo hi:
    case Tip{} Tip{}: Tip{}
    case a b: Branch{a,b}
```

Fixed: exactly one exception arm, then one pass-through arm. Varies: what the
exception normalises.

Law shape: `branch(Tip,Tip) = Tip`; `branch(a,b) = Branch{a,b}` otherwise.

Instances: `packages/int_map/main.bend::branch`,
`packages/symbols/main.bend::Trie.black`, the stopping arm of
`packages/vec/main.bend::plan_step`.

## S8 Law and proof mirror

The proof fill follows the same case split as the mechanism, so understanding
the operational rule also unlocks its composition rule.

```bend
law fuel_add:
  for n: Nat
  for m: Nat
  for r: T.Run
  {T.run(m,T.run(n,r))
   == T.run(Nat.add(n,m),r)
   : T.Run}

def L.fuel_add(n,m,r):
  match n r:
    case 0n _: {==}
    case 1n+k T.Checkpoint{task}: L.fuel_add(k,m,T.step(task))
    case 1n+k T.Delivered{d,p}: L.delivered_absorbs(m,d,p)
```

Fixed: the law's equation sits on three lines; the proof's arms are the
mechanism's arms; a canonical `{==}` fill stays `{==}`. Varies: which earlier
law each arm appeals to.

Instances: `research/adaptive-tasks/PROOF.bend::L.fuel_add` mirroring
`task.bend::run`, `src/check-LAWS.bend` equations for `E.sequential` and
`E.occurrence`.

## Reading a figure

A figure passes the sheet when a fluent reader can name its shapes from the
code alone, the lead makes the shape teach the next operation, the laws sit in
the mechanism's order, and the proofs mirror the mechanism. A supporting
declaration passes when it instantiates one shape exactly in the sheet's
layout. Variation is welcome when the sheet predicts it; a new shape is welcome
when two figures in different vocabularies need it. Adding a shape to this
sheet requires those two instances.
