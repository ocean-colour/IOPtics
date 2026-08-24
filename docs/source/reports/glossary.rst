====================
Metrics and verdicts
====================

Every number on the leaderboard and in the report tables is defined below,
together with the value a **perfect** retrieval would produce. That value is
*not* always zero — earlier versions of these pages said "all metrics 0 =
perfect", which is false for at least four columns: ``median_ratio`` is perfect
at **1**, ``win_frac`` at **1** (0.5 = a tie), and ``coverage68`` /
``coverage95`` at their nominal levels **0.68** and **0.95**. Each entry states
its own target.

Throughout, :math:`M` is the retrieved (modelled) value and :math:`O` the truth
(observed) value, compared **pair by pair**. A pair enters a metric only where
both values are finite **and strictly positive** — the accuracy metrics are
log-space, so a zero or negative retrieval is dropped exactly like a missing one.
Nothing is zero-filled, and the surviving count travels with every number.

Accuracy
--------

All accuracy metrics are **log-space and multiplicative**, following Erickson et
al. (2023) Eqs. 13-14, after Seegers et al. (2018).

.. important::

   **Ours is the fractional form: 0 = perfect, and 0.109 means 10.9%.**
   Seegers et al. publish the *un-subtracted factor* — the same retrieval is
   reported there as **1.109**, and their "1.5 = 50% error". A reader from that
   lineage must not read our ``mae = 0.109`` as a factor of 0.109. The two differ
   by the trailing :math:`-1`, nothing else.

``mae`` — mean absolute (multiplicative) error
    :math:`\mathrm{mae} = 10^{\,\overline{|\log_{10}(M/O)|}} - 1`.
    **Perfect = 0.** The typical retrieval is wrong by this fraction,
    irrespective of sign. Worked: an ``mae`` of **0.109** is 10.9% typical error
    (underlying log error 0.045 dex; Seegers would print 1.109).

``bias`` / ``abs_bias`` — signed multiplicative bias
    :math:`\mathrm{bias} = 10^{\,\overline{\log_{10}(M/O)}} - 1`.
    **Perfect = 0**; positive = systematic **over**-estimate, negative =
    under-estimate. ``abs_bias`` is :math:`|\mathrm{bias}|` and is the column
    that gets ranked, because direction should not decide a standing. A small
    ``bias`` is compatible with a large ``mae``, since scatter cancels in the
    signed mean.

``rms_log`` — RMS error in log space
    :math:`\sqrt{\overline{[\log_{10}(M/O)]^{2}}}`, in **dex** (decades), *not*
    back-transformed. **Perfect = 0.** Reported for continuity; Seegers et al.
    discourage RMS-family statistics as a headline score because they amplify
    outliers.

``median_ratio`` — GIOP's *Ratio*
    :math:`\mathrm{median}(M/O)`. **Perfect = 1.** The statistic Werdell et al.
    (2013) Table 4 tabulates, named the way that audience names it. Being a
    median it is insensitive to the few catastrophic points that dominate
    ``mae``.

MPD — GIOP's *median absolute percent difference*
    :math:`\mathrm{median}\!\left(100\,|M/O - 1|\right)`%. **Perfect = 0.**
    Computed for the figure legends rather than the tables: each scatter legend
    entry reads ``giop  n=20, ratio 1.06, MPD 6.2%``, so a panel can be read
    without the table beneath it.

Ratio histogram
    Counts of :math:`M/O` in the Erickson Fig. 4 buckets with edges
    :math:`0,\,\tfrac13,\,\tfrac12,\,\tfrac34,\,1,\,\tfrac43,\,2,\,3,\,\infty`.
    **Perfect** = every count in the two buckets adjoining 1. Central tendency
    alone hides the spread that decides whether a retrieval is usable.

Type-II fit
    Reduced-major-axis regression of :math:`\log_{10} M` on :math:`\log_{10} O`,
    returning ``(slope, intercept, r2)``. **Perfect = (1, 0, 1).** RMA rather
    than ordinary least squares because both axes carry error.

How many spectra
----------------

