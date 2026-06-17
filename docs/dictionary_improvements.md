# Dictionary & Pipeline Improvements

This document records every change made to the keyword dictionaries and processing pipeline, with the reasoning and literature backing for each decision. It is intended as a methods annex for the paper and as a changelog for the lexicon YAML files.

---

## 1. Overview

The pipeline uses four YAML files as a single source of truth:

| File | Purpose |
|---|---|
| `data/lexicons/genai.yaml` | Define what counts as "generative AI" coverage |
| `data/lexicons/governance.yaml` | Filter articles to those with a governance/policy signal |
| `data/lexicons/frames.yaml` | Classify articles into six governance frames |
| `data/lexicons/milestones.yaml` | Define event-study windows around key policy milestones |

Dictionary-based methods have well-documented strengths (transparency, reproducibility, multilingual scalability) and well-documented weaknesses (false positives, static vocabulary, sensitivity to dictionary design choices). The improvements below address the most impactful weaknesses identified through a systematic audit of all four files. For a broader discussion of dictionary vs. embedding vs. transformer approaches, see Widmann & Wich (2023) and Kunjar et al. (2025).

---

## 2. False-Positive Analysis (`src/preprocessing.py`)

### Problem: Substring matching without word boundaries

`assign_frame_flags` in `src/preprocessing.py` used `re.escape(kw)` without word-boundary anchors (`\b`), causing unanchored substring matches. The following terms were identified as high-risk:

| Term | Frame | False-positive substring | Example false-positive context |
|---|---|---|---|
| `lies` | risk_safety | "re**lies**", "a**llies**", "fami**lies**", "sup**plies**" | "Europe re**lies** on US safety standards" |
| `harm` | risk_safety | "p**harm**acy", "p**harm**a" | "AI applications in p**harm**acy" |
| `race` | economic | "em**brace**", "g**race**" | "Brussels will em**brace** new rules" |
| `ban` | regulation | "ur**ban**", "a**ban**don" | "ur**ban** AI deployment policies" |
| `law` | regulation | "f**law**", "f**law**s" | "critics point to f**law**s in the AI Act" |
| `coding` | innovation | "en**coding**", "de**coding**" | "video en**coding** pipeline" |

### Fix

Single-word terms (those without a space) are now wrapped in `\b` anchors in `assign_frame_flags`:

```python
pattern = "|".join(
    (r"\b" + re.escape(kw) + r"\b") if " " not in kw else re.escape(kw)
    for kw in keywords
)
```

Multi-word phrases (e.g. `arms race`, `ai safety`, `large language model`) are left as plain substrings because `\b` at phrase boundaries interacts poorly with hyphens and accented characters, and multi-word phrases are already specific enough not to require it.

**Scope:** This fix applies only to the Python-side `assign_frame_flags`. The BigQuery `LIKE` clauses in `extract_genai_gov.sql` do not support `\b`; given the dual GenAI+governance corpus filter already applied, residual SQL false-positive rates are acceptable.

---

## 3. Frame Size Imbalance (`src/preprocessing.py`, `src/analysis.py`)

### Problem: Larger dictionaries inflate hit counts

Term counts per frame (all languages flattened):

| Frame | Terms (approx.) |
|---|---|
| economic_competition_labour | ~225 |
| regulation_governance | ~186 |
| innovation_opportunity | ~176 |
| risk_safety | ~173 |
| rights_privacy | ~168 |
| misinformation_integrity | ~168 |

`economic_competition_labour` has ~34% more terms than `rights_privacy`. Because `assign_dominant_frame` selects the frame with the highest raw hit count, and because `frame_shares_agg` sums raw hits before normalising, the economic frame has a structural advantage unrelated to actual article content.

### Fix A: Normalise `assign_dominant_frame` by dictionary size

Before taking the argmax, each frame's hit count is divided by its keyword count:

```python
frame_sizes = pd.Series({col: len(FRAME_DICTS[col.replace("frame_", "")]) for col in present_cols})
df["dominant_frame"] = df[present_cols].div(frame_sizes).idxmax(axis=1)...
```

### Fix B: Change the normalisation denominator in `frame_shares_agg` and `frame_shares`

**Before:** `shares = hits / hits.sum(axis=1)` — each frame's share of total keyword hits. This denominator exceeds `total_articles` for multi-label articles, making the interpretation ambiguous.

