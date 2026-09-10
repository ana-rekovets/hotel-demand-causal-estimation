# Price Effects in Online Hotel Search

Causal estimation of how price affects click-through and booking probability on
a large online travel platform, followed by a structural sequential search
model that separates consumer preferences from search frictions.

Data: the Expedia *Personalizing Hotel Searches* dataset — 9,917,530
hotel–search impressions across 399,344 search sessions and 136,886 properties,
November 2012 to June 2013.

## The identification problem

Two things confound the raw price–demand relationship. Expensive hotels are
better in ways the data does not record, and the platform's ranking algorithm
places hotels on the page partly on the basis of price. Both push the naive
estimate in unknown directions.

The design leans on the `random_bool = 1` subsample (2,939,652 impressions,
29.6% of the data), where the ranking algorithm is switched off and hotels
appear in random order. That provides exogenous variation in display position.
Within-session demeaning then absorbs everything specific to a search —
destination, dates, party composition, the overall price level of the choice
set — so identification comes from comparing a hotel to the alternatives shown
next to it.

## Specifications

Eight models, arranged so that the sample restriction and the estimator change
can be read separately:

| | Estimator | N | Click | Booking |
|---|---|---|---|---|
| M1 | OLS, bivariate | 2,000,000 | −0.0063 | −0.0071 |
| M2 | OLS + quality controls | 2,000,000 | −0.0143 | −0.0116 |
| M3 | OLS + position | 2,000,000 | −0.0148 | −0.0120 |
| M3r | M3, random-order only | 2,933,760 | −0.0114 | −0.0025 |
| M3_IV | M3, on the IV sample | 500,000 | −0.0145 | −0.0118 |
| **M4** | **Within-session FE** | **2,933,760** | **−0.0298** | **−0.0049** |
| M5 | IV / 2SLS | 500,000 | −0.0074 | −0.0092 |
| M6 | DDML (gradient boosting) | 150,000 | −0.0134 | −0.0024 |

All coefficients are semi-elasticities on log price and significant at the 1%
level. M3 → M3r is the pure sample effect; M3r → M4 is the pure estimator
effect.

**Headline estimate.** Under M4, a 10% price increase lowers click probability
by 0.28 percentage points — about 6% of the 4.66% baseline click rate — and
booking probability by 0.047 points, roughly 8.6% of its 0.54% base rate.

## Two findings worth flagging

**Demand is not monotone in price.** Click and booking rates rise from the
cheapest decile to a peak at decile 3–4 (booking 3.36% at a median of \$85)
before declining. The very cheapest listings are not the most clicked, which is
consistent with low price acting as a negative quality signal.

**The instrument fails, and its own estimates say so.** Instrumenting price
with the hotel's historical rate gives a strong first stage (partial
F = 261,010, Shea partial R² = 0.43). But on identical rows, 2SLS is *less*
negative than OLS (−0.0074 vs −0.0145), the opposite of what quality-driven
endogeneity predicts. A correction in the wrong direction is the signature of
an instrument carrying the very quality signal it was meant to remove. M5 is
reported as a diagnostic, not as a causal estimate.

## Sequential search model

Following Ursu, Seiler and Honka (2024), estimated by simulated maximum
likelihood on 2,000 random-order sessions with 300 draws and a subsampled
bootstrap. Search costs rise with depth on the page — about 4.7% per position,
so position 20 costs roughly 2.4× position 1 to reach.

The report is candid that the bootstrap standard errors are implausibly tight
(t-statistics of 62–136 are not credible at this sample size) and treats the
point estimates, not the inference, as the output.

## Repository structure

```
├── notebooks/
│   └── hotel_demand_estimation.ipynb
├── report/
│   ├── hotel_demand_estimation.tex
│   ├── hotel_demand_estimation.pdf
│   └── figures/
├── scripts/
│   ├── check_report_matches_notebooks.py
│   ├── compare_notebook_results.py
│   └── execute_notebook.py
├── .github/workflows/
├── Makefile
├── requirements.txt
└── LICENSE
```

## Reproducibility

Every number in the report traces to a saved notebook output, enforced
mechanically rather than by inspection:

```bash
make verify   # check the report against the notebook outputs (seconds, no data)
make report   # verify, then rebuild the PDF
```

`scripts/check_report_matches_notebooks.py` extracts every number from the
report's LaTeX source and fails if it cannot be found in the executed notebook
outputs. It runs in CI on every push. Report tables are generated
programmatically from the fitted model objects (final notebook cell) rather
than transcribed by hand.

To re-execute the analysis end to end you need the dataset, which is not
redistributable here. Download it from the Kaggle
[Personalize Expedia Hotel Searches](https://www.kaggle.com/c/expedia-personalized-sort)
competition, then:

```bash
EXPEDIA_PARQUET=/path/to/train_processed.parquet make rerun
```

That re-runs the notebook and diffs it against the committed results with
`scripts/compare_notebook_results.py`. The notebook also detects a Kaggle
environment automatically and runs there unchanged.

## Environment

```bash
pip install -r requirements.txt
```

## Author

Anastasiia Rekovets

## AI tool usage

Claude was used as a coding assistant for syntax and debugging, and for a
review pass over the analysis and write-up.
