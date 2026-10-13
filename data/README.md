# Market data

`ai_jobs_market_2025_2026.csv` is the Kaggle **AI Jobs Market 2025-2026** dataset used by the Market insights page.

- 1,500 job postings from January 2025 to March 2026
- 25 AI job titles in 12 categories, four experience levels (Entry, Mid, Senior, Lead)
- Salaries are **annual, in US dollars**
- 14 countries plus "Global". **There are no South African postings**, so the app labels the data as global.

Columns used by `app/services/market.py`: `job_title`, `job_category`, `experience_level`, `annual_salary_usd`,
`country`, `remote_work`, `required_skills` (pipe-separated), `demand_score`, `demand_growth_yoy_pct`,
`posting_year`, `posting_month`.

Before submitting, record the dataset's author, Kaggle URL and licence from the dataset page in your
documentation. The distribution of the data (for example, almost equal numbers of postings per experience
level and education level) suggests it may be synthetic, so check the dataset description and say so if it is.

To use a different file, set `MARKET_CSV_PATH`. It must have the same columns.
