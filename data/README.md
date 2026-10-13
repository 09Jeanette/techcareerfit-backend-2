# Market data

Put the Kaggle **AI Jobs Market 2025-2026** export here as `ai_jobs_market.csv`, prepared with these columns:

| column | example |
|---|---|
| role | Junior Python Developer |
| month | 1-12 |
| postings | 42 |
| salary_min | 18000 |
| salary_max | 28000 |
| remote_share | 0.38 |
| region | Gauteng |
| skills | python;sql;docker |

If the file is missing or the columns differ, the API uses the built-in sample data in `app/services/market.py`.
Change `load_csv` there if your export uses different column names.
