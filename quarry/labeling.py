"""Stage 1d: Generate human-readable labels for each cluster using Ollama."""

import json
from collections import defaultdict

import numpy as np
import ollama

from quarry.embedding import load_conversations
from quarry.paths import CLUSTERS, EMBEDDINGS

OLLAMA_MODEL = "llama3.1:8b"
TOP_N_MESSAGES = 8  # representative messages per cluster shown to the LLM


LABELING_PROMPT = """You are analyzing customer support conversations from Meridian, a B2B SaaS project management tool.

Below are {n} representative messages from ONE cluster of similar conversations. Your job is to produce a short label and a one-sentence description that captures what these conversations are about.

Messages:
{messages}

Respond in EXACTLY this format, nothing else:
LABEL: <2-5 word label, title case>
DESCRIPTION: <one sentence describing the shared underlying customer need>"""


def load_clusters_with_embeddings() -> tuple[list[dict], np.ndarray]:
    """Load per-message cluster assignments alongside their raw embeddings."""
    rows = []
    with CLUSTERS.open() as f:
        for line in f:
            rows.append(json.loads(line))
    embeddings = np.load(EMBEDDINGS)
    assert len(rows) == len(embeddings), "clusters.jsonl and embeddings.npy misaligned"
    return rows, embeddings


def pick_representative_messages(
    rows: list[dict],
    embeddings: np.ndarray,
    cluster_id: int,
    top_n: int = TOP_N_MESSAGES,
) -> list[str]:
    """Return the top_n messages closest to the cluster centroid."""
    indices = [i for i, r in enumerate(rows) if r["cluster_id"] == cluster_id]
    cluster_embs = embeddings[indices]
    centroid = cluster_embs.mean(axis=0)

    # Distance from each message to centroid; pick closest
    distances = np.linalg.norm(cluster_embs - centroid, axis=1)
    closest_local = np.argsort(distances)[:top_n]
    closest_global = [indices[i] for i in closest_local]
    return [rows[i]["text"] for i in closest_global]


def label_cluster(messages: list[str]) -> dict:
    """Ask Llama for a label + description. Returns {'label': ..., 'description': ...}."""
    formatted = "\n".join(f"- {m}" for m in messages)
    prompt = LABELING_PROMPT.format(n=len(messages), messages=formatted)

    response = ollama.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        options={"temperature": 0.2},  # low temp for consistent formatting
    )
    text = response["response"].strip()

    label = "UNLABELED"
    description = ""
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("LABEL:"):
            label = line.split(":", 1)[1].strip()
        elif line.upper().startswith("DESCRIPTION:"):
            description = line.split(":", 1)[1].strip()

    return {"label": label, "description": description}


def label_all_clusters() -> dict[int, dict]:
    """Label every non-noise cluster. Returns {cluster_id: {label, description, size}}."""
    rows, embeddings = load_clusters_with_embeddings()

    cluster_sizes: dict[int, int] = defaultdict(int)
    for r in rows:
        cluster_sizes[r["cluster_id"]] += 1

    labels: dict[int, dict] = {}
    non_noise = sorted(cid for cid in cluster_sizes if cid != -1)

    for cid in non_noise:
        size = cluster_sizes[cid]
        print(f"→ Labeling cluster {cid} (n={size})...", end=" ", flush=True)
        messages = pick_representative_messages(rows, embeddings, cid)
        result = label_cluster(messages)
        result["size"] = size
        labels[cid] = result
        print(f"'{result['label']}'")

    # Noise bucket gets a fixed label; it isn't a real cluster
    if -1 in cluster_sizes:
        labels[-1] = {
            "label": "Noise / Unclustered",
            "description": "Messages that did not fit any discovered cluster.",
            "size": cluster_sizes[-1],
        }

    return labels