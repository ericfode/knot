# Coordinator wording for D15–D18

The decisions are already adopted at `454bf30`. These are proposed precision
amendments, not an executor's change to the campaign decision table.

- **D15:** Nat is mathematical 0..4294967295, represented as the VM's tagged
  scalar word, boxed above 2^31-1. Check before narrowing. NatRange is Exhausted
  kind 2, with a precise VM outcome/receipt; U32 still wraps. Pure Char keeps
  every u32 code, including non-scalars, with scalar validation at IO only.
- **D16:** Count successful top-level entries, Applications and Invokes, including
  action/continuation and erased applications. Debit after arguments and before
  entry/effect. Primitives and representation work cost zero. Yield after the
  65,536th debit before body/effect execution, preserving the complete state.
  Fuel, heap/representation and frame exhaustion use kinds 1, 2 and 3.
- **D17:** Adopt knot-io-2. io-abi-2 owns the exact path_identity payload and
  symlink/case precedence from modules' pinned inspect bodies. VM IO acceptance
  waits for that contract; a Foreign format vector is not IO implementation.
- **D18:** Keep literals' machine and its emitted native profile frozen in S.
  knot-vm-1 is a separate runtime for knot-image-1. Its initial contract has
  uniform RC and immortal constants, not a unary-Nat extension of that machine.

Two design details require the coordinator's attention during review:

1. Scalar U32/Char cases need a sorted sparse-key table plus Default; only
   finite constructor cases can have a dense tag table. This preserves the
   existing literals core rather than allocating 2^32 arms.
2. Pinning separate evaluator snapshots makes the spec gate reproducible before
   merge-wave. It does not qualify the combined feature closure. The Foreign
   evaluator result remains Unsupported; vm-io supplies the missing lane.
