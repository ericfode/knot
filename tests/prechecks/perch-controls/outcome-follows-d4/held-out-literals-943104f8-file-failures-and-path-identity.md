<!-- prechecks packet v1; rule=outcome-follows-d4; increment=literals; head=943104f881da; base=c0bd08d03942; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-modules/SPEC.md@943104f8 sha256=14a849a1aef6717d7252542ea6b7b11eeb7a3b5b32baa87894733862b5a128bf -->
# Claim
Outcome claims this branch changed:

tests/compiler-modules/SPEC.md:19-20 (section: Imported books and pinned Base) - verbatim text:

> File access failures other than missing imported files remain
> `HostFailure`. Resource bounds report `Exhausted` and never establish invalidity.

tests/compiler-modules/SPEC.md:25-27 (section: Imported books and pinned Base) - verbatim text:

> The host query rejects symlink components and non-exact directory-entry spellings
> with `Unsupported load path-identity`, including case aliases on insensitive
> filesystems.

tests/compiler-modules/SPEC.md:25-28 (section: Imported books and pinned Base) - verbatim text:

> The host query rejects symlink components and non-exact directory-entry spellings
> with `Unsupported load path-identity`, including case aliases on insensitive
> filesystems. Entry and bundle roots are queried before lexical normalization;
> user paths are queried before reading.

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
