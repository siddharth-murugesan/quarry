"""
Stage 1a + 1b: Embedding and dimensionality reduction.

Reads conversations.jsonl, embeds each message with sentence-transformers,
reduces to 5 dimensions with UMAP, and saves both arrays for downstream
clustering.

Outputs:
  - embeddings.npy         (900, 384) — raw embeddings
  - reduced_embeddings.npy (900, 5)   — UMAP-reduced for clustering
  - sanity_plot.png                    — 2D scatter, colored by true intent
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import umap
from sentence_transformers import SentenceTransformer


# ─── Config ─────────────────────────────────────────────────
INPUT_FILE = "conversations.jsonl"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# UMAP hyperparameters — the two that matter most
UMAP_N_COMPONENTS = 5   # target dimensions for clustering
UMAP_N_NEIGHBORS = 15   # controls local vs global structure preservation
UMAP_MIN_DIST = 0.0     # 0.0 = tightly-packed clusters (good for HDBSCAN)

# For the 2D sanity plot only (separate from clustering pipeline)
UMAP_2D_NEIGHBORS = 15
UMAP_2D_MIN_DIST = 0.1

RANDOM_STATE = 42


def load_conversations(path):
    """Load conversations.jsonl into three parallel lists."""
    texts, intents, resolved = [], [], []
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            texts.append(row["text"])
            intents.append(row["true_intent"])
            resolved.append(row["was_resolved_by_fin"])
    return texts, intents, resolved


def embed(texts):
    """Encode all texts. Returns (N, 384) numpy array."""
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Embedding {len(texts)} messages...")
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return embeddings


def reduce_for_clustering(embeddings):
    """UMAP: 384 → 5 dims for HDBSCAN input."""
    print(f"Reducing {embeddings.shape[1]}D → {UMAP_N_COMPONENTS}D with UMAP...")
    reducer = umap.UMAP(
        n_components=UMAP_N_COMPONENTS,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric="cosine",
        random_state=RANDOM_STATE,
    )
    return reducer.fit_transform(embeddings)


def reduce_for_plot(embeddings):
    """UMAP: 384 → 2 dims, only for the sanity-check scatter plot."""
    print("Reducing 384D → 2D for visualization...")
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=UMAP_2D_NEIGHBORS,
        min_dist=UMAP_2D_MIN_DIST,
        metric="cosine",
        random_state=RANDOM_STATE,
    )
    return reducer.fit_transform(embeddings)


def save_sanity_plot(coords_2d, intents, output="sanity_plot.png"):
    """Scatter plot colored by ground-truth intent."""
    unique_intents = sorted(set(intents))
    intent_to_int = {name: i for i, name in enumerate(unique_intents)}
    colors = [intent_to_int[name] for name in intents]

    plt.figure(figsize=(14, 10))
    scatter = plt.scatter(
        coords_2d[:, 0], coords_2d[:, 1],
        c=colors, cmap="tab20", s=15, alpha=0.7,
    )
    plt.title(
        f"Quarry sanity check: {len(intents)} messages projected to 2D\n"
        f"(color = ground-truth intent — clusters should be visible)",
        fontsize=12,
    )
    plt.xlabel("UMAP dim 1")
    plt.ylabel("UMAP dim 2")

    # Legend: one entry per intent
    handles = [
        plt.scatter([], [], c=scatter.cmap(scatter.norm(intent_to_int[name])),
                    label=name, s=30)
        for name in unique_intents
    ]
    plt.legend(handles=handles, bbox_to_anchor=(1.02, 1), loc="upper left",
               fontsize=8, title="true_intent")
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    print(f"Saved sanity plot to {output}")


def main():
    if not Path(INPUT_FILE).exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run generate_dataset.py first.")

    texts, intents, resolved = load_conversations(INPUT_FILE)
    print(f"Loaded {len(texts)} conversations across {len(set(intents))} intents.\n")

    # Stage 1a: raw embeddings
    embeddings = embed(texts)
    np.save("embeddings.npy", embeddings)
    print(f"Saved embeddings.npy — shape {embeddings.shape}\n")

    # Stage 1b: UMAP reduction for downstream clustering
    reduced = reduce_for_clustering(embeddings)
    np.save("reduced_embeddings.npy", reduced)
    print(f"Saved reduced_embeddings.npy — shape {reduced.shape}\n")

    # Bonus: 2D projection for a human-inspectable sanity plot
    coords_2d = reduce_for_plot(embeddings)
    save_sanity_plot(coords_2d, intents)

    print("\n Completed!")


if __name__ == "__main__":
    main()