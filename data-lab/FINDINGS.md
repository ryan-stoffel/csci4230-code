# Findings: GitHub Repository Preprocessing Lab

Notes from `GitHub_Repos_Preprocessing_Lab.ipynb`. Snapshot taken 2026-09-28; 25,173 public
repositories created between January 2019 and September 2025, reduced to 18,866 after cleaning.

---

## 1. Cleaning cost 25% of the rows, and the losses were not random

| Stage | Rows | Removed |
| --- | --- | --- |
| Raw | 25,173 | — |
| Drop null `description` / `language` | 21,164 | 4,009 |
| Drop empty repos (`size_kb == 0`) and non-English descriptions | 18,866 | 2,298 |

There were no duplicates at all — zero duplicate `repo_id`, `full_name`, or full rows — so every
removal was a missing-data or quality decision.

Missingness before cleaning: `topics` 59.3%, `license` 39.0%, `description` 15.7%, `language` 0.25%.

**None of this is missing at random.** A repository with no description, no topics, and no license is
usually a repository nobody invested in. Filling `license` with `'None'` is therefore not a neutral
imputation — it encodes a weak abandonment signal into what looks like a categorical level. Worth
stating explicitly in any model built on this table.

The non-English filter drops 2,291 rows using an ASCII-letter-share heuristic (`< 0.9`). It works on
the obvious cases (`逃离北上广`, `Разработка веб-сервисов на Golang`) but will also catch legitimate
repositories with emoji-heavy or transliterated descriptions. Acceptable for a lab, a caveat for the
research project.

## 2. Every numeric attribute is severely right-skewed

Raw distributions (pre-cleaning):

| Attribute | Mean | Median | Max | Skew | Kurtosis |
| --- | --- | --- | --- | --- | --- |
| stars | 154.19 | 23 | 110,855 | 36.9 | 2,169.8 |
| forks | 28.48 | 5 | 25,050 | 48.7 | 3,297.4 |
| open_issues | 8.51 | 1 | 9,433 | 69.0 | 5,665.1 |
| size_kb | 33,915.84 | 1,201 | 27,295,925 | 46.5 | 2,950.6 |
| topic_count | 2.55 | 0 | 20 | 1.9 | 3.7 |

Mean stars (154) sits at roughly the 85th percentile. **Report medians, not means, for anything in
this dataset.** Kurtosis in the thousands means a handful of mega-repositories dominate every moment
of the distribution.

Log1p fixes most of it:

| Attribute | Raw skew | Log skew |
| --- | --- | --- |
| stars | 36.87 | 1.66 |
| forks | 48.67 | 0.90 |
| open_issues | 92.60 | 1.04 |
| size_kb | 46.54 | 0.11 |
| topic_count | 1.60 | 0.39 |

Box-Cox on stars (λ = −0.520, close to a reciprocal-root transform) does slightly better than log,
reaching skew 0.26 — but it costs interpretability and cannot handle zeros without a shift, so log1p
is the better default here.

## 3. Nothing is normally distributed

Shapiro-Wilk rejects H₀ at p ≈ 0 for all eight numeric attributes, including the comparatively tame
ones (`age_days` W = 0.954, `active_span_days` W = 0.885). Q-Q plots show heavy right tails
throughout.

Two consequences:

- Use nonparametric tests — Mann-Whitney, Kruskal-Wallis, Spearman — not their parametric twins.
- At n = 18,866, normality tests reject on trivial departures. The W statistic and the plot say more
  than the p-value does. The same caution applies to every p-value below.

## 4. The abandonment label is confounded with repository age

This is the most consequential finding in the lab.

Label distribution: 8,074 abandoned, 3,327 maintained, 7,465 unlabeled.

Abandoned share by creation year:

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| % abandoned | 83.6 | 80.0 | 73.9 | 71.9 | 66.6 | 59.7 | 38.3 |

Perfectly monotone, and it follows directly from the labeling rule: abandoned means no push in 365
days, which a 2019 repository has had seven years to satisfy and a 2025 repository has barely had
time to. **A classifier given age will mostly learn "old = abandoned."**

