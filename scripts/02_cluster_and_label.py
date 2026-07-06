"""Stage 1c+1d CLI: cluster embeddings and label clusters."""

from quarry.clustering import run_clustering_pipeline


def main() -> None:
    run_clustering_pipeline()
    print("\nClustering complete. Ready for cluster labeling.")


if __name__ == "__main__":
    main()