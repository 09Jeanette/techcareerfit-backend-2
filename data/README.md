# Data

## Market insights: `ai_jobs_market_2025_2026.csv`

Kaggle **AI Jobs Market 2025-2026**: 1,500 job postings from January 2025 to March 2026, 25 AI job titles,
four experience levels, annual salaries in **US dollars**, 14 countries plus "Global". **There are no South
African postings**, so the app labels the data as global. Used by `app/services/market.py`.

## Learning roadmap: `courses.csv`

Built from two Kaggle course datasets in `raw/` by `python -m scripts.build_courses`:

| Raw file | Rows kept | Notes |
|---|---|---|
| `raw/coursera_course_dataset_v3.csv` | courses that teach at least one recognised skill | 220 rows have no URL and a few URLs belong to another course; those get a Coursera search link and `link_type=search` |
| `raw/edx.csv` | English courses that teach at least one recognised skill | Titles lost spaces at line breaks; the script repairs most of them |

Each course is tagged with the same canonical skills the CV scanner uses (`app/services/ats.py`), so a missing
skill in a report maps directly to courses. `app/services/courses.py` ranks them: skill named in the title,
focused on few skills, beginner level, rating, review count and a direct link.

Skills with no course in either dataset (for example FastAPI, TypeScript, LangChain, RAG, CUDA) fall back to
the built-in links in `app/services/learning.py`. Admin-curated resources always appear first.

The Udemy, Skillshare and older Coursera files from the same downloads were not used: they have no course
links or no skills column.

## Before submitting

Record each dataset's author, Kaggle URL and licence in your references. The jobs dataset looks synthetic
(almost equal postings per experience and education level), so check its description and say so if it is.
