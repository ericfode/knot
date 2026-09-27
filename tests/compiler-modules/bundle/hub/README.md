# Offline hub stub

`regen.py` points `BEND_HUB` at `file://<ROOT>/tests/compiler-modules/bundle/hub`.
This directory deliberately contains no packages or names. The seed consults
the hub only when material is absent from `BEND_LIB`. It then fails
deterministically on a missing `<hash>/manifest`, with no network request and
no write into the frozen `bundle/lib`.

Never add package material here. Frozen packages belong in `bundle/lib`, where
`regen.py` recomputes their content hashes before and after every run.
