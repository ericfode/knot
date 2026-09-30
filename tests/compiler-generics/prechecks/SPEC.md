# Parser observation boundary

The parse CLI prints Parsed only after checking the declaration availability
that the seed's parse_patt requires. Record datatype constructor declaration
spans. At each pattern, only matching constructors at earlier source offsets
are visible. Availability follows source order, independently of AST list order.
A constructor in a pattern must belong to that set; recurse into its field
patterns and each arm's body. Term constructors may reference later declarations.
Unregistered patterns are Invalid parse unknown-constructor at their name.
The traversal is bounded: exhausted depth is Exhausted, never Invalid.

The AST builder remains separate from this observation check; generic checking
independently enforces the same visibility obligation. The monomorphic checker
residual remains explicit. No general parser-soundness or traversal-refinement
theorem is claimed. Three filled boundary laws describe the pattern guard and
zero budget, with concrete registered and unregistered fixtures as witnesses.

Line breaks before a result colon are layout. A `~` in a type argument and a
second initializer `=` are malformed term starts. Existing authorized prefix
refusals remain frozen, with the exact recognized prefix distinguished from the
diagnostic token. No refused program is evaluated or produces a new artifact.

Layout also separates declaration keywords/names, names/opening delimiters,
generic headers/the required `is`, function parameters/separators, and a result
arrow/its type. Applied-type lookahead sees a line break before `<`. Parameter
list layout is distinct from expression argument layout. Source offsets still
decide adjacency inside arrows, quantity/meet tokens and closing type lists.
Missing delimiters retain their existing failures. Three additional universal
boundary equations preserve parameter-start, parameter-tail and declaration-name
layout, including refusal results. A fourth refuses a detached named-type header
closer. Both named and structured parameter routes check the original source
offsets before the parameter-list parser skips layout. These equations do not
prove general parser soundness.

Parameter-tail layout does not restart a leading template region. After any
ordinary binder (including a bare quantity binder), a following `~` is Invalid
parse parameter at the marker, across comments and line breaks. Initial
templates retain the documented prefix-only Unsupported boundary. The added
filled equation states the non-leading-marker refusal after a newline,
independently of the unconsumed suffix and source positions.
