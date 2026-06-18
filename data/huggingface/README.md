---
license: cc-by-4.0
language:
- multilingual
task_categories:
- text-classification
tags:
- generative-ai
- ai-governance
- news-framing
- gdelt
- computational-social-science
- web-science
size_categories:
- 1M<n<10M
configs:
- config_name: articles
  data_files: articles.parquet
  description: "1,116,091 article-level records with keyword flags and LaBSE embedding scores for six governance frames."
- config_name: event_studies
  data_files: event_studies.parquet
  description: "Pre/post frame prevalence for 11 AI governance milestones (adaptive symmetric windows)."
- config_name: aggregates
  data_files:
  - path: aggregates/monthly_frames.parquet
    split: monthly_frames
  - path: aggregates/monthly_volume.parquet
    split: monthly_volume
  - path: aggregates/regional_frames.parquet
    split: regional_frames
  - path: aggregates/regional_frames_quarterly.parquet
    split: regional_frames_quarterly
  - path: aggregates/tone_monthly.parquet
    split: tone_monthly
  - path: aggregates/tone_by_frame.parquet
    split: tone_by_frame
  - path: aggregates/tone_by_region.parquet
    split: tone_by_region
  description: "Monthly, regional, and tone aggregates derived from the article corpus."
---

# GenAI Governance Framing in Online News (GDELT 2.0, 2022–2026)

This dataset accompanies the paper:

> **Framing Generative AI Governance in Online News: A Longitudinal Analysis of 1.1 Million Articles (2022–2026)**  
> Brewen Couaran, Yuvraj Singh Pathania, Arjun Rajesh Nair · 2026  
> Code & paper: [github.com/brewcoua/GenAI-GDELT](https://github.com/brewcoua/GenAI-GDELT)  
> Companion site: [brewcoua.github.io/GenAI-GDELT](https://brewcoua.github.io/GenAI-GDELT)

## Dataset overview

1,116,091 online news articles from the [GDELT 2.0 Global Knowledge Graph](https://www.gdeltproject.org/), queried via Google BigQuery, covering **November 2022 – June 2026** (44 months). Articles were selected using a two-condition filter: a 34-term generative AI lexicon AND a governance signal (policy keywords, GDELT thematic codes, or URL slug patterns).

Each article is annotated with a **six-category governance frame taxonomy** via a two-stage procedure:
1. **Keyword matching** — multilingual dictionaries across 9 languages (318 English terms, 959 total)
2. **LaBSE embedding confirmation** — cosine similarity between the article embedding and the frame's positive/negative pole centroids (FrameAxis method, Kwak et al. 2021)

A frame is *confirmed* when both the keyword flag fires and the embedding score is positive.

## Configurations

### `articles` — article-level records (1,116,091 rows)

| Column | Type | Description |
|--------|------|-------------|
| `document_id` | string | Source URL (GDELT DocumentIdentifier) |
| `month` | string | Publication month (YYYY-MM) |
| `region` | string | Source geography: US / EU / UK / Other |
| `dominant_frame` | string | Frame with highest normalized keyword count (null if unconfirmed) |
| `kw_innovation_opportunity` | int8 | 1 = keyword match fired for this frame |
| `kw_risk_safety` | int8 | |
| `kw_regulation_governance` | int8 | |
| `kw_rights_privacy` | int8 | |
| `kw_economic_competition_labour` | int8 | |
| `kw_misinformation_integrity` | int8 | |
| `emb_innovation_opportunity` | float32 | LaBSE bipolar embedding score (−1 to +1) |
| `emb_risk_safety` | float32 | |
| `emb_regulation_governance` | float32 | |
| `emb_rights_privacy` | float32 | |
| `emb_economic_competition_labour` | float32 | |
| `emb_misinformation_integrity` | float32 | |

A frame is **confirmed** when `kw_* == 1` AND `emb_* > 0`. 40.8% of articles (455,349) are confirmed in at least one frame.

**Note on the Regulation & Governance frame:** Its base rate (16.6%) is likely structurally elevated because the corpus governance filter shares vocabulary with this frame's keyword dictionary. Cross-frame comparisons measure relative emphasis rather than absolute prevalence.

### `event_studies` — milestone event study results (22 rows)

Pre/post window mean frame prevalence for 11 AI governance milestones (8 with windows ≥ 21 days + 3 short-window indicative events). Window length = min(d_prev, d_next, 90 days).

| Column | Description |
|--------|-------------|
| `milestone` | Milestone identifier slug |
| `milestone_date` | Date (YYYY-MM-DD) |
| `window_days` | Symmetric window length in days |
| `side` | `pre` or `post` |
| `n_articles` | Article count in this window-side |
| `reg_governance` … `misinformation_integrity` | Mean confirmed frame prevalence |

### `aggregates` — summary statistics

Seven splits of precomputed aggregates: `monthly_volume`, `monthly_frames`, `regional_frames`, `regional_frames_quarterly`, `tone_monthly`, `tone_by_frame`, `tone_by_region`.

## Frame taxonomy

| Frame | Description |
|-------|-------------|
| Innovation & Opportunity | Benefits, transformative potential, market opportunities |
| Risk & Safety | Harms, threats, safety risks, existential concerns |
| Regulation & Governance | Laws, oversight, compliance, institutional steering |
| Rights & Privacy | Data protection, civil liberties, copyright, fairness |
| Economic Competition & Labour | Jobs, automation, market dynamics, national AI competition |
| Misinformation & Integrity | Deepfakes, disinformation, election integrity |

## Data provenance & license

Source data: GDELT 2.0 Global Knowledge Graph (Leetaru & Schrodt, 2013), released under **Creative Commons Attribution** (CC-BY). This derived dataset is released under **CC-BY 4.0**.

The raw article text is not included. `document_id` contains the source URL; full text must be retrieved independently. GDELT `AllNames` (named entities) and `Quotations` (direct speech) fields were used for frame assignment but are not redistributed here.

## Citation

```bibtex
@inproceedings{couaran_framing_2026,
  title     = {Framing Generative {AI} Governance in Online News:
               A Longitudinal Analysis of 1.1 Million Articles (2022--2026)},
  author    = {Couaran, Brewen and Pathania, Yuvraj Singh and Nair, Arjun Rajesh},
  year      = {2026},
  url       = {https://github.com/brewcoua/GenAI-GDELT},
}
```

## Related links

- Paper source (LaTeX): [github.com/brewcoua/GenAI-GDELT/paper](https://github.com/brewcoua/GenAI-GDELT/tree/master/paper)
- Companion website: [brewcoua.github.io/GenAI-GDELT](https://brewcoua.github.io/GenAI-GDELT)
- Frame dictionaries: [github.com/brewcoua/GenAI-GDELT/data/lexicons](https://github.com/brewcoua/GenAI-GDELT/tree/master/data/lexicons)
