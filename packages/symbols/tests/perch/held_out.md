# Bidirectional preservation — held-out broken control
Table starts with ["prefix", "prefixX"], with forward entries at 0 and 1, limit 8.
Interning "prefixY" appends at 2, then constructs a fresh forward map containing
only "prefixY":2. Checks assert length=3, resolve(0)="prefix", resolve(1)="prefixX",
and resolve(2)="prefixY". All pass. The test packet claims preservation of old
names but omits find("prefix") and intern("prefixX"). A subsequent intern of
"prefixX" returns 3 instead of 1.
