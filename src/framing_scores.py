"""
Optional ML-based frame scoring: FrameAxis-style embeddings and zero-shot NLI.

Requires: pip install -r requirements-ml.txt
          (sentence-transformers, transformers, torch)

Two complementary approaches to the dictionary-based assign_frame_flags:

  1. Embedding scoring (FrameAxis-inspired, Kwak et al. 2021):
     Encodes article text and frame keyword centroids with a multilingual
     sentence-transformer; returns cosine-similarity scores (continuous, −1 to 1).

  2. Zero-shot NLI scoring (Laurer et al. 2024):
     Uses MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 to score
     each article against natural-language frame hypotheses; returns entailment
     probabilities (0–1) without any labelled training data.

Both functions return a DataFrame with one column per frame, compatible with
the existing FRAME_DICTS key names from src.dictionaries.

Usage
-----
    from src.framing_scores import assign_frame_scores_embedding, assign_frame_scores_nli
    from src.dictionaries import FRAME_DICTS

    # embedding path (faster, ~500 ms/100 articles on CPU)
    scores = assign_frame_scores_embedding(texts, FRAME_DICTS)

    # NLI path (slower, ~2–5 s/article on CPU; use a GPU or small sample)
    scores = assign_frame_scores_nli(texts)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
_NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

# Natural-language hypotheses for the six governance frames.
# Used by the NLI scorer; phrased to be unambiguous and language-neutral
# (the NLI model handles 100 languages; the premise is the article text).
FRAME_HYPOTHESES: dict[str, str] = {
    "innovation_opportunity": (
        "This article discusses AI innovation, new capabilities, or beneficial applications."
    ),
    "risk_safety": (
        "This article discusses AI safety risks, harms, or dangerous misuse of AI systems."
    ),
    "regulation_governance": (
        "This article discusses AI regulation, law, governance frameworks, or policy."
    ),
    "rights_privacy": (
        "This article discusses AI and privacy, data protection, bias, or human rights."
    ),
    "economic_competition_labour": (
        "This article discusses the economic impact of AI, job displacement, "
        "market competition, or the geopolitical AI race."
    ),
    "misinformation_integrity": (
        "This article discusses AI-generated misinformation, deepfakes, "
        "synthetic media, or threats to information integrity."
    ),
}


# ---------------------------------------------------------------------------
# Embedding-based scoring (FrameAxis-inspired)
# ---------------------------------------------------------------------------

def _load_sentence_transformer(model_name: str = _EMBEDDING_MODEL):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "sentence-transformers is required for embedding scoring. "
            "Install with: pip install -r requirements-ml.txt"
        ) from e
    return SentenceTransformer(model_name)


def _compute_frame_centroids(frame_dicts: dict[str, list[str]], model) -> dict[str, np.ndarray]:
    """Encode each frame's keyword list and return the mean embedding (centroid)."""
    centroids = {}
    for name, keywords in frame_dicts.items():
        embs = model.encode(keywords, show_progress_bar=False, batch_size=64)
        centroids[name] = embs.mean(axis=0)
    return centroids


def assign_frame_scores_embedding(
    texts: list[str],
    frame_dicts: dict[str, list[str]],
    model_name: str = _EMBEDDING_MODEL,
    batch_size: int = 64,
) -> pd.DataFrame:
    """Cosine-similarity scores between article texts and frame keyword centroids.

    Returns a DataFrame (n_articles × 6 frames) with values in [−1, 1].
    Higher values mean the article text is semantically closer to the frame.

    Implements the FrameAxis approach (Kwak et al., 2021 PeerJ CS):
    each frame acts as a semantic axis defined by its keyword centroid.
    """
    model = _load_sentence_transformer(model_name)
    centroids = _compute_frame_centroids(frame_dicts, model)

    article_embs = model.encode(texts, show_progress_bar=True, batch_size=batch_size)

    # Normalise to unit vectors for cosine similarity
    def _normalise(m: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return m / norms

    article_norm = _normalise(article_embs)
    centroid_matrix = np.stack(list(centroids.values()))
    centroid_norm = _normalise(centroid_matrix)

    scores = article_norm @ centroid_norm.T  # (n_articles, n_frames)
    return pd.DataFrame(scores, columns=list(centroids.keys()))


# ---------------------------------------------------------------------------
# Zero-shot NLI scoring
# ---------------------------------------------------------------------------

def _load_nli_pipeline(model_name: str = _NLI_MODEL):
    try:
        from transformers import pipeline
    except ImportError as e:
        raise ImportError(
            "transformers is required for NLI scoring. "
            "Install with: pip install -r requirements-ml.txt"
        ) from e
    return pipeline(
        "zero-shot-classification",
        model=model_name,
        multi_label=True,
    )


def assign_frame_scores_nli(
    texts: list[str],
    hypotheses: dict[str, str] | None = None,
    model_name: str = _NLI_MODEL,
    batch_size: int = 8,
) -> pd.DataFrame:
    """Zero-shot NLI entailment probabilities per frame per article.

    Uses mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 (Laurer et al., 2024)
    — no labelled training data needed, supports 100 languages.

    Returns a DataFrame (n_articles × 6 frames) with values in [0, 1].
    Values are multi-label entailment probabilities (columns do NOT sum to 1).

    First call downloads the model (~700 MB) from HuggingFace.
    Expect ~2–5 seconds per article on CPU; use batch_size=1 if memory-limited.
    """
    hypotheses = hypotheses or FRAME_HYPOTHESES
    classifier = _load_nli_pipeline(model_name)

    label_list = list(hypotheses.keys())
    hypothesis_list = list(hypotheses.values())

    rows = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        results = classifier(batch, hypothesis_list, multi_label=True)
        if isinstance(results, dict):
            results = [results]
        for res in results:
            # results["labels"] is in descending score order; re-align to
            # the original hypothesis order
            score_map = dict(zip(res["labels"], res["scores"]))
            rows.append([score_map.get(h, 0.0) for h in hypothesis_list])

    return pd.DataFrame(rows, columns=label_list)
