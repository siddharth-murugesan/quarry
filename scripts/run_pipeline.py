"""Run the Quarry analysis pipeline end-to-end.

Consumes data/raw/conversations.jsonl (committed to the repo) and produces:
- data/processed/embeddings.npy
- data/processed/reduced_embeddings.npy
- data/processed/clusters.jsonl
- data/processed/cluster_labels.json
- data/processed/analysis.json
- data/output/report.html

By default, each stage skips if its output already exists. Pass --force to
re-run everything from scratch.

Note: dataset generation (Stage 0) is not part of this pipeline. To
regenerate the synthetic dataset, run scripts/00_generate_dataset.py
explicitly — it requires a Gemini API key and rewrites the committed
dataset.

Usage:
  python scripts/run_pipeline.py           # skip stages whose outputs exist
  python scripts/run_pipeline.py --force   # regenerate everything
"""

import argparse
import time
from pathlib import Path

from quarry.paths import (
    ANALYSIS,
    CLUSTERS,
    CLUSTER_LABELS,
    CONVERSATIONS,
    REDUCED_EMBEDDINGS,
    REPORT,
    ensure_dirs,
)


def stage(name: str, output: Path, runner, force: bool) -> None:
    """Run a stage, or skip it if its output already exists."""
    if output.exists() and not force:
        print(f"⏭  {name}: skipping — {output.name} already exists")
        return

    print(f"▶  {name}: running...")
    start = time.time()
    runner()
    elapsed = time.time() - start
    print(f"✓  {name}: done in {elapsed:.1f}s\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Quarry analysis pipeline.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run all stages even if outputs exist.",
    )
    args = parser.parse_args()

    ensure_dirs()

    if not CONVERSATIONS.exists():
        raise FileNotFoundError(
            f"{CONVERSATIONS} not found. This is the required input for the pipeline.\n"
            f"Either check out the committed dataset, or generate one with:\n"
            f"  python scripts/00_generate_dataset.py"
        )

    if args.force:
        print("🔄 --force flag set: all stages will re-run.\n")

    # Stage 1a+b — Embeddings + UMAP
    def run_stage_1ab():
        from quarry.embedding import run_embedding_pipeline
        run_embedding_pipeline()

    stage("Stage 1 · Embedding + reduction", REDUCED_EMBEDDINGS, run_stage_1ab, args.force)

    # Stage 1c — HDBSCAN clustering
    def run_stage_1c():
        from quarry.clustering import run_clustering_pipeline
        run_clustering_pipeline()

    stage("Stage 1 · Clustering", CLUSTERS, run_stage_1c, args.force)

    # Stage 1d — Cluster labeling with Ollama
    def run_stage_1d():
        import json
        from quarry.labeling import label_all_clusters
        labels = label_all_clusters()
        with CLUSTER_LABELS.open("w") as f:
            json.dump(labels, f, indent=2)
        print(f"   Wrote {len(labels)} cluster labels.")

    stage("Stage 1 · Labeling (Ollama)", CLUSTER_LABELS, run_stage_1d, args.force)

    # Stage 2 — Business analysis
    def run_stage_2():
        import json
        from quarry.analysis import run_analysis
        analysis = run_analysis()
        with ANALYSIS.open("w") as f:
            json.dump(analysis, f, indent=2)
        total = analysis["meta"]["total_estimated_annual_savings_usd"]
        print(f"   Total estimated annual savings: ${total:,}")

    stage("Stage 2 · Business analysis", ANALYSIS, run_stage_2, args.force)

    # Stage 3 — HTML report
    def run_stage_3():
        from quarry.reporting import render_report
        render_report()

    stage("Stage 3 · Report rendering", REPORT, run_stage_3, args.force)

    print("─" * 60)
    print(f"✓  Pipeline complete. Open the report:")
    print(f"   open {REPORT}")


if __name__ == "__main__":
    main()