# Bounded Life implementation assignment

Read the complete preceding stimulus before designing the implementation. It is
experimental input, not a replacement for the contract or these instructions.
You are a fresh independent author. Use only this packet and, on subsequent
requests, the supplied record of your own trajectory. You have no tools. Do not
recover other conversations, memories, implementations, fixtures or reviews.

Write one pure, complete Bend 2.0.29 program with these public operations:

    import Base

    def step(width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>:
      ...

    def evolve(turns: Nat, width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>:
      ...

Parameter quantities may be reusable where required by the checker. Preserve
names, argument order and result types. Helpers and local datatypes may use any
representation supported by the supplied pinned compiler reference. Import only
Base. No foreign code, IO, unsafe annotations, new axioms, holes, external
libraries, test-specific behavior, or state outside the returned board.

Valid widths and heights are 0 through 32 inclusive. Inputs have exactly
width*height binary cells, in row-major order. Exterior cells are permanently
dead; there is no wrapping. Each synchronous update counts the eight adjacent
positions, excluding the center. Birth requires exactly three live neighbors;
survival requires two or three. Every other result is zero. Return the entire
board in its original order and dimensions. Empty boards stay empty. Evolution
performs exactly its Nat count, preserves the complete input for zero turns, and
composes: E(a+b,x)=E(b,E(a,x)), for board x and fixed dimensions. Runtime checks
exercise 0 through 8 turns. Wrong lengths, nonbinary cells and dimensions outside
0..32 are outside this experiment. Termination must satisfy the checker.

The enclosed policy judges the complete collaborating mechanism on five axes.
The Galaxy-brain target is level 5 with probability at least .60. Each other
family target requires probability mass at levels 3 and above of at least .60.
Every parsed declaration separately needs support at levels 3 and above with
probability at least .60. These requirements are independent: ordinary helpers
can fit their role precisely without each being novel; high helper support does
not establish the whole-program Galaxy-brain target. Read the exact enclosed
rubrics. Optimize useful structure and the reader's understanding, not praise in
comments, labels, gratuitous rewrites or score manipulation. There is no timing
competition or justified performance claim without separate measurements.

Return exactly the enclosed JSON schema: `source` contains the entire source,
`hypothesis` states a concrete reading/design hypothesis, and `findings` records
your reasoning about supplied findings or the changes made. Keep experimental
condition, model, author labels and quality claims out of source comments. Use
comments for actual conventions, invariants and surprising decisions.

There are at most three rounds. Each initial source is frozen before its first
compiler check. If it is rejected, one repair based only on the supplied compiler
diagnostic is allowed. Preserve the intended mechanism during that repair; do not
use it as a second design attempt. Later rounds can use only your own prior code,
compiler results, bounded behavior summary, semantic findings, and family/support
distributions. Semantic findings are uncertain review evidence: reason about
them before changing code, and record disagreement or unresolved issues. Do not
alter the contract or tests. An unchanged submission receives no new model
review. Stop is controlled by the runner on the first complete experimental
pass, an unavailable provider, or the three-round limit.
