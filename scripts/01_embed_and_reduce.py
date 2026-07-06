"""Stage 1a+1b CLI: embed conversations and reduce dimensions."""

from quarry.embedding import run_embedding_pipeline


def main() -> None:
    run_embedding_pipeline()
    print("\nEmbedding pipeline complete. Ready for clustering.")


if __name__ == "__main__":
    main()