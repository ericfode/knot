<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-spec; head=cea554abc93f; base=none; builder=manual-excerpt@3a2ef420dff1; sources: vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/serializer.py@cea554ab sha256=f28aef2493968d3729388c75909037dc4a3a56fc63a9b1bca885a1ff825279db -->
# Claim
`vm/check-spec.py:1670-1672` (comment above CODEC_MUTANTS)

> # Semantic mutants of the reference codec: (name, [(old, new), ...]). Each must change a
> # committed image, a frozen refusal, an admitted control or a frozen describe verdict; a crash
> # is never a kill.

# Evidence
`vm/serializer.py:39-44` (the reference codec's two refusal classes)

```
   39  class Malformed(Exception):
   40      """The bytes are not a knot-image-1 image: HostFailure image."""
   41  
   42  
   43  class Exhausted(Exception):
   44      """The image passes a version-1 resource limit (SPEC section 4): Exhausted kind 2."""
```

`vm/check-spec.py:1020-1035` (rejected)

```
 1020  def rejected(data: bytes, reg: dict, digest: bytes, c=None) -> str | None:
 1021      """None when the image is admitted; otherwise the refusal, as the VM loader must classify it:
 1022      a resource limit of section 4 is Exhausted kind 2, any other refusal HostFailure image."""
 1023      c = c or codec
 1024      try:
 1025          plan = c.decode(data, digest)
 1026      except c.Exhausted as e:
 1027          return f'Exhausted 2 {e}'
 1028      except c.Malformed as e:
 1029          return f'HostFailure image: {e}'
 1030      problems = c.validate(plan, reg)
 1031      if problems:
 1032          return 'HostFailure image: validator: ' + problems[0]
 1033      if c.encode(plan, digest) != data:
 1034          return 'HostFailure image: noncanonical'
 1035      return None
```

`vm/check-spec.py:1599-1602` (argument_verdict)

```
 1599  def argument_verdict(data: bytes, argv: list, reg: dict, digest: bytes, c=None) -> str | None:
 1600      """Sections 4 and 8 before any entry: the image first, then its entry kind's words."""
 1601      c = c or codec
 1602      return rejected(data, reg, digest, c) or c.arguments(c.decode(data, digest), argv)
```

`vm/check-spec.py:1624-1626` (describe_verdicts)

```
 1624  def describe_verdicts(controls: list, c=None) -> dict:
 1625      c = c or codec
 1626      return {label: c.undescribable({'types': types}, t) for label, types, t, _ in controls}
```

`vm/check-spec.py:1647-1667` (round_trip, text_spelling)

```
 1647  def round_trip(plan: dict, image: bytes, digest: bytes, c=None) -> str | None:
 1648      """None when `image` decodes to `plan` and survives the decode CLI's JSON text step."""
 1649      c = c or codec
 1650      decoded = c.decode(image, digest)
 1651      if decoded != plan:
 1652          return 'decodes to another plan'
 1653      if c.encode(json.loads(json.dumps(decoded)), digest) != image:
 1654          return 'the JSON text of its decoded plan re-encodes to other bytes'
 1655      return None
 1656  
 1657  
 1658  def text_spelling(plans: dict, digest: bytes, c=None) -> str | None:
 1659      """None when the encoder refuses a String constant spelled as text, the lossy spelling."""
 1660      c = c or codec
 1661      plan = json.loads(json.dumps(plans['string-ne-order']))
 1662      plan['functions'][1]['body'][3][0][3] = 'ab'
 1663      try:
 1664          c.encode(plan, digest)
 1665      except ValueError:
 1666          return None
 1667      return 'a text-spelled String constant was encoded'
```

`vm/check-spec.py:1824-1827` (invocation_verdicts)

```
 1824  def invocation_verdicts(invoking: list, c=None) -> dict:
 1825      """Section 8's verdict on every frozen Book invocation, by label."""
 1826      c = c or codec
 1827      return {label: c.invocation(plan, words) for label, plan, words in invoking}
```

`vm/check-spec.py:1830-1900` (codec_mutants)

```
 1830  def codec_mutants(plans, images, controls, admitted, describing, reg, digest, invoking, arguing) -> list:
 1831      """`plans` and `images` include the code-list controls; a decode that differs from its
 1832      plan kills as surely as an encode that differs from its image."""
 1833      source = CODEC.read_text()
 1834      results = []
 1835      for name, edits in CODEC_MUTANTS:
 1836          text = source
 1837          for old, new in edits:
 1838              require(text.count(old) == 1, f'codec mutant {name} is not uniquely located')
 1839              text = text.replace(old, new)
 1840          mutant = load_codec(text)
 1841          killed_by = None
 1842          for case, plan in plans.items():
 1843              try:
 1844                  if mutant.encode(plan, digest) != images[case]:
 1845                      killed_by = f'image {case} differs'
 1846                      break
 1847                  lost = round_trip(plan, images[case], digest, mutant)
 1848                  if lost:
 1849                      killed_by = f'image {case} {lost}'
 1850                      break
 1851              except Exception:
 1852                  continue
 1853          if not killed_by:
 1854              try:
 1855                  killed_by = text_spelling(plans, digest, mutant)
 1856              except Exception:
 1857                  pass
 1858          for label, data, reason, message in [] if killed_by else controls:
 1859              try:
 1860                  got = rejected(data, reg, digest, mutant)
 1861              except Exception:
 1862                  continue
 1863              if got is None or not got.startswith(reason) or message not in got:
 1864                  killed_by = f'control {label}: {got}'
 1865                  break
 1866          for label, data in [] if killed_by else admitted:
 1867              try:
 1868                  got = rejected(data, reg, digest, mutant)
 1869              except Exception:
 1870                  continue
 1871              if got is not None:
 1872                  killed_by = f'admitted control {label}: {got}'
 1873                  break
 1874          if not killed_by:
 1875              try:
 1876                  verdicts = describe_verdicts(describing, mutant)
 1877              except Exception:
 1878                  verdicts = None
 1879              changed = [label for label, _, _, verdict in describing if verdicts and verdicts[label] != verdict]
 1880              if changed:
 1881                  killed_by = f'describe control {changed[0]}: {verdicts[changed[0]]}'
 1882          if not killed_by:
 1883              frozen = invocation_verdicts(invoking)
 1884              try:
 1885                  verdicts = invocation_verdicts(invoking, mutant)
 1886              except Exception:
 1887                  verdicts = frozen
 1888              changed = [label for label in frozen if verdicts[label] != frozen[label]]
 1889              if changed:
 1890                  killed_by = f'invocation {changed[0]}: {verdicts[changed[0]]}'
 1891          for label, data, argv, verdict in [] if killed_by else arguing:
 1892              try:
 1893                  got = argument_verdict(data, argv, reg, digest, mutant)
 1894              except Exception:
 1895                  continue
 1896              if got != verdict:
 1897                  killed_by = f'argument control {label}: {got}'
 1898                  break
 1899          results.append({'mutant': name, 'killed': killed_by is not None, 'by': killed_by})
 1900      return results
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