Three different denominators appear in the tables, and they are not
interchangeable. On the first GLORIA sweep one contest had all three, and all
three had previously been published as some flavour of "n":

.. list-table::
   :header-rows: 1
   :widths: 18 14 68

   * - Column
     - GLORIA
     - What it counts
   * - ``n_pairs``
     - 12
     - Surviving *(retrieved, truth)* pairs after the finite-and-positive
       intersection. The denominator of every accuracy metric above.
   * - ``n_scored``
     - 21
     - Spectra whose fit ``status`` is ``ok`` — the solutions. Fewer spectra can
       be *scored for accuracy* than solved, because a solved spectrum still
       needs truth for that component at that band.
   * - ``n_attempted``
     - 100
     - Every fit the sweep attempted. The honest denominator for "how often does
       this algorithm work at all".

``coverage_n`` is a **fourth** count, and deliberately its own column. Coverage
needs the truth and *both* interval bounds and ignores the retrieved value,
whereas ``n_pairs`` needs a positive retrieval and truth and ignores the
bounds — so a fit whose covariance failed contributes to one and not the other.
Testing a ``coverage_n``-trial proportion with an ``n_pairs``-trial standard
error would be too tight by :math:`\sqrt{n/\mathrm{coverage\_n}}` and could
accuse a thin contest of mis-calibration.

**Stratum** says which spectra a row covers. Rows are emitted for the synthetic
``stratum='all'`` *and* for each chlorophyll bin — ``oligotrophic``
(Chl < 0.1 mg m\ :sup:`-3`), ``mesotrophic`` (0.1-1.0), ``eutrophic``
(:math:`\ge` 1.0) or ``unknown`` — assigned from truth Chl where the dataset has
it, else from the retrieved Chl.

Fit quality, and why a spectrum was not scored
----------------------------------------------

Two fit-quality numbers are published side by side, and they answer different
questions.

:math:`\chi^{2}_{\nu}` (``chi2_nu_median``)
    :math:`\chi^{2}/(n-k)`, noise-weighted. **Perfect** :math:`\approx 1`; below
    1 is over-fitting, above 1 under-fitting. It answers *"does the model agree
    with the data to within the stated uncertainty"* — and therefore moves
    whenever that uncertainty is re-stated, even though the fit has not changed
    (on GLORIA it shifted five-fold when the assumed error floor changed). The
    acceptance band is scaled to the degrees of freedom,
    :math:`1 \pm 2\sqrt{2/\mathrm{dof}}` — wide for few bands, tight for many —
    and each fit falls into ``frac_good`` / ``frac_overfit`` / ``frac_underfit``
    accordingly.

``rel_misfit`` — GIOP's :math:`\Delta R_{rs}`
    :math:`\mathrm{median}_\lambda\,|R_{rs}^{\mathrm{model}} -
    R_{rs}^{\mathrm{obs}}| / R_{rs}^{\mathrm{obs}}`, over bands with
    :math:`R_{rs}^{\mathrm{obs}} > 0`. **Perfect = 0.** It owes nothing to the
    noise model: *"how far off is it, in fractions of the observation."* On data
    whose quoted uncertainties are absent or untrustworthy, read this first.
    Published twice — ``rel_misfit_median`` over the solved spectra and
    ``rel_misfit_median_all`` over every attempted one.

``frac_qc_fail`` is the share of attempted fits with
:math:`\chi^{2}_{\nu} > 5`, the same threshold that sets the per-row status, so
the row label and the aggregate cannot drift apart.

Only ``status == 'ok'`` rows are scored — a leaderboard ranks *solutions*, and
averaging a failed fit in makes each algorithm's number a median over its own
private subset of spectra. The rest are reported as **coverage**: one
``frac_<status>`` per status.

