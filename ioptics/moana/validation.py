"""Validation of MOANA against the three locked targets (design doc §1).

**Stub — implemented by the Validation prompt (prompt 14).** The targets and
their data are fixed (Q&A #4, #13, #15):

(i)   reproduce Lange et al. (2020) Tables 1–2 on AMT24 — training matrix
      from :func:`ioptics.moana.pipeline.build_training_matrix`, model from
      :func:`ioptics.moana.train.train_moana`, in the CTD-only
      configuration until the underway FCM arrives (PML follow-up item 1);
(ii)  apply the published coefficients to held-out cruises — Brewin et al.
      (2023) in-situ hyperspectral Rrs for AMT23/25/28 + their BODC
      flow-cytometry deposits;
(iii) the operational PACE product vs SeaBASS, including the one-granule
      bit-exactness check (`nasa_compat=True`, both `pc_mapping` settings)
      that settles Q&A #9.

Metrics throughout: log-space bias / MAE (Seegers et al. 2018) / adjusted R²,
with clipped retrievals treated as censored and the unphysical fraction
reported as a headline number (Q&A #13).
"""

from __future__ import annotations


def _not_yet(target):
    raise NotImplementedError(
        f"MOANA validation target {target} is scheduled for the Validation "
        "prompt (prompt 14); see this module's docstring for its definition.")


def validate_amt24(*args, **kwargs):
    """Target (i): reproduce Lange Tables 1–2 on AMT24. Not yet implemented."""
    _not_yet('(i)')


def validate_heldout_cruises(*args, **kwargs):
    """Target (ii): AMT23/25/28 in-situ Rrs vs cell counts. Not yet implemented."""
    _not_yet('(ii)')


def validate_pace_product(*args, **kwargs):
    """Target (iii): PACE MOANA vs SeaBASS + bit-exactness. Not yet implemented."""
    _not_yet('(iii)')
