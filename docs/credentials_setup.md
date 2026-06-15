# GCP Credentials Setup for BigQuery

**Short answer: this project can be done for free.** The BigQuery Sandbox gives you
1 TB of query processing per month with no credit card and no billing account.
Our queries — if you select only the columns you need and do aggregation in SQL
rather than downloading raw rows — should stay well below that limit.

---

## Option A — BigQuery Sandbox (free, no credit card)

### 1. Create a Google account and open BigQuery

Go to [console.cloud.google.com/bigquery](https://console.cloud.google.com/bigquery)
and sign in with any Google account. Google will prompt you to create a project.
**Do not enable billing.** The sandbox activates automatically when billing is off.

You get:
- **1 TB of query processing per month** — free, resets monthly
- **10 GB of storage** for tables you save
- No credit card required, no charge if you stay within limits

The GDELT table (`gdelt-bq.gdeltv2.gkg_partitioned`) is a public dataset hosted
by Google — you don't need to own it or pay for it, you just pay for the queries
you run against it using your own project's quota.

### 2. Install the Google Cloud CLI

```bash
# Linux / WSL
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# macOS (Homebrew)
brew install --cask google-cloud-sdk
```

### 3. Log in

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID   # shown in BigQuery console top-left
gcloud auth application-default login       # used by the Python client
```

### 4. Set your project ID for the notebooks

Copy `.env.example` to `.env` and fill in your project ID:

```
BIGQUERY_PROJECT=your-project-id
```

The Python client then needs nothing else:

```python
import os
from google.cloud import bigquery

client = bigquery.Client(project=os.environ["BIGQUERY_PROJECT"])
```

---

## How to stay within the 1 TB free limit

**Always check before running.** In the BigQuery Console, paste your SQL and look at
the top-right — it shows the bytes to be scanned before you click Run.

**Use the partition filter on every query.** The line
`WHERE DATE(_PARTITIONTIME) >= '...' AND DATE(_PARTITIONTIME) <= '...'`
is not optional — without it, BigQuery scans the entire table (~10 years of data).
With it, only the days in your range are read.

**Do not download raw rows.** The biggest cost risk is running the full extraction
and downloading millions of rows to process locally. Instead, push the heavy work
into SQL — count keyword hits and group by month *inside BigQuery*, then download
only the aggregated result (a few hundred rows).

Example: instead of extracting all matching articles and frame-labeling them in
Python, run a query like:

```sql
SELECT
  DATE_TRUNC(PARSE_DATE('%Y%m%d', SUBSTR(CAST(DATE AS STRING), 1, 8)), MONTH) AS month,
  COUNTIF(LOWER(Quotations) LIKE '%regulation%' OR LOWER(Quotations) LIKE '%governance%') AS reg_gov_hits,
  COUNTIF(LOWER(Quotations) LIKE '%risk%' OR LOWER(Quotations) LIKE '%safety%') AS risk_hits,
  COUNT(*) AS total
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE(_PARTITIONTIME) >= '2022-11-01'
  AND DATE(_PARTITIONTIME) <= '2026-06-30'
  AND (LOWER(AllNames) LIKE '%chatgpt%' OR LOWER(AllNames) LIKE '%openai%')
  AND LOWER(Quotations) LIKE '%regulation%'
GROUP BY month
ORDER BY month
```

This scans the same data but returns ~40 rows instead of millions.

**Rough scan estimates for this project** (selecting 3–4 columns, 3.5-year window):

| Query | Estimated scan | Within free tier? |
|---|---|---|
| Explore query, 1 month | ~15 GB | Yes — use freely |
| Monthly volume count, full range | ~60 GB | Yes |
| Aggregated frame counts, full range | ~150–300 GB | Yes |
| Full raw extraction (all rows, 8 cols) | ~500 GB–1 TB | Likely yes, but check first |

The numbers above are estimates — always verify in the console before running.
If a single query would exceed your remaining monthly quota, BigQuery will reject
it before charging you anything (sandbox mode).

---

## Option B — GDELT DOC 2.0 API (completely free, no account needed)

For RQ1 (monthly volume) and the volume component of RQ3 (event study), you can
skip BigQuery entirely and use GDELT's own free REST API.

The **DOC 2.0 API** returns time-series data for any keyword query:

```
https://api.gdeltproject.org/api/v2/doc/doc?query=chatgpt+regulation&mode=timelinevol&format=json&startdatetime=20221101000000&enddatetime=20260601000000
```

Key parameters:

| Parameter | Description |
|---|---|
| `query` | Space-separated keywords (uses AND logic); quote phrases |
| `mode=timelinevol` | Returns a monthly/weekly article count time series |
| `mode=timelinetone` | Returns average tone over time |
| `startdatetime` / `enddatetime` | `YYYYMMDDhhmmss` format; covers back to Jan 2017 |
| `format=json` or `format=csv` | Output format |

Example Python usage:

```python
import requests
import pandas as pd

params = {
    "query": '"generative ai" regulation',
    "mode": "timelinevol",
    "format": "json",
    "startdatetime": "20221101000000",
    "enddatetime": "20260601000000",
    "timespan": "CUSTOM",
}
resp = requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params)
data = resp.json()
df = pd.DataFrame(data["timeline"][0]["data"])
df["datetime"] = pd.to_datetime(df["date"])
```

**Limitations of the DOC 2.0 API:**
- Returns article volume and tone, but not the raw text or theme codes — you cannot
  use it for the frame detection step (that still requires BigQuery or direct downloads)
- Results reflect GDELT's internal ranking, not a strict keyword count, so treat
  them as approximate volume signals rather than exact corpus counts

**Recommended split:**
- Use the DOC 2.0 API for quick volume sanity checks and to cross-validate RQ1
- Use BigQuery (sandbox) for the frame detection that requires `AllNames` and
  `Quotations` field access

---

## Verify your BigQuery connection

```python
from google.cloud import bigquery
import os

client = bigquery.Client(project=os.environ.get("BIGQUERY_PROJECT", "YOUR_PROJECT_ID"))

sql = """
SELECT DATE, SourceCommonName
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE(_PARTITIONTIME) = '2023-01-01'
LIMIT 1
"""
row = next(client.query(sql).result())
print("Connected. Sample date:", row.DATE)
```

This scans roughly 1–2 GB — well within the free limit.