.. list-table::
   :header-rows: 1
   :widths: 18 12 70

   * - ``status``
     - GLORIA
     - Plain-English reason
   * - ``ok``
     - 21%
     - Converged, with :math:`\chi^2_\nu \le 5`. A turbid spectrum that *is*
       fitted well is ``ok``: the regime alone never disqualifies a fit.
   * - ``poor_fit``
     - 16%
     - The optimiser returned, but :math:`\chi^2_\nu > 5`. Parameters are kept so
       the row can be inspected; it is not a solution.
   * - ``out_of_scope``
     - 63%
     - A poor fit **explained by the regime**: the :math:`R_{rs}` peak lies
       redward of 560 nm, outside what this open-ocean model family is built for.
   * - ``fit_failed``
     - 0%
     - No usable parameters — the optimiser raised, or returned non-finite values.

.. note::

   GLORIA's 63% ``out_of_scope`` is a statement **about the models, not a defect
   in IOPtics**: those spectra are turbid, and no algorithm in this family should
   be expected to work there. It is a different finding from 63% ``poor_fit``
   (the models were asked a fair question and got it wrong) and from 63%
   ``fit_failed`` (the fitter broke). A report that collapses the four statuses
   into one "failure rate" destroys exactly that distinction.

Uncertainty calibration
-----------------------

``coverage68`` / ``coverage95``
    The fraction of truth values falling inside the retrieved 68% / 95%
    interval. **Perfect = 0.68 and 0.95** — not 0, and not 1. Too low means the
    intervals are too narrow, too high means they are too wide. Accuracy and
    calibration are independent: on the L23 smoke test ``giop`` won 85% of
    head-to-head contests at :math:`a(440)` while its 68% / 95% intervals held
    truth only 45% / 65% of the time — the most accurate algorithm there was also
    the most over-confident.

Each level carries a ``*_verdict`` word rather than a boolean, because the
direction is the finding: **over-confident** (empirical coverage more than
:math:`2\sigma` below nominal, intervals too narrow), **conservative** (more than
:math:`2\sigma` above, too wide), **consistent** (neither), or ``NA`` (nothing
was scored). The :math:`\sigma` is the binomial standard error
:math:`\sqrt{p(1-p)/\mathrm{coverage\_n}}`.

.. warning::

   **"consistent" is a statement about the evidence, not a certificate.** It
   means *not distinguishable from nominal at this* ``coverage_n``. The detection
   window is wide when ``n`` is small: at :math:`n = 12` only a ``coverage68``
   outside **[0.41, 0.95]** is flagged at all, while at :math:`n = 3320` the
   window narrows to **[0.66, 0.70]**. A thin contest reading "consistent" has
   mostly told you it was thin.

Comparing algorithms
--------------------

``wins`` / ``win_frac``
    Within each ``(dataset, fit_method, stratum, component, ref_wave)`` contest,
    every spectrum hosts a round-robin among the algorithms present; the one
    **closer to truth** wins, on :math:`|\log_{10}(M/O)|`. Ties split credit
    (0.5 each) and still count as a contest for both.
    ``win_frac = wins / contests``: **perfect = 1, and 0.5 is a tie**. Percent
    wins is Seegers et al.'s recommended ranking metric. Caveat: ``wins`` tallies
    per algorithm and **discards the opponent's identity**, so its "contests" are
    not independent trials of any one pairing — with four algorithms, 36 contests
    are 12 spectra × 3 opponents.

The **head-to-head** table keeps the pairing, and is the only place a page can
honestly say "these two are indistinguishable".

``n_paired``
    Spectra where *both* algorithms produced a scoreable retrieval.

``win_frac_a``
    The tally for **this pair alone**. 0.5 = tie, 1 = A wins every spectrum.

``delta_mae``, ``d_lo`` / ``d_hi``
    :math:`\mathrm{mae}(A) - \mathrm{mae}(B)` on the paired spectra
    (**negative favours A**; perfect tie = 0), with its 95% **paired** bootstrap
    percentile interval — 1000 resamples of the spectra, so each replicate
    recomputes both MAEs on the same draw (after the Brewin et al. 2015
    round-robin). The seed is fixed and derived per contest and pair, so a
    published verdict does not change when the report is regenerated, and
    intervals from different pairs are independent draws rather than correlated
    noise.

