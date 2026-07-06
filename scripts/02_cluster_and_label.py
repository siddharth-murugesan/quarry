"""Stage 1c+1d CLI: cluster embeddings and label clusters."""

import json

from quarry.clustering import run_clustering_pipeline
from quarry.labeling import label_all_clusters
from quarry.paths import CLUSTER_LABELS


def main() -> None:
    run_clustering_pipeline()
    print("\nLabeling clusters with Ollama (this may take 1-3 minutes)...\n")

    labels = label_all_clusters()

    with CLUSTER_LABELS.open("w") as f:
        json.dump(labels, f, indent=2)

    print(f"\nSaved {len(labels)} cluster labels to {CLUSTER_LABELS.name}")
    print("Ready for analysis (Stage 2).")


if __name__ == "__main__":
    main()