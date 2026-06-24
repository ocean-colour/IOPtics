# Code IOPtics — Stage 2 ★: Engine wrap (the in-tandem vertical slice)

## Goal

Wire BING into the uniform layer and get the **first real two-way comparison**
running: one L23 spectrum fit by **both `expb_pow` and `giop`** via least-squares,
reconstructed with uncertainty, and written to the results tables + provenance.
**Exit criterion:** a single L23 spectrum × both algorithms (χ²) → two
`RetrievalResult`s → rows in `results_{spectral,scalar}.parquet` + `provenance.yaml`;
the synthetic-5-band micro-test recovers planted IOPs within tolerance.

Implements **Algorithm registry** + **Retrieval & run** and the **Staged plan /
Stage 2** of `docs/design/IOPtics_implementation.md`. One prompt per module.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- **BING is imported only by `algorithms.spec`, `run`, `evaluate`** (the boundary).
- Build BING models on the record's **native grid**; **never** seed the fit from truth.

## Context

- `docs/design/IOPtics_implementation.md` — §Algorithm registry (`AlgorithmSpec`,
  `to_bing_p`/`from_standard`/`build_models`, registry seeding), §Retrieval & run
  (`run_algorithm`, truth-free `initial_guess`, `evaluate.from_chisq`, results
  schema, `provenance.yaml`).
- bing: `parameters.{standard,p_ntuple}`, `models.{anw,bbnw}.init_model`,
  `models.utils.{init,init_other_bits}`, `priors.set_standard_priors`,
  `rt.defs.rt_dict_from_p`, `fitting.chisq_fit.fit`,
  `evaluate.reconstruct_chisq_fits`, `stats.{calc_chisq,calc_ICs}`.

## Prompts

### Coding

1. `algorithms/spec.py` (AlgorithmSpec + BING interop).
2. `algorithms/registry.py` (seed expb_pow + giop).
3. `run.py` — `run_algorithm` (χ² path) + truth-free `initial_guess`.
4. `evaluate.py` — `from_chisq` (covariance-sampled bands + stats).
5. `io.py` — long/tidy tables + sweep-dir layout.
6. `provenance.py` — YAML record + version stamping.
7. End-to-end synthetic micro-test.

## Modules

### Tasks

1. **`algorithms/spec.py`.** Implement `RTOptions`, `MCMCOptions`, `AlgorithmSpec`
   with `to_bing_p()` (→ `p_ntuple.gen`), `from_standard()` (← `parameters.standard`),
   `build_models(wave)` (→ `models.utils.init` + `priors.set_standard_priors` +
   `othera_priors`). Tier-1: round-trip vs `parameters.standard.{expb_pow,giop}`,
   param counts. Q&A. Log.

2. **`algorithms/registry.py`.** `register`/`get`/`available`; **seed `expb_pow`
   and `giop`** via `from_standard`; duplicate-name guard. Tier-1 tests. Q&A. Log.

3. **`run.py` — `run_algorithm` (χ²).** Build `p`/models/`rt_dict`; truth-free
   `init_other_bits` from `record.init`; **truth-free `initial_guess`** (QAA-style
   band inversion of observed Rrs + prior-central fallback); call
   `chisq_fit.fit`; hand to `evaluate.from_chisq`. Tier-1 on the synthetic record.
   Q&A. Log.

4. **`evaluate.py` — `from_chisq`.** Covariance-sample `N(ans,cov)` →
   `reconstruct_chisq_fits` → 68/95% bands; sub-components (`a_ph`/`a_dg`/`bb_p`);
   `stats.calc_chisq`/`calc_ICs` → χ²ᵥ/AIC/BIC; assemble `RetrievalResult` +
   `status`/QC. Tier-1. Q&A. Log.

5. **`io.py`.** Flatten `RetrievalResult`s to `results_spectral`/`results_scalar`
   long/tidy parquet (schemas per doc); create/own the
   `$OS_COLOR/IOPtics/runs/<sweep_id>/` layout; read helpers. Tier-1 round-trip.
   Q&A. Log.

6. **`provenance.py`.** Assemble `provenance.yaml` (versions incl. ocpy/bing/
   ioptics commits + doc versions; verbatim config copy; per-algorithm blocks with
   full priors + RT + fit method + noise model); `provenance_id` linking. Tier-1.
   Q&A. Log.

7. **End-to-end micro-test.** Synthetic 5-band Rrs from a known forward model →
   `prep` (synthetic record) → `run_algorithm` for **both** algorithms (χ²) →
   `evaluate` → `io` write → assert planted IOPs recovered within tolerance and
   tables/provenance well-formed. No `$OS_COLOR`, no MCMC. Q&A. Log.

### Q&A

## Logs
