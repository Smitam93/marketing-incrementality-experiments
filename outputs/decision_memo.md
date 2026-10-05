# Synthetic marketing decision memo

The channel suppression experiment estimates 10,681 incremental conversions over 28 days across 24 suppressed geos (95% paired-t CI: 9,480 to 11,882). Estimated incremental revenue ROAS is 1.55 (95% CI: 1.38 to 1.73). This uses all-channel conversions, not attributed channel conversions.

The paired randomization p-value is 0.0001; inference uses 24 randomized pairs, not 4,032 independent geo-day rows. The preperiod placebo difference is 0.39 conversions per geo-day and is a diagnostic, not proof of parallel trends.

Interpretation: the interval estimates the channel contribution in these test markets and dates. Revenue ROAS does not equal profit ROAS. At a hypothetical 60% gross margin the revenue break-even iROAS would be 1/0.60 = 1.67; compare the full interval with that threshold before recommending spend. These results cannot establish lifetime value, annual channel impact, or marginal returns from doubling budgets.

Assumptions: no cross-geo spillover; channel actually disabled; matching and budgets fixed before randomization; stable revenue per conversion. Paired-t confidence intervals are approximate; sign-flip testing is valid under the sharp null and the within-pair random assignment. A non-random historical rollout would need stronger identification and robustness checks.

Next: examine pair heterogeneity, run a longer confirmatory test, and measure contribution and customer quality before scaling.
