<!-- prechecks packet v1; rule=outcome-follows-d4; increment=vm-spec; head=63e63203bb2e; base=454bf3059679; builder=manual-excerpt@3a2ef420dff1; sources: docs/COMPILER-CAMPAIGN.md@63e63203 sha256=223cf76f13cd0911819691eacd2d5de09dc4b8e62d296675c6c6a9e3beb5b294; docs/COMPILER-CAMPAIGN.md@63e63203 sha256=223cf76f13cd0911819691eacd2d5de09dc4b8e62d296675c6c6a9e3beb5b294; vm/SPEC.md@63e63203 sha256=9d65a6ae4cdd8b78181ff8846add9e6415c935f46dc2362d74aab6459815caed; vm/SPEC.md@63e63203 sha256=9d65a6ae4cdd8b78181ff8846add9e6415c935f46dc2362d74aab6459815caed; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511 -->
# Claim
`vm/SPEC.md:253-255`

> 1. Size first: an image above 16 MiB (4,194,304 words) is `Exhausted` kind 2
>    (`image-size`), even when it is also malformed. Then length, magic, version,
>    total, entry kind, reserved word and registry digest.

`vm/SPEC.md:267-268`

> A refused image is `HostFailure image` with a reason, except past a **resource
> limit** of version 1, which is `Exhausted` kind 2 with the limit as its cause (D16).

# Evidence
`docs/COMPILER-CAMPAIGN.md:73-73` (decision row D4)

```
   73  | D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
```

`docs/COMPILER-CAMPAIGN.md:85-85` (decision row D16)

```
   85  | D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap and representation: NatRange, RCOverflow, the image limits of `vm/SPEC.md` §4 (size, records per table, arity and slots), and display), and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. Kind 2 was widened in vm-spec review round 8: an image past a resource limit is exhausted, not malformed. |
```

`vm/check-spec.py:1107-1140` (frozen refusal expectations for image bytes)

```
 1107  def byte_controls(images: dict, digest: bytes) -> list:
 1108      """(label, bytes, frozen refusal prefix) for malformed and noncanonical images."""
 1109      second, capture, hit = images['second'], images['closure-captures'], images['default-hit']
 1110      first_node, names_at = word(second, 9) + 1, word(second, 10)
 1111      swap = word(capture, 7) + 1                 # first function record (swap, arity 2: 8 words)
 1112      body = word(capture, swap + 5)              # its root Let node
 1113      oversize = b'\0' * (4 * codec.LIMITS['image_words'])
 1114      out = [
 1115          ('truncated', second[:-4], 'total'),
 1116          ('bad-magic', word_patch(second, 0, 0x474D494C), 'magic'),
 1117          ('version-2', word_patch(second, 1, 2), 'magic'),
 1118          ('total-words', word_patch(second, 2, word(second, 2) + 1), 'total'),
 1119          ('entry-kind', word_patch(second, 3, 2), 'header'),
 1120          ('reserved-word', word_patch(second, 11, 1), 'header'),
 1121          ('registry-digest', word_patch(second, 24, word(second, 24) ^ 1), 'registry digest'),
 1122          ('section-offset', word_patch(second, 6, word(second, 6) + 1), 'section 1 offset'),
 1123          ('record-length', word_patch(second, first_node, 1), 'section 4 record length'),
 1124          ('trailing-word', word_patch(second + b'\0' * 4, 2, word(second, 2) + 1), 'trailing words'),
 1125          ('opcode', word_patch(second, first_node + 1, 13), 'node record'),
 1126          ('main-index', word_patch(second, 4, 0), 'main index'),
 1127          ('name-utf8', word_patch(second, names_at + 3, 0xFFFFFFFF), 'name utf-8'),
 1128          ('function-root-shared', word_patch(capture, swap + 8 + 5, body), 'function root'),
 1129          ('child-not-record', word_patch(capture, body + 4, word(capture, body + 4) + 1), 'child offset'),
 1130          ('child-after-parent', word_patch(capture, body + 4, body + 6), 'child after parent'),
 1131          ('unused-constant', unused_constant(hit), 'noncanonical'),
 1132      ]
 1133      # Section 4.1 and D16: an image above 16 MiB is Exhausted kind 2, even when also malformed.
 1134      exhausted = [
 1135          ('oversize', second + oversize, 'image-size'),
 1136          ('oversize-and-bad-magic', word_patch(second, 0, 0) + oversize, 'image-size'),
 1137          ('oversize-and-misaligned', second + oversize + b'\0', 'image-size'),
 1138      ]
 1139      return [(label, data, 'HostFailure image: ' + reason, '') for label, data, reason in out] + \
 1140          [(label, data, 'Exhausted 2 ' + cause, '') for label, data, cause in exhausted]
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
