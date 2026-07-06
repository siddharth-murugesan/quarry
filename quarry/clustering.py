"""Stage 1c: Discover clusters in the reduced embeddings using HDBSCAN."""

import json
from collections import Counter

import hdbscan
import numpy as np

from quarry.embedding import load_conversations
from quarry.paths import CLUSTERS, REDUCED_EMBEDDINGS, ensure_dirs

# HDBSCAN hyperparameters — the two that dominate result quality
MIN_CLUSTER_SIZE = 25   # a cluster must have at least this many messages
MIN_SAMPLES = 5         # controls how conservative the density estimate is


def cluster_embeddings(
    reduced: np.ndarray,
    min_cluster_size: int = MIN_CLUSTER_SIZE,
    min_samples: int = MIN_SAMPLES,
) -> np.ndarray:
    """Run HDBSCAN. Returns array of cluster labels (-1 = noise)."""
    print(f"Running HDBSCAN (min_cluster_size={min_cluster_size}, min_samples={min_samples})...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    return clusterer.fit_predict(reduced)


def summarize(labels: np.ndarray) -> None:
    """Print cluster distribution for a quick sanity check."""
    counts = Counter(labels.tolist())
    n_clusters = len([c for c in counts if c != -1])
    n_noise = counts.get(-1, 0)
    total = len(labels)

    print(f"\nFound {n_clusters} clusters + {n_noise} noise points ({100*n_noise/total:.1f}%).")
    print("\nCluster sizes:")
    for cluster_id, count in sorted(counts.items()):
        label = "noise" if cluster_id == -1 else f"cluster {cluster_id}"
        print(f"  {label:12s}  {count:4d}")


def run_clustering_pipeline() -> None:
    """End-to-end: load reduced embeddings → cluster → save per-message assignments."""
    ensure_dirs()

    if not REDUCED_EMBEDDINGS.exists():
        raise FileNotFoundError(
            f"{REDUCED_EMBEDDINGS} not found. Run scripts/01_embed_and_reduce.py first."
        )

    reduced = np.load(REDUCED_EMBEDDINGS)
    print(f"Loaded reduced embeddings: shape {reduced.shape}\n")

    labels = cluster_embeddings(reduced)
    summarize(labels)

    # Attach cluster_id to each conversation and write out
    texts, intents, resolved = load_conversations()
    assert len(texts) == len(labels), "Mismatch between conversations and labels."

    with CLUSTERS.open("w") as f:
        for text, intent, was_resolved, cluster_id in zip(texts, intents, resolved, labels):
            row = {
                "text": text,
                "true_intent": intent,
                "was_resolved_by_fin": was_resolved,
                "cluster_id": int(cluster_id),
            }
            f.write(json.dumps(row) + "\n")

    print(f"\nSaved per-message cluster assignments to {CLUSTERS.name}")