`z_days_since_push` and `z_active_span_days` are dropped from the final table for exactly this
reason, but `age_days` and `created_year` survive into `final_df` — the same leak one step removed.
Either drop them too, or stratify evaluation by creation year.

One structural note: `days_since_push = age_days − active_span_days` is an exact identity, which PCA
confirms (PC9 explains 0.000 variance). It fails on only 6 rows, where `pushed_at` predates
`created_at` — repositories with imported git history.

## 5. Ownership predicts maintenance better than anything else measured

| Owner type | Median days since last push |
| --- | --- |
| Organization | 401 |
| User | 896 |

A 2.2× gap, Mann-Whitney U p ≈ 1.3e-204. Organizations maintain; individuals drift. For a project
about unmet developer needs, user-owned repositories are where the abandonment signal lives.

## 6. Language matters — but read the effect sizes, not the p-values

Kruskal-Wallis on stars by language: H = 144.4, p ≈ 2.1e-29. χ² of language against maintenance
status: 408.7, dof 5, p ≈ 3.9e-86. Both are inevitable at this sample size.

The real content is the spread:

| Language | n | Median stars | Mean stars | % maintained |
| --- | --- | --- | --- | --- |
| Rust | 1,165 | 28.0 | 329.6 | 44.6 |
| Go | 1,379 | 29.0 | 271.3 | 44.4 |
| TypeScript | 3,268 | 26.0 | 300.2 | 37.5 |
| Java | 1,096 | 21.5 | 69.1 | 33.5 |
| Python | 8,736 | 25.0 | 141.8 | 23.2 |
| JavaScript | 3,222 | 21.0 | 90.9 | 21.4 |

Two separate stories. **Maintenance rates differ about twofold** — Rust and Go nearly double
JavaScript and Python. **Median stars barely differ at all** (21–29 across every language); only the
means diverge, which is tail behavior, not typical-repository behavior. Reporting mean stars by
language would manufacture a difference that the medians say does not exist.

ANOVA on log stars gives F = 37.2, p ≈ 0, agreeing with Kruskal-Wallis.

## 7. Popularity does not keep a repository alive

| Pair | Spearman ρ |
| --- | --- |
| stars vs forks | 0.656 |
| stars vs open_issues | 0.369 |
| stars vs days_since_push | −0.200 |

Stars and forks move together, as expected — forks are downstream of attention. But the link between
popularity and continued activity is weak. Well-starred repositories go stale at close to the base
rate, which is a good motivating fact for the "unmet developer needs" framing: users are left
stranded on projects that look healthy by the metric they can see.

A one-sample t-test confirms the corpus skews stale overall: mean days since last push is 879.5
against the 365-day threshold, t = 97.2, p ≈ 0.

## 8. The feature set is already compact

No pair of transformed features exceeds |r| > 0.8. The strongest are log_stars ↔ log_forks (0.75),
age_days ↔ days_since_push (0.52), and days_since_push ↔ active_span_days (0.50).

PCA needs 6 components to reach 90% of variance (PC1 alone explains only 30.9%), so dimensionality
reduction buys little here. Keep the interpretable features.

Boolean flags are mostly uninformative: `has_wiki` is true for 80.7% of repositories (a GitHub
default, not a choice), while `has_pages` 10.8%, `has_discussions` 9.5%, and `archived` 6.6% are rare
enough to be near-constant. `snapshot_date` has exactly one distinct value and carries no
information.

---

## Output

`github_repos_clean.csv` — 18,866 rows × 33 columns, zero missing values: identifiers, raw counts,
z-scored log features, one-hot encodings for language / owner type / license group, and the
`maintenance_status` label.

## What to fix before modeling

1. Drop `age_days` and `created_year`, or stratify by creation year — otherwise the model learns age.
2. Decide what `unlabeled` (7,465 rows, 40%) means. Dropping them assumes the 90–365 day middle
   ground is missing at random, which the age confound suggests it is not.
3. Treat missing `license` and `topics` as a signal, not as a filled category.
4. Replace the ASCII heuristic with real language detection if this corpus feeds the research project.
