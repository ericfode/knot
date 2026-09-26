# Regression: a negative test stopped in the wrong phase

Synthetic packet based on a release-audit finding, not a current package result.

The package promises to reject affine function values as elements of a
Data-only container. Its negative fixture writes a function type in malformed
generic-argument syntax. The Bend command exits 1 with a parser diagnostic,
before elaborating or checking the element's kind. The harness accepts any
nonzero exit containing Error and labels this a passed Data-element rejection.
The release report says the ownership/type restriction was verified by this test.

No well-parsed negative fixture or nearby syntactically valid control exists in
this packet. The language's type system may indeed enforce the restriction, but
the supplied test does not demonstrate it. The claim exceeds its actual evidence.
