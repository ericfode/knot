Excerpt of research/compiler-fields/SPEC.md: the paragraph of binders and quantities that the checker states and proves.

A pattern field receives the product of declaration quantity and scrutinee
quantity. A `+` pattern mark may promote quantity 1 over Data to quantity 2;
quantity 0 stays erased. Field names may shadow parameters or earlier fields.
A row may descend through several constructors before binding a field.
Already-declared constructor names cannot be used as bare pattern binders. Each occurrence
uses its lexical identity, not its display name.
