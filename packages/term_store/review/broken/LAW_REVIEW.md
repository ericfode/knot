# Memo completion control: broken

Only this table is under review. States: Pending, Evaluating, Ready(value), Failed(error).
Begin changes Pending to Evaluating. Succeed(v) changes Evaluating to Ready(v).
Reject(e) changes Evaluating to Failed(e). Other invalid actions preserve state.
Ready(v) returns completed success v; Failed(e) returns completed failure e.
Pending/Evaluating return NotReady; absent ID returns Bounds.

Cancellation example: Pending → Begin → Evaluating; on exhausted evaluation fuel,
Cancel installs Ready(0), and result returns completed success 0. This lets callers
reuse a deterministic fallback without resuming computation.