**After:** `shares = hits / total_articles` — fraction of that month's articles mentioning each frame. Because frames are multi-label, column values can sum to more than 1; this is expected and interpretable (e.g. 0.6 means 60% of that month's articles mentioned the frame at least once).

The same fix is applied to `event_study_agg` and `event_study` in `src/analysis.py`.

**Note for figures:** Figure 2 (monthly frame shares) values will now exceed 1 in total for some months. This should be documented in the caption: *"Frame prevalence rates: fraction of monthly articles matching each frame keyword list; frames are multi-label so rates do not sum to 1."*

---

## 4. GenAI Lexicon Gap: 2024–2026 Terms (`data/lexicons/genai.yaml`)

The original `genai_lexicon` was compiled around the November 2022 ChatGPT launch. The study window extends to June 2026, covering several major developments that the original lexicon misses entirely:

| Added term | Rationale |
|---|---|
| `openai` | The company's name was absent despite `anthropic` being listed; OpenAI appears as a named entity in the vast majority of GenAI coverage |
| `gpt-4o`, `gpt4o` | OpenAI's multimodal flagship (May 2024) drove a measurable coverage spike |
| `deepseek` | The DeepSeek-R1 release (January 2025) was the single largest non-ChatGPT GenAI news event in the study period |
| `sora` | OpenAI's text-to-video model (December 2023) opened a new AI governance debate on synthetic media |
| `mistral ai` | The leading European open-weight model company; central to EU AI Act compliance discussions |
| `ai agent`, `agentic ai` | "Agentic AI" became the dominant framing of AI capability in 2024–2025 policy discourse |
| `reasoning model` | Introduced with OpenAI o1 (September 2024); associated with new risk and governance debates |

Corresponding multilingual contextual variants (`agent ia`, `ki-agent`, `agente ia`, etc.) were added to `genai_lexicon_contextual` for all eight project languages.

After any change to `genai.yaml`, regenerate the SQL with:
```bash
python src/build_query.py --write
```

---

## 5. Conservative Term Cleanup (`data/lexicons/frames.yaml`)

The word-boundary fix (Section 2) resolves most substring false-positive issues. Two terms remain noisy even as whole words and were removed:

### Removed: `help you` from `innovation_opportunity.en`

Fires on any customer-service or tutorial framing ("to help you understand", "designed to help you navigate"). The innovation signal is fully captured by `assistant`, `automate`, `workflow`, and `augment` which remain.

### Removed: bare `race` from `economic_competition_labour.en`

"Race" as a standalone word fires on "human race", "race relations", "race car", and marathon contexts. The geopolitical meaning is already covered by `arms race`, `ai race`, `race for`, `race to`, and `race with`, which all remain.

All other potentially noisy terms (`lies`, `harm`, `ban`, `law`, `coding`) are now adequately constrained by the `\b` word-boundary fix and were kept.

---

## 6. FrameAxis Embedding Scoring (`src/framing_scores.py`)

### Method

FrameAxis (Kwak et al., 2021, *PeerJ Computer Science*) scores each document on continuous "microframe" axes using word embedding geometry. The core idea: encode a frame's keywords as a centroid in embedding space, then measure how closely an article's text aligns with that centroid.

Our implementation uses `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` — a 278M-parameter multilingual model trained on paraphrase tasks, covering all 9 project languages. For each article:

1. Encode the `Quotations` text (or URL-derived headline as fallback).
2. Encode all keywords per frame and compute the mean embedding (centroid).
3. Compute cosine similarity between article embedding and each frame centroid.

The result is a continuous score in [−1, 1] per frame per article — richer than binary match counts and not sensitive to dictionary size.

### Advantage over keyword counting

- Captures semantic similarity even when exact keywords are absent ("data privacy breach" would score high on `rights_privacy` even without the literal keyword `data protection`).
- Works on any language (model handles 100 languages) without requiring language-specific keyword translations.
- Score is continuous, enabling time-series analysis of framing *intensity* rather than just presence.

### Usage

```bash
pip install -r requirements-ml.txt
python scripts/run_framing_scores.py --method embedding --n 500
```

Output: `data/interim/framing_scores_embedding_500.parquet` with 6 cosine-similarity columns alongside the original `frame_*` integer columns for direct comparison.

