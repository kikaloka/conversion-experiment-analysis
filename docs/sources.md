# Sources and provenance

## Original data

- Published CSV: https://video.udacity-data.com/topher/2023/February/63f67d64_ab_data/ab_data.csv
- Retrieved 2026-10-27. Original retained locally at `data/original/ab_data.csv`.
- 1,048,891 bytes; 69,889 rows, three columns: country, group, converted.
- SHA-256: `8c1ce3d02b7b195c1f40a1c278ba8c2f807295874c302efb61812ba226ce43ac`.
- Public accessibility is not a redistribution license. Redistribution rights were not established; the original CSV and any row-level data are excluded from the publication candidate. No license is claimed for upstream data.
- This is educational experiment data. Real-world collection, independent units, event definition and randomization cannot be verified from the CSV. Country codes are interpreted conventionally; no additional columns or identities are invented.

## Methods

- [Statsmodels two-proportion z test](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportions_ztest.html).
- [Statsmodels two-independent-proportions confidence interval](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.confint_proportions_2indep.html).
- [Statsmodels logistic regression](https://www.statsmodels.org/stable/generated/statsmodels.discrete.discrete_model.Logit.html).

The notebook and analysis code specify all actual choices. Alpha=0.05, the two-sided primary test and country adjustment are retrospective analyst choices, not a claimed preregistration. No simulated business assumptions, revenue, costs or MDE are used.
