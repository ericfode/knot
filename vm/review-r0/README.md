# vm-spec review-r0 controls

These seed observations and literal plan outcomes were frozen before the review
fixes. They supplement the existing goldens; no existing expectation or oracle
archive is amended.

- `io-sequence`: the pinned seed checks the source and writes `alpha\nbeta\n`
  in Bun and native. The historical literals checker and evaluator both return
  `Invalid parse function-result`, exit 2. This is an inherited D4 defect owned
  by literals/io-check. Its IO lane is unavailable, never conformance agreement.
  The owner must report Unsupported until it can check IO result types.
- `tail-5000`: the seed and literals evaluator return True. The hand-written
  plan needs 5,002 entries: main, drain(5000), and 5,000 recursive calls.
  One entry less must stop as Exhausted kind 1, with 5,001 calls and no effects.
- `non-tail-4999`: the seed and literals evaluator return False. The plan needs
  10,000 entries: main, 5,000 drains and 4,999 inversions after recursive returns.
  One entry less must stop as Exhausted kind 1, with 9,999 calls and no effects.

The original reference evaluation fails `tail-5000` with RecursionError at the
gate's recursion limit of 20,000 and 1,000,000 fuel. This is a harness failure,
never VM Exhausted or agreement. The repair must evaluate both plans on an
explicit stack, including the non-tail work, and retain the exact fuel results.
It must also pass with the host recursion limit set to 256.

All observations in `expectations.json` were freshly reproduced with
`BEND_NO_TELEMETRY=1`, Bun 1.3.14 and the pinned Bend 2.0.29 seed. Commands:

```sh
export BEND_NO_TELEMETRY=1
export PATH=/Users/ericfode/.bun/bin:$PATH
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts vm/review-r0/io-sequence.bend --check-only
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts vm/review-r0/io-sequence.bend
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts vm/review-r0/io-sequence.bend -o .local/vm-spec/review-r0/seed-io-sequence
.local/vm-spec/review-r0/seed-io-sequence
.local/vm-spec/gate/literals-check --bundle . vm/review-r0/io-sequence.bend
.local/vm-spec/gate/literals-eval --bundle . vm/review-r0/io-sequence.bend main 1048576
```

The same commands, with the source and binary names replaced by `tail-5000`
and `non-tail-4999`, supplied their frozen observations. The literals binaries
are built from the unmodified hash-verified snapshot by `vm/check-spec.py`.
The non-tail plan is a literal reading of its source, with invert before drain.
Both plans validate and canonically round-trip through `vm/serializer.py`.

No law or compiler capability is added by these fixture programs. The reference
evaluation remains a value oracle, with no heap or frame-region model. Live
semantic and style ratings remain coordinator work.
