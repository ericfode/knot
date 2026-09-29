<!-- prechecks packet v1; rule=outcome-follows-d4; increment=vm-spec; head=94bc3d575cdf; base=none; builder=manual-excerpt@3a2ef420dff1; sources: docs/COMPILER-CAMPAIGN.md@94bc3d57 sha256=40e00d3b2f87172cf12890ff2fb1561395b84165009a65be9d0c0d56c46d8b7a; docs/COMPILER-CAMPAIGN.md@94bc3d57 sha256=40e00d3b2f87172cf12890ff2fb1561395b84165009a65be9d0c0d56c46d8b7a; vm/SPEC.md@94bc3d57 sha256=d0666796ac67a26f36f9c01137822d14ab7ae847ed1462dc92d35b5b7a31ad11; vm/SPEC.md@94bc3d57 sha256=d0666796ac67a26f36f9c01137822d14ab7ae847ed1462dc92d35b5b7a31ad11; vm/check-spec.py@94bc3d57 sha256=2cad8c30f3ac305c3c5301619e765f60fc6e955850cd8c4724f8c62248cfaca4 -->
# Claim
`vm/SPEC.md:232-234`

> 1. Size first: an image above 16 MiB (4,194,304 words) is `Exhausted image-size`,
>    even when it is also malformed. Then length, magic, version, total, entry kind,
>    reserved word and registry digest.

`vm/SPEC.md:245-246`

> A refused image is `HostFailure image` with a reason. `check-spec.py` freezes 61
> refusals (20 byte-level, 41 plan-level); vm-core MUST refuse the same controls,

# Evidence
`docs/COMPILER-CAMPAIGN.md:73-73` (decision row D4)

```
   73  | D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
```

`docs/COMPILER-CAMPAIGN.md:85-85` (decision row D16)

```
   85  | D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |
```

`vm/check-spec.py:877-906` (frozen refusal expectations for image bytes)

```
  877  def byte_controls(images: dict, digest: bytes) -> list:
  878      """(label, bytes, frozen refusal prefix) for malformed and noncanonical images."""
  879      second, capture, hit = images['second'], images['closure-captures'], images['default-hit']
  880      first_node, names_at = word(second, 9) + 1, word(second, 10)
  881      swap = word(capture, 7) + 1                 # first function record (swap, arity 2: 8 words)
  882      body = word(capture, swap + 5)              # its root Let node
  883      oversize = b'\0' * (4 * codec.LIMITS['image_words'])
  884      out = [
  885          ('truncated', second[:-4], 'total'),
  886          ('bad-magic', word_patch(second, 0, 0x474D494C), 'magic'),
  887          ('version-2', word_patch(second, 1, 2), 'magic'),
  888          ('total-words', word_patch(second, 2, word(second, 2) + 1), 'total'),
  889          ('entry-kind', word_patch(second, 3, 2), 'header'),
  890          ('reserved-word', word_patch(second, 11, 1), 'header'),
  891          ('registry-digest', word_patch(second, 24, word(second, 24) ^ 1), 'registry digest'),
  892          ('section-offset', word_patch(second, 6, word(second, 6) + 1), 'section 1 offset'),
  893          ('record-length', word_patch(second, first_node, 1), 'section 4 record length'),
  894          ('trailing-word', word_patch(second + b'\0' * 4, 2, word(second, 2) + 1), 'trailing words'),
  895          ('opcode', word_patch(second, first_node + 1, 13), 'node record'),
  896          ('main-index', word_patch(second, 4, 0), 'main index'),
  897          ('name-utf8', word_patch(second, names_at + 3, 0xFFFFFFFF), 'name utf-8'),
  898          ('function-root-shared', word_patch(capture, swap + 8 + 5, body), 'function root'),
  899          ('child-not-record', word_patch(capture, body + 4, word(capture, body + 4) + 1), 'child offset'),
  900          ('child-after-parent', word_patch(capture, body + 4, body + 6), 'child after parent'),
  901          ('oversize', second + oversize, 'exhausted image-size'),
  902          ('oversize-and-bad-magic', word_patch(second, 0, 0) + oversize, 'exhausted image-size'),
  903          ('oversize-and-misaligned', second + oversize + b'\0', 'exhausted image-size'),
  904          ('unused-constant', unused_constant(hit), 'noncanonical'),
  905      ]
  906      return [(label, data, 'HostFailure image: ' + reason, '') for label, data, reason in out]
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