---

## 7. Zero-Shot NLI Scoring (`src/framing_scores.py`)

### Method

Zero-shot NLI classification (Laurer et al., 2024, *Political Analysis*) frames text classification as a natural language inference task: given an article (premise) and a frame description (hypothesis), the model predicts whether the premise *entails* the hypothesis.

We use `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` — fine-tuned on XNLI and a 2.7M-pair multilingual NLI dataset, achieving 87.1% accuracy on the XNLI test set across 100 languages.

Frame hypotheses:

| Frame | Hypothesis |
|---|---|
| innovation_opportunity | "This article discusses AI innovation, new capabilities, or beneficial applications." |
| risk_safety | "This article discusses AI safety risks, harms, or dangerous misuse of AI systems." |
| regulation_governance | "This article discusses AI regulation, law, governance frameworks, or policy." |
| rights_privacy | "This article discusses AI and privacy, data protection, bias, or human rights." |
| economic_competition_labour | "This article discusses the economic impact of AI, job displacement, market competition, or the geopolitical AI race." |
| misinformation_integrity | "This article discusses AI-generated misinformation, deepfakes, synthetic media, or threats to information integrity." |

### Advantage over keyword counting

- No keyword list needed: the model generalises from the natural-language hypothesis to semantically equivalent article text in any language.
- Returns soft probabilities (0–1, multi-label), enabling confidence-weighted analysis.
- Directly comparable to the dictionary approach: run on the same sample and compute correlation.

### Usage

```bash
pip install -r requirements-ml.txt
python scripts/run_framing_scores.py --method nli --n 100
# First run downloads the model (~700 MB) from HuggingFace
```

Output: `data/interim/framing_scores_nli_100.parquet`.

---

## 8. Dictionary vs. ML Tradeoffs

Widmann & Wich (2023, *Political Analysis*) benchmark dictionary, word-embedding, and transformer models for measuring discrete emotions in German political text. Their key finding: transformer models consistently outperform dictionaries on accuracy, but dictionaries remain preferable when transparency, reproducibility, and multilingual coverage matter.

For this project:
- The **dictionary approach** remains the primary method for all figures and statistics. It is fully auditable (every keyword visible in YAML), reproducible without ML infrastructure, and directly usable in BigQuery SQL for the corpus extraction step.
- The **ML scoring tools** (`src/framing_scores.py`) serve as optional validation: running them on a 300–500 article sample and computing Pearson/Spearman correlations with the dictionary scores tests whether the two approaches agree. High correlation would strengthen the paper's methodological claim; low correlation on specific frames would identify where the dictionary has weaknesses.
- Gilardi et al. (2023) and Ziems et al. (2024) show that LLM-based annotation (GPT-4, Claude) achieves κ = 0.40–0.65 on CSS framing tasks. A future improvement would be to annotate a gold-standard sample with an LLM and report agreement with the dictionary — this is the most credible validation approach for a methods section.

---

## 9. New BibTeX Entries Added to `references.bib`

The following 8 entries were appended. Cite as `\cite{key}` in the paper:

| Key | Reference |
|---|---|
| `gilardi_chatgpt_2023` | Gilardi et al. (2023), *PNAS* — ChatGPT outperforms crowd workers for text annotation |
| `ziems_large_2024` | Ziems et al. (2024), *Computational Linguistics* — Can LLMs transform computational social science? |
| `kwak_frameaxis_2021` | Kwak et al. (2021), *PeerJ CS* — FrameAxis: microframe bias and intensity with word embedding |
| `schindler_lgde_2025` | Schindler et al. (2025), *Computational Linguistics* — LGDE: Local Graph-based Dictionary Expansion |
| `kunjar_computational_2025` | Kunjar et al. (2025), arXiv 2511.17746 — Computational frame analysis revisited: LLMs for news coverage |
| `pastorino_decoding_2024` | Pastorino et al. (2024), arXiv 2402.11621 — Decoding news narratives: LLMs in framing bias detection |
| `laurer_less_2024` | Laurer et al. (2024), *Political Analysis* — Less annotating, more classifying: BERT-NLI |
| `widmann_creating_2023` | Widmann & Wich (2023), *Political Analysis* — Dictionary vs. embedding vs. transformer for political text |
