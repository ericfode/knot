# Held-out incomplete-work control

Table: unevaluated Begin → busy; busy Succeed(v) → complete(v); busy Reject(e) →
error(e). All remaining transition pairs fail unchanged, including Cancel on busy.
Result maps complete(v) to completed success v, error(e) to completed failure e,
unevaluated or busy to Incomplete, and unknown ID to Missing.
Cancellation example: busy Cancel returns Interrupted with the busy cell unchanged;
result still returns Incomplete. No fallback value is published. A separate owner
may later resume evaluation and explicitly Succeed.
