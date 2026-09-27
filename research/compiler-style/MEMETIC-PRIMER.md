# Hold the unfinished future

An author-written reading specimen, 2026-09-26. This tests the leading hypothesis
in [the theory proposal](MEMETIC-THEORY.md). It is not a finished style, a user
preference, a new implementation or a three-axis pass. The Bend excerpts are
copied from existing source; explanatory equations are labeled separately.
The runner is another owner's staged candidate, preserved here as a quotation.
The [evidence snapshot](memetic-theory-evidence-2026-09-26.json) pins all six code
excerpts, their source hashes and whether they match committed HEAD. This
documentation increment does not commit that owner's source change.

## Work survives the end of its time slice

Imagine holding a computation halfway through. You have its current value, the
work still pending and the destination of the answer. Giving it time moves it
forward. Running out of time returns what remains.

The current [task representation](../adaptive-tasks/task.bend) makes that
distinction explicit:

```bend
type Task is Type:
  Work{destination: U32, remaining: Nat, payload: Payload, frames: List<&1,Frame>}

type Run is Type:
  Checkpoint{task: Task}
  Delivered{destination: U32, payload: Payload}
```

This task owns its payload and captured frames. It is not a reusable snapshot.
Its current implementation performs a bounded word computation and applies saved
unary/binary frames. General closures and compiler-generated GPU execution remain
future work.

Now read the [current runner candidate](../adaptive-tasks/task.bend):

```bend
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 1n+n Checkpoint{task}: run(n,step(task))
    case _ _: state
```

Fuel and unfinished work advance together. Every other pairing returns the
state. Once you know that pairing, you can predict both boundaries: zero fuel
preserves the residual owner, and a delivered answer stays delivered.

The catchall compresses those two boundaries, which also makes them less explicit.
That reading tradeoff remains open. This candidate's memetic rating is uncertain.

## A pause becomes a change of grouping

Here is the next recognition to aim for. If a time slice returns all the work
still owed, the next slice can continue it. The existing
[fuel-composition law](../adaptive-tasks/LAWS.bend) is:

```bend
law fuel_add:
  for n: Nat
  for m: Nat
  for r: T.Run
  {T.run(m,T.run(n,r)) == T.run(Nat.add(n,m),r) : T.Run}
```

In explanatory notation, with natural-number fuel:

```text
run(m, run(n, r)) = run(n + m, r)
```

The [inductive proof](../adaptive-tasks/PROOF.bend) follows the pending-work step:

```bend
def L.fuel_add(n,m,r):
  match n r:
    case 0n _: {==}
    case 1n+k T.Checkpoint{task}:
      L.fuel_add(k,m,T.step(task))
    case 1n+k T.Delivered{d,p}:
      L.delivered_absorbs(m,d,p)
```

The desired experience is that understanding the runner helps you anticipate its
proof. This equation concerns the defined sequential task machine. It does not
by itself establish arbitrary scheduler equivalence, parallel determinism or
host/device transport correctness.

## A refused handoff returns what was offered

The [owning slot](../adaptive-tasks/slot.bend) supplies another place to use the
same discipline. Its result includes either an inserted slot or the occupied
slot together with the incoming value:

```bend
type Put<-T: Type> is Type:
  Inserted{slot: Slot<T>}
  Rejected{slot: Slot<T>, value: T}
```

```bend
def put(-T: Type, s: Slot<T>, x: T) -> Put<T>:
  match s:
    case Vacant{}: Inserted{Occupied{x}}
    case Occupied{value}: Rejected{Occupied{value},x}
```

Rejection keeps both facts visible: the old occupant and the offer that could
not be accepted. The proposed shared motif is to look for what each transition
still owes its caller. That is a local contract; Bend's affine usage permits
discarding, and these examples do not establish universal resource conservation
or general destructor behavior.

## Three ways to read the same source

| Treatment | What it makes salient | What a third example must demonstrate |
| --- | --- | --- |
| Conservation | Which owner crosses each boundary, and what returns on refusal | An explicit disposal operation retains the right distinctions |
| Hold the unfinished future | The caller can possess and continue what remains | A new suspension or handoff can be expressed without obscuring captures or lifetime |
| Lawful transformation | Moving between equivalent groupings makes new operations intelligible | Another operation and its law share a useful structure without sharing an oracle |

My current preference is the second reading. The other two provide essential
precision. This comparison changes the framing of existing code; it has not yet
demonstrated a better source form. The next specimen must make the identity work
in actual expressions even when this surrounding prose is removed.

The transfer challenge should expose that distinction: show two operations,
provide the complete contract for a third, then see what someone writes and
wants to retain. Success requires both a usable grammar and an appetite to use
it. Neither response has been observed yet.
