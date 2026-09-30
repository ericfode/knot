<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-model; head=07e6db733079; base=none; builder=manual-excerpt@3a2ef420dff1; sources: docs/compiler-campaign/GATES.md@07e6db73 sha256=55e1d241cc08a8dea28551716ba3a94cc56a11c5287d16dc9e22dc31258aa2bb; vm/MODEL.md@07e6db73 sha256=b7a86f1c91eb36799825c30b9c09690e3303d4c28ac8ebae554fc90f29a9b6da; vm/check-model.py@07e6db73 sha256=1f45bd478b9a9afe0320d678d1d1a2d2c9356dce5df46f722ecd6d0bca94eae8; vm/check-model.py@07e6db73 sha256=1f45bd478b9a9afe0320d678d1d1a2d2c9356dce5df46f722ecd6d0bca94eae8 -->
# Claim
`docs/compiler-campaign/GATES.md:104-105` (vm-model gate: mutant kills)

> printing `All terms check.` (32 laws); 46 model mutants killed by a wrong
> observation, never a crash or a harness fault, 14 of them also refuted by a law;

`vm/MODEL.md:40-45` (outcome exits, HarnessBound)

> The seed runtime strips its own options up to the first `--`, so callers put
> `--` before the image. Outcomes print as eval-cli does: `Evaluated` lines on
> stdout; `Exhausted<TAB>vm<TAB>kind<TAB>cause` (exit 4), `HostFailure<TAB>phase<TAB>code`
> (5), `Unsupported<TAB>phase<TAB>code` (3) and `InternalFailure<TAB>vm<TAB>code` (6) on
> stderr. `HarnessBound<TAB>model<TAB>transitions` (7) is the model's own Nat bound
> on transitions: a harness limit, never VM exhaustion.

# Evidence
`vm/check-model.py:287-303` (TORN, harness_faults, KNOWN_EXITS, well_formed)

```
  287  TORN = tuple(f'HostFailure image: {reason}' for reason in ('length', 'magic', 'total', 'noncanonical'))
  288  
  289  
  290  def harness_faults(observed: dict) -> list:
  291      """Rows whose image the reference codec admits and the model refused as TORN."""
  292      return [f'{check}:{name}' for check, rows in observed.items() for name, row in rows.items()
  293              if row.get('admitted') and model_refusal(row['result']) in TORN]
  294  
  295  
  296  # ------------------------------------------------------------------ observations
  297  
  298  KNOWN_EXITS = {0, 3, 4, 5, 6, 7}
  299  
  300  
  301  def well_formed(result) -> bool:
  302      """A model answer, not a crash, trap or timeout: those never count as a kill."""
  303      return result['exit'] in KNOWN_EXITS and 'bend:' not in result['stderr']
```

`vm/check-model.py:1048-1057` (kills)

```
 1048  def kills(base: dict, mutant: dict) -> list:
 1049      """Checks whose observation changed to a well-formed wrong one; a harness fault is none."""
 1050      faults = set(harness_faults(mutant))
 1051      killed = []
 1052      for check, rows in mutant.items():
 1053          for name, row in rows.items():
 1054              if not row['agrees'] and base[check][name]['agrees'] and (
 1055                      check == 'sweep' or well_formed(row['result'])) and f'{check}:{name}' not in faults:
 1056                  killed.append(f'{check}:{name}')
 1057      return killed
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
