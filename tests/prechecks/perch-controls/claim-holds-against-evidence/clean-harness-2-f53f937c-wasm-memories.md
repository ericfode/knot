<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=harness-2; head=f53f937c9706; base=b926a3c379b8; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-bootstrap/README.md@f53f937c sha256=6cdbf13c7267a364c4f0f42aa29343a585ad62156902fa4f83cc2296fa171ffb; tests/compiler-bootstrap/check.py@f53f937c sha256=c1507662a6f30eabd6e661932264ed9515effa3b27461dcec9611802d6cd76d4 -->
# Claim
tests/compiler-bootstrap/README.md:148-149 (section: One bundle, one argv, one contract) - verbatim text:

> **Artifact memory (D19, IO-ABI).** `wasm_memories` walks the whole import
> section and the whole memory section, not just the first memory it meets.

# Evidence
Evidence: the declarations the claim names, at head.

`tests/compiler-bootstrap/check.py:614-665` (declaration naming `wasm_memories`)
```
  614  def wasm_memories(data: bytes) -> dict:
  615      """Every memory a Wasm module declares, imported and defined, with its limits
  616      in pages and its shared and memory64 flags; {'unreadable': True} when the
  617      bytes do not parse as a module's import and memory sections."""
  618      def leb(at):
  619          value = shift = 0
  620          while True:
  621              byte = data[at]
  622              value, at, shift = value | (byte & 127) << shift, at + 1, shift + 7
  623              if byte < 128:
  624                  return value, at
  625  
  626      def limits(at):
  627          flags, at = leb(at)
  628          require(flags < 8, 'unknown limits flags')
  629          minimum, at = leb(at)
  630          maximum, at = leb(at) if flags & 1 else (None, at)
  631          return {'minimum': minimum, 'maximum': maximum, 'shared': bool(flags & 2), 'memory64': bool(flags & 4)}, at
  632  
  633      def value_type(at):  # (ref ht) and (ref null ht) carry a heap type
  634          return leb(at + 1)[1] if data[at] in (0x63, 0x64) else at + 1
  635  
  636      skip = {0: lambda at: leb(at)[1],                    # function: type index
  637              1: lambda at: limits(value_type(at))[1],     # table: reference type, limits
  638              3: lambda at: value_type(at) + 1,            # global: value type, mutability
  639              4: lambda at: leb(at + 1)[1]}                # tag: attribute, type index
  640      found = {'defined': [], 'imported': []}
  641      try:
  642          require(data[:8] == MAGIC, 'not a Wasm 1 module')
  643          at = 8
  644          while at < len(data):
  645              sid, (size, body) = data[at], leb(at + 1)
  646              end = body + size
  647              require(end <= len(data), 'section overruns the module')
  648              if sid in (2, 5):
  649                  count, cursor = leb(body)
  650                  for _ in range(count):
  651                      if sid == 2:
  652                          for _ in range(2):  # module and field names
  653                              length, cursor = leb(cursor)
  654                              cursor += length
  655                          kind, cursor = data[cursor], cursor + 1
  656                          if kind != 2:
  657                              cursor = skip[kind](cursor)
  658                              continue
  659                      memory, cursor = limits(cursor)
  660                      found['defined' if sid == 5 else 'imported'].append(memory)
  661                  require(cursor == end, 'section length disagrees with its contents')
  662              at = end
  663      except (AssertionError, IndexError, KeyError):
  664          return {'unreadable': True}
  665      return found
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
