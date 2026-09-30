# Non-leading template binders under layout

`template-tail-expectations.json` freezes nine controls before the repair (D7).
The two supplied programs retain exact SHA-256 identities
`4ce0f6cf470fb3922e9c7da0b96fd1731352503b0b1984f40ee891f6c0030ffc`
and `4dc786a9c0d9bf308127a53d443fc548c0832f092e0be43ccb8bb6b403ed0a6b`.
The pinned seed rejects their non-leading `~` tokens at offsets 98 and 110:
`a plain binder (only leading binders take ~)`.

The seed's `parse_tele` skips layout before testing whether a template binder
follows an ordinary binder. Knot already rejects a non-leading `~` on the same
line (`nonleading_template_binder` in `src/LAWS.bend`), but its parameter-tail
guard tests the unnormalized token list. A newline bypasses that guard and
reaches the initial-template Unsupported boundary. The fix must apply the
existing parameter rejection after layout, at the `~` token's own span.

| Controls | Seed / required Knot observation |
| --- | --- |
| Reported second and third binders | Invalid parse parameter at `98:99:9:2` and `110:111:10:2` |
| Ordinary binder followed by newline, comments/blank lines, or inline `~` | Invalid parse parameter at the non-leading marker |
| Bare quantity binder followed by newline and `~` | Same rejection; an ordinary erased binder also ends the leading template region |
| Leading template after layout | Seed accepts; Knot retains Unsupported parse template-binder |
| Leading template followed by a malformed later binder | Seed rejects later; Knot retains its documented initial-template prefix refusal |
| Ordinary multiline parameters and closed main | Seed checks and returns On{}; Knot must parse/check/evaluate/compile, with actual enum Wasm agreement |

All seed syntax/check outputs and source hashes are recorded verbatim. Seed
main runs are recorded for the two complete accepted controls. The required
Knot diagnostic is a literal application of the existing parameter rule, not
a diagnostic inferred from the implementation being repaired. Earlier frozen
expectations, source bytes and laws remain unchanged.
