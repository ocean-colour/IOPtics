# `ioptics/runs/`

Versioned **build scripts** that drive a sweep end to end (prep -> run ->
metrics -> report) — *not* a CLI and *not* an importable package. The library
(`ioptics.config`, `ioptics.run`, `ioptics.report`) is the real interface; each
`build_vN.py` is a thin, staged orchestrator over it.

Layout (per `docs/design/IOPtics_implementation.md` §"Driving a sweep"):

```
runs/prototypes/<name>/
├── build_v1.py    # `python build_v1.py <flg>` — integer-flag staged sweep driver
└── run_v1.yaml    # the sweep config (single source of truth: sweep_id, datasets, algorithms)
```

Paths derive from `$OS_COLOR` + the sweep id, so every stage reads/writes under
`$OS_COLOR/IOPtics/runs/<sweep_id>/`.