``verdict``
    Two thresholds, deliberately separate: the bootstrap answers *can we tell?*
    and the practical floor answers *would anyone care?* A winner is named only
    when both say yes. Values: a **winner's name**; ``indistinguishable``
    (equivalence established — the whole interval lies inside the floor);
    ``underpowered`` (fewer than 3 paired spectra, or a material point estimate
    the interval does not resolve); or empty (the pair shares no scoreable
    spectrum at all, a different fact from an unresolved difference — such rows
    are dropped from the published table). A side whose MAE is infinite loses
    outright: a catastrophic loss needs no statistics.

.. warning::

   **The practical floor is 0.10 in absolute fractional MAE**, and this has a
   measured consequence. On a dataset where both algorithms are accurate — a few
   percent ref-band MAE, as an L23-class synthetic gives — two algorithms whose
   errors differ **five-fold** (1% vs 5%) are only 0.04 apart, so no pair can
   ever clear the floor and every contest is declared equivalent by construction.
   The floor encodes what counts as scientifically meaningful, which is a
   judgement rather than a statistic.

:math:`\Delta\mathrm{BIC}`
    :math:`\mathrm{BIC}_A - \mathrm{BIC}_B` per spectrum, matched like-for-like
    within one ``fit_method``. **Negative favours model A** (lower BIC); for a
    pair chosen as the sweep's highest- against lowest-parameter algorithm, that
    means the extra parameters earned their keep. ``frac_favor_a`` is the share
    with :math:`\Delta\mathrm{BIC} < 0`; exact ties favour neither, so the two
    fractions need not sum to 1.

``ranking``
    Why a row does or does not carry a ``rank``. Ranks order each contest by
    ``win_frac`` (descending), then ``abs_bias``, then ``mae`` (ascending).

    .. list-table::
       :header-rows: 1
       :widths: 30 70

       * - Value
         - Meaning
       * - ``ranked``
         - A rank supported by at least one resolved pairwise verdict.
       * - ``ranked (no head-to-head)``
         - Ordered, but no pairwise verdict exists for this contest (an older
           sweep, or a fit method whose pairs were never computed). The ordering
           has no head-to-head support.
       * - ``sole competitor``
         - One measured algorithm. "Rank 1" over a one-horse race reads as a win,
           so no rank is printed.
       * - ``indistinguishable``
         - Measured, but **no pair separated**. Printing 1..N here would assert
           an order the data do not support.
       * - ``not scored``
         - Nothing measured behind the row.

``frac_ok``
    The share of attempted spectra that produced a solution — Brewin et al.
    (2015) :math:`\eta`, *"percentage of possible retrievals"*, on their stated
    grounds that an algorithm should not be a source of more data gaps than its
    competitors. **Perfect = 1.** Read it *with* the rank: a top rank over 10% of
    the spectra is not a better algorithm than a lower rank over all of them.

``separable`` / ``algo_digest``
    ``separable`` records, per contest, whether any pair resolved to a winner; it
    is what blanks a rank. ``algo_digest`` is an 8-character hash of the sweep's
    recorded algorithm configuration block — two rows sharing an algorithm *name*
    are not necessarily the same algorithm, and this makes the difference
    visible.

Caveats
-------

``caveat = 'CDOM_vs_adg'``
    Stamped on **GLORIA** ``a_dg`` rows and carried through to the leaderboard.
    GLORIA supplies CDOM absorption as truth, while :math:`a_{dg}` is CDOM
    **plus detritus**: the retrieval and the truth are not the same quantity, so
    the accuracy numbers on those rows carry a known truth-mapping mismatch and
    cannot be read as a clean error budget.

The :math:`\pm 3` nm ``ref_match`` rule
    Reference bands are nominal: **440 and 443 nm** for absorption components
    (``a``, ``a_ph``, ``a_dg``), **555 and 670 nm** for backscatter (``bb``,
    ``bb_p``). Each dataset is scored at the **nearest native band within 3 nm** —
    no interpolation. ``ref_wave`` is the nominal target and ``ref_match`` the
    band actually used, so a row reading ``ref_wave = 555``,
    ``ref_match = 554.2`` is honest about what was measured. A reference band
    with no native match inside the tolerance is **omitted rather than forced**,
    which is why a dataset may carry rows at 443 nm but none at 440 nm.
