"""Stage 1a + 1b: Embed messages and reduce dimensionality."""

import json
from pathlib import Path

import numpy as np
import umap
from sentence_transformers import SentenceTransformer

from quarry.paths import (
    CONVERSATIONS,
    EMBEDDINGS,
    REDUCED_EMBEDDINGS,
    ensure_dirs,
)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

UMAP_N_COMPONENTS = 5
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.0
RANDOM_STATE = 42


def load_conversations(
    path: Path = CONVERSATIONS,
) -> tuple[list[str], list[str], list[bool]]:
    """Load conversations.jsonl into three parallel lists."""
    texts, intents, resolved = [], [], []
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            texts.append(row["text"])
            intents.append(row["true_intent"])
            resolved.append(row["was_resolved_by_fin"])
    return texts, intents, resolved


def embed_texts(texts: list[str]) -> np.ndarray:
    """Encode texts with sentence-transformers. Returns (N, 384) array."""
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Embedding {len(texts)} messages...")
    return model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )


def reduce_dims(
    embeddings: np.ndarray,
    n_components: int = UMAP_N_COMPONENTS,
    n_neighbors: int = UMAP_N_NEIGHBORS,
    min_dist: float = UMAP_MIN_DIST,
) -> np.ndarray:
    """UMAP dimensionality reduction. Returns (N, n_components) array."""
    print(f"Reducing {embeddings.shape[1]}D → {n_components}D with UMAP...")
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="cosine",
        random_state=RANDOM_STATE,
    )
    return reducer.fit_transform(embeddings)


def run_embedding_pipeline() -> None:
    """End-to-end: load conversations → embed → reduce → save."""
    ensure_dirs()

    if not CONVERSATIONS.exists():
        raise FileNotFoundError(
            f"{CONVERSATIONS} not found. Run scripts/00_generate_dataset.py first."
        )

    texts, _, _ = load_conversations()
    print(f"Loaded {len(texts)} conversations.\n")

    embeddings = embed_texts(texts)
    np.save(EMBEDDINGS, embeddings)
    print(f"Saved {EMBEDDINGS.name} — shape {embeddings.shape}\n")

    reduced = reduce_dims(embeddings)
    np.save(REDUCED_EMBEDDINGS, reduced)
    print(f"Saved {REDUCED_EMBEDDINGS.name} — shape {reduced.shape}")