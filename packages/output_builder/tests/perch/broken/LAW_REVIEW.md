Assembly: append(b,s)=fragment(String.append(finish(b),s)).
Compose(a,b)=fragment(String.append(finish(a),finish(b))). Finish returns the
single stored fragment. Claimed total assembly cost O(N+K), where N is output
length and K is operations. Tests confirm exact emitted content; no cost issue.
