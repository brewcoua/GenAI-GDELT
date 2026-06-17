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

from typing import Any

import numpy as np
import pandas as pd

_EMBEDDING_MODEL = "sentence-transformers/LaBSE"
_NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

_MODEL_CACHE: dict[str, Any] = {}
_CENTROID_CACHE: dict[tuple, dict[str, np.ndarray]] = {}


def _get_device() -> str:
    """Return 'cuda' if a GPU is available (covers NVIDIA CUDA and AMD ROCm), else 'cpu'."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"

# Natural-language hypotheses for the six governance frames.
# Used by the NLI scorer; phrased to be unambiguous and language-neutral
# (the NLI model handles 100 languages; the premise is the article text).
FRAME_HYPOTHESES: dict[str, str] = {
    "innovation_opportunity": (
        "This article discusses AI innovation, new capabilities, or beneficial applications of AI."
    ),
    "risk_safety": (
        "This article discusses AI safety risks, harms, accidents, or dangerous misuse of AI systems."
    ),
    "regulation_governance": (
        "This article discusses AI regulation, legislation, governance frameworks, or public policy for AI."
    ),
    "rights_privacy": (
        "This article discusses AI and privacy, personal data protection, algorithmic bias, or civil rights."
    ),
    "economic_competition_labour": (
        "This article discusses AI and jobs, automation replacing workers, economic inequality, "
        "or countries competing in AI development."
    ),
    "misinformation_integrity": (
        "This article discusses AI-generated fake news, deepfakes, synthetic media, "
        "or AI used to spread disinformation and deceive people."
    ),
}


# ---------------------------------------------------------------------------
# Embedding-based scoring (FrameAxis-inspired)
# ---------------------------------------------------------------------------

def _load_sentence_transformer(model_name: str = _EMBEDDING_MODEL):
    if model_name not in _MODEL_CACHE:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for embedding scoring. "
                "Install with: pip install -r requirements-ml.txt"
            ) from e
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name, device=_get_device())
    return _MODEL_CACHE[model_name]


def _compute_frame_centroids(
    frame_dicts: dict[str, list[str]], model, model_name: str
) -> dict[str, np.ndarray]:
    """Encode each frame's keyword list and return the mean embedding (centroid)."""
    key = (model_name, tuple(sorted(frame_dicts.keys())))
    if key not in _CENTROID_CACHE:
        centroids = {}
        for name, keywords in frame_dicts.items():
            embs = model.encode(keywords, show_progress_bar=False, batch_size=64)
            centroids[name] = embs.mean(axis=0)
        _CENTROID_CACHE[key] = centroids
    return _CENTROID_CACHE[key]


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
    centroids = _compute_frame_centroids(frame_dicts, model, model_name)

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
        device=_get_device(),
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

    # The pipeline rejects empty strings; replace them with a neutral placeholder.
    texts = [t if t and t.strip() else "." for t in texts]

    # Wrap in a Dataset so the pipeline uses GPU-efficient DataLoader batching
    # instead of sequential per-item processing.
    try:
        from torch.utils.data import Dataset as _TorchDataset

        class _TextDataset(_TorchDataset):
            def __init__(self, data: list[str]) -> None:
                self.data = data
            def __len__(self) -> int:
                return len(self.data)
            def __getitem__(self, i: int) -> str:
                return self.data[i]

        iterable = classifier(
            _TextDataset(texts),
            candidate_labels=hypothesis_list,
            multi_label=True,
            batch_size=batch_size,
        )
    except ImportError:
        # Fallback when torch is not installed (shouldn't happen if NLI is running).
        iterable = classifier(texts, hypothesis_list, multi_label=True)

    rows = []
    for res in iterable:
        score_map = dict(zip(res["labels"], res["scores"]))
        rows.append([score_map.get(h, 0.0) for h in hypothesis_list])

    return pd.DataFrame(rows, columns=label_list)
