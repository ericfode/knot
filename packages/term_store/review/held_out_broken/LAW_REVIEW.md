# Held-out premature-result control

Table: Pending Begin → Evaluating; Evaluating Succeed(v) → Ready(v);
Evaluating Reject(e) → Failed(e); Evaluating Cancel → Pending. All other
transitions fail and preserve state. Unknown IDs return Missing. Ready(v)
returns completed success v; Failed(e) returns completed failure e.
Cancellation example: Evaluating Cancel → Pending; result on Pending returns
completed success 1, as does result on Evaluating, so callers need not branch on
incomplete work. Cancellation itself never writes a Ready cell.
