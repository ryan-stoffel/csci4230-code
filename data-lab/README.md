# Week-03 Lab: Preprocessing GitHub Repositories

Statistics and preprocessing lab over a sample of ~25k public GitHub repositories created between
2019 and September 2025. The corpus is the repository-level dataset for the course research project,
*Mining GitHub for Unmet Developer Needs*.

The notebook covers descriptive statistics, distribution checks (skew, kurtosis, Q-Q, Shapiro-Wilk),
parametric and nonparametric hypothesis tests, log/Box-Cox transforms, one-hot encoding,
standardization, and PCA — ending in an analysis-ready feature table.

## Files

| File | Description |
| --- | --- |
| `GitHub_Repos_Preprocessing_Lab.ipynb` | The lab, with all outputs |
| `github_repos_2019_2025.csv` | Raw input, one row per repository |
| `github_repos_clean.csv` | Output: 18,866 rows × 33 columns, no missing values |
| `github_collector/collect.py` | Queries the GitHub Search API and writes paged JSON to `raw/` |
| `github_collector/flatten.py` | Flattens those pages into the raw CSV |

`raw/` is not committed — rerun `collect.py` to regenerate it. Set `GITHUB_TOKEN` first to raise the
search limit from 10 to 30 requests per minute.

## Running the notebook

```sh
uv venv .venv
uv pip install --python .venv pandas seaborn numpy matplotlib scikit-learn ipykernel
```

Select `.venv` as the kernel and run all cells. The notebook also runs in Colab, where it mounts
Google Drive and reads the CSV from `Data-Mining/Labs/Week-3-Lab/`.

## A few findings

- Every numeric attribute is severely right-skewed (open_issues skew 92.6, stars 36.9). Log1p brings
  them to roughly 0.1–1.7; Shapiro-Wilk rejects normality everywhere, so nonparametric tests are used.
- Repository age confounds the abandonment label: 83.6% of 2019 repos are labeled abandoned versus
  38.3% of 2025 repos, because the rule is "no push in 365 days."
- Organization-owned repos go half as long without a push as user-owned ones (median 401 vs 896 days).
- Stars barely predict activity (Spearman −0.20 against days since last push).